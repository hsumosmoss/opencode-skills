"""水墨歷史短片合成（ink_history_video skill 範本；場景類別以「白沙屯媽祖・粉紅超跑的由來」為範例）
用法：
  python build.py audio     旁白處理、排時間軸、合成配樂與混音
  python build.py stills    每幕輸出檢查用截圖
  python build.py video     渲染畫面並輸出成品 MP4（確定版：兩階段壓縮，控制在 20MB 內）
  python build.py draft     渲染畫面並輸出初版 MP4（單次快速壓縮，供檢查用）
"""
import json, math, os, re, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter, grey_erosion
from scipy.signal import fftconvolve, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
script = json.load(open(os.path.join(HERE, "script.json"), encoding="utf-8"))
OUTDIR = os.path.join(os.path.dirname(HERE), *script.get("output_dir", "影片/prob_tts").split("/"))
OUTFILE = os.path.join(OUTDIR, script.get("output_name", f"{script['title']}・{script['subtitle']}") + ".mp4")
W, H, FPS = 1920, 1080, 24
SR = 44100
FONT = "C:/Windows/Fonts/kaiu.ttf"
f32 = np.float32

PAPER = np.array([236, 227, 206], f32) / 255
INK = np.array([30, 27, 28], f32) / 255
RED = np.array([186, 40, 28], f32) / 255

TITLE_DUR = 6.0
LEAD, GAP, TAIL = 1.1, 0.55, 0.9
END_HOLD = 7.5
TR = 0.9  # 換幕時先收墨到紙色，再落下一幕


# ═════════════════════════ 基本工具 ═════════════════════════
def smooth(x, a, b):
    t = np.clip((np.asarray(x, f32) - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noise2d(h, w, cy, cx, seed):
    rng = np.random.default_rng(seed)
    gh, gw = h // cy + 4, w // cx + 4
    g = rng.random((gh, gw), dtype=f32)
    im = Image.fromarray(g).resize((gw * cx, gh * cy), Image.BICUBIC)
    return np.asarray(im, f32)[cy:cy + h, cx:cx + w]


def fbm2d(h, w, cell, octaves, seed):
    s = np.zeros((h, w), f32); amp = 1.0; tot = 0
    for i in range(octaves):
        c = max(2, cell >> i)
        s += amp * noise2d(h, w, c, c, seed + 17 * i); tot += amp; amp *= 0.5
    s -= s.min(); s /= max(1e-6, s.max())
    return s


def fbm1d(n, cell, octaves, seed):
    s = np.zeros(n, f32); amp = 1.0
    for i in range(octaves):
        c = max(2, cell >> i)
        s += amp * noise2d(1, n, 1, c, seed + 31 * i)[0]; amp *= 0.5
    s -= s.min(); s /= max(1e-6, s.max())
    return s


class Pen:
    """2 倍超取樣的灰階畫筆，座標用輸出像素。"""
    def __init__(self, w, h, S=2):
        self.w, self.h, self.S = int(w), int(h), S
        self.im = Image.new("L", (self.w * S, self.h * S), 0)
        self.d = ImageDraw.Draw(self.im)

    def _p(self, pts):
        return [(x * self.S, y * self.S) for x, y in pts]

    def poly(self, pts, v):
        self.d.polygon(self._p(pts), fill=int(v))

    def line(self, pts, v, width):
        self.d.line(self._p(pts), fill=int(v), width=max(1, int(round(width * self.S))), joint="curve")

    def ell(self, cx, cy, rx, ry, v):
        S = self.S
        self.d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=int(v))

    def rect(self, x0, y0, x1, y1, v):
        S = self.S
        self.d.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], fill=int(v))

    def arr(self, blur=0.7):
        a = np.asarray(self.im.resize((self.w, self.h), Image.LANCZOS), f32) / 255
        return gaussian_filter(a, blur) if blur else a


def inkify(a, seed, grain=0.18, pool=0.35):
    h, w = a.shape
    n = noise2d(h, w, 3, 3, seed)
    a = a * (1 - grain + 2 * grain * n)
    if pool:
        a = a + pool * np.clip(a - gaussian_filter(a, 2.5), 0, None)  # 墨在邊緣積聚
    return np.clip(a, 0, 1).astype(f32)


def put(L, a, x, y, k=1.0):
    """把 alpha 以「疊墨」方式放到 L 上（左上角 x,y）。回傳實際區域供遮擋用。"""
    h, w = a.shape
    x0, y0 = int(round(x)), int(round(y))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb or k <= 0:
        return None
    sub = a[ya - y0:yb - y0, xa - x0:xb - x0] * k
    reg = L[ya:yb, xa:xb]
    reg += sub * (1 - reg)
    return (ya, yb, xa, xb, sub)


def put_ink(A, R, a, x, y, k=1.0):
    r = put(A, a, x, y, k)
    if r:  # 墨蓋住朱紅
        ya, yb, xa, xb, sub = r
        R[ya:yb, xa:xb] *= 1 - sub


def radial_field(h, w, cx, cy, seed, nz=0.3):
    yy, xx = np.mgrid[0:h, 0:w].astype(f32)
    d = np.hypot((xx - cx) / max(w, 1), (yy - cy) / max(h, 1))
    d /= max(1e-6, d.max())
    n = fbm2d(h, w, max(4, min(h, w) // 4), 3, seed)
    F = (1 - nz) * d + nz * n
    F -= F.min(); F /= max(1e-6, F.max())
    return F.astype(f32)


def reveal(F, p, soft=0.1):
    return np.clip((p * (1 + soft) - F) / soft, 0, 1)


def ease(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def catmull_keys(keys):
    """keys: [(u, x, y)...] → 函式 f(u) 回傳 (x, y)。"""
    us = np.array([k[0] for k in keys], float)
    P = np.array([k[1:] for k in keys], float)
    P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])

    def f(u):
        u = min(us[-1], max(us[0], u))
        i = min(len(us) - 2, int(np.searchsorted(us, u, side="right") - 1))
        s = (u - us[i]) / (us[i + 1] - us[i])
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        return 0.5 * (2 * p1 + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s
                      + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3)
    return f


# ═════════════════════════ 文字與印章 ═════════════════════════
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


def text_h(text, size, bold=0):
    f = font(size)
    l, t, r, b = f.getbbox(text)
    pad = int(size * 0.3) + bold
    im = Image.new("L", (r - l + 2 * pad, int(size * 1.25) + 2 * pad), 0)
    ImageDraw.Draw(im).text((pad - l, pad), text, font=f, fill=255, stroke_width=bold, stroke_fill=255)
    return np.asarray(im, f32) / 255


def text_v(text, size, spacing=1.08, bold=0):
    f = font(size)
    pad = int(size * 0.3) + bold
    step = int(size * spacing)
    im = Image.new("L", (size + 2 * pad, step * len(text) + 2 * pad), 0)
    d = ImageDraw.Draw(im)
    for i, ch in enumerate(text):
        if ch == "　":
            continue
        # 標楷體為等寬全形字，固定起點才會上下對齊成一直線
        d.text((pad, pad + i * step), ch, font=f, fill=255,
               stroke_width=bold, stroke_fill=255)
    return np.asarray(im, f32) / 255


class InkText:
    """墨水暈開式出場的文字。"""
    def __init__(self, a, seed, dark=0.92):
        self.T = inkify(a, seed, grain=0.12, pool=0.25) * dark
        s = max(4, a.shape[0] // 14, a.shape[1] // 60)
        self.B = gaussian_filter(a, min(s, 14)) * 1.3
        self.halo = gaussian_filter(a, 2.2) * 0.14
        self.clear = np.clip(gaussian_filter(a, 14) * 4, 0, 1).astype(f32)  # 暗底時襯出宣紙色
        self.shape = a.shape

    def alpha(self, p):
        if p <= 0:
            return None
        if p >= 1:
            return np.clip(self.T + self.halo, 0, 1)
        sharp = smooth(p, 0.08, 0.55)
        bleed = smooth(p, 0.0, 0.25) * (1 - smooth(p, 0.20, 0.55))
        return np.clip(self.T * sharp + self.halo * sharp + np.clip(self.B, 0, 0.68) * bleed, 0, 1)


def make_seal(text, size, seed):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype(f32)
    m = size * 0.04
    n = noise2d(size, size, 4, 4, seed)
    edge = np.minimum.reduce([xx - m, yy - m, size - m - xx, size - m - yy]) + (n - 0.5) * size * 0.05
    sq = smooth(edge, 0, 1.5)
    im = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(im)
    inner = size * 0.1
    if len(text) == 4:  # 右欄上下、左欄上下
        fs = int(size * 0.4)
        cells = [(1, 0), (1, 1), (0, 0), (0, 1)]
    else:
        fs = int(size * 0.4)
        cells = [(0.5, 0), (0.5, 1)]
    f = font(fs)
    span = size - 2 * inner
    for ch, (cx, cy) in zip(text, cells):
        l, t, r, b = f.getbbox(ch)
        x = inner + cx * span / 2 + (span / 2 - (r - l)) / 2 - l
        y = inner + cy * span / 2 + (span / 2 - (b - t)) / 2 - t
        d.text((x, y), ch, font=f, fill=255)
    txt = gaussian_filter(np.asarray(im, f32) / 255, 0.6)
    a = sq * (1 - txt)
    speck = noise2d(size, size, 2, 2, seed + 1)
    a *= 0.82 + 0.18 * n
    a *= np.where(speck > 0.86, 0.35, 1.0)
    return np.clip(a, 0, 1).astype(f32) * 0.92


# ═════════════════════════ 圖形素材 ═════════════════════════
def mountain(ridge, dark, fall=160, shun=0.55, seed=0, mist=None, blur=1.2):
    wext = len(ridge)
    y = np.arange(H, dtype=f32)[:, None]
    d = y - ridge[None, :].astype(f32)
    dp = np.maximum(d, 0)
    body = smooth(d, 0, 2.5)
    a = dark * (0.22 + 0.78 * np.exp(-dp / fall))
    st = noise2d(H, wext, 26, 5, seed)
    st2 = noise2d(H, wext, 8, 3, seed + 1)
    tex = (1 - shun) + shun * (0.35 + 1.3 * smooth(st, 0.3, 0.8) * (0.6 + 0.8 * st2))
    a = a * tex + dark * 0.4 * np.exp(-dp / 4)
    a *= body
    if mist:
        a *= 1 - smooth(y, mist[0], mist[1])
    return np.clip(gaussian_filter(a, blur), 0, 1).astype(f32)


def ridge(wext, base, amp, cell, seed, peaks=()):
    r = base - amp * fbm1d(wext, cell, 5, seed) ** 1.3
    x = np.arange(wext, dtype=f32)
    for xc, hh, wd in peaks:
        r -= hh * np.exp(-((x - xc) / wd) ** 2)
    return r


def waves(wext, y0, y1, rows, amp, dark, seed, storm=False):
    rng = np.random.default_rng(seed)
    pen = Pen(wext, H)
    for j in range(rows):
        u = j / max(1, rows - 1)
        y = y0 + (y1 - y0) * u ** 1.5
        sc = 0.3 + 0.7 * u
        x = -rng.random() * 200
        while x < wext:
            L = (70 + rng.random() * 130) * sc * (2.0 if storm else 1.0)
            A = amp * sc * (0.6 + 0.8 * rng.random())
            yj = y + rng.normal() * 4 * sc
            pts = [(x + L * k / 14, yj - A * math.sin(math.pi * k / 14) ** 2) for k in range(15)]
            if storm:
                hook = [(x + L * (0.5 + 0.18 * math.cos(a)), yj - A + A * 0.35 * (1 - math.sin(a)))
                        for a in np.linspace(0.5, 3.6, 8)]
                pen.poly(pts + [(x + L * 0.85, yj + A * 0.5), (x + L * 0.15, yj + A * 0.5)], 255 * dark * 0.12)
                pen.line(hook, 255 * dark * 0.8, 2.2 * sc)
            pen.line(pts, 255 * dark * (0.45 + 0.55 * u), (1.2 + 2.2 * sc) * (1.5 if storm else 1))
            x += L * (1.0 + rng.random() * 0.9)
    a = pen.arr(0.8)
    yy = np.arange(H, dtype=f32)[:, None]
    base = smooth(yy, y0 - 10, y1) * dark * (0.35 if storm else 0.16)
    base = base * (0.7 + 0.6 * noise2d(H, wext, 40, 120, seed + 5))
    return np.clip(1 - (1 - a) * (1 - base), 0, 1).astype(f32)


def houses(wext, xs, base_y, seed, dark=0.75):
    rng = np.random.default_rng(seed)
    pen = Pen(wext, H)
    for x in xs:
        s = 34 + rng.random() * 36
        y = base_y + rng.normal() * 6
        w = s * (1.3 + rng.random() * 0.7)
        pen.rect(x, y - s * 0.55, x + w, y, 255 * dark * 0.35)
        pen.rect(x + w * 0.42, y - s * 0.32, x + w * 0.58, y, 255 * dark * 0.8)
        ov = s * 0.25
        pen.poly([(x - ov, y - s * 0.5), (x - ov * 1.4, y - s * 0.68), (x + w * 0.2, y - s * 0.95),
                  (x + w * 0.8, y - s * 0.95), (x + w + ov * 1.4, y - s * 0.68), (x + w + ov, y - s * 0.5)],
                 255 * dark)
    return inkify(pen.arr(0.9), seed, 0.2)


def trees(wext, xs, base_y, seed, dark=0.75):
    """木麻黃：細長樹幹＋下垂細葉。"""
    rng = np.random.default_rng(seed)
    pen = Pen(wext, H)
    for x in xs:
        hgt = 170 + rng.random() * 120
        y = base_y + rng.normal() * 10
        lean = rng.normal() * 10
        top = (x + lean, y - hgt)
        pen.line([(x, y), (x + lean * 0.5, y - hgt * 0.5), top], 255 * dark, 4)
        for k in range(70):
            u = rng.random() ** 0.8
            cx = x + lean * (1 - u * 0.5) + rng.normal() * hgt * 0.12 * (0.4 + u)
            cy = y - hgt * (0.35 + 0.65 * (1 - u * 0.75))
            L = 12 + rng.random() * 26
            pen.line([(cx, cy), (cx + rng.normal() * 3, cy + L)], 255 * dark * (0.4 + 0.5 * rng.random()), 1.3)
    return inkify(pen.arr(0.6), seed, 0.25)


def temple(w, dark=0.85):
    h = int(w * 0.62)
    pen, red = Pen(w, h), Pen(w, h)
    ye, yt = 0.42 * h, 0.17 * h
    eave = [(0.02 * w + 0.96 * w * u, ye - smooth(abs(u - 0.5), 0.3, 0.5) ** 1.5 * 0.14 * h)
            for u in np.linspace(0, 1, 40)]
    top = [(0.14 * w + 0.72 * w * u, yt - smooth(abs(u - 0.5), 0.36, 0.5) ** 1.5 * 0.16 * h)
           for u in np.linspace(0, 1, 40)]
    pen.rect(0.08 * w, 0.88 * h, 0.92 * w, 0.95 * h, 255 * dark * 0.55)
    pen.rect(0.16 * w, ye, 0.84 * w, 0.88 * h, 255 * dark * 0.22)
    for cx in (0.2, 0.38, 0.62, 0.8):
        pen.line([(cx * w, ye), (cx * w, 0.88 * h)], 255 * dark * 0.9, 0.013 * w)
    pen.rect(0.44 * w, 0.56 * h, 0.56 * w, 0.88 * h, 255 * dark * 0.8)
    pen.poly(eave + top[::-1], 255 * dark * 0.7)
    for u in np.linspace(0.1, 0.9, 16):
        x = 0.14 * w + 0.72 * w * u
        pen.line([(x, yt + 0.02 * h), (0.02 * w + 0.96 * w * u, ye - 0.01 * h)], 255 * dark * 0.92, 0.004 * w)
    pen.line(top, 255 * dark, 0.02 * w)
    pen.line(eave, 255 * dark, 0.008 * w)
    pen.ell(0.5 * w, yt - 0.06 * h, 0.03 * w, 0.03 * w, 255 * dark)
    for cx in (0.3, 0.7):  # 紅燈籠
        red.ell(cx * w, 0.5 * h, 0.022 * w, 0.03 * w, 255 * 0.9)
    return inkify(pen.arr(0.8), 7, 0.15), red.arr(0.8)


def person(hgt, seed, hat=None):
    rng = np.random.default_rng(seed)
    hat = rng.random() < 0.4 if hat is None else hat
    w = int(hgt * 0.75) + 6
    pen = Pen(w, hgt + 4)
    cx = w / 2
    r = hgt * 0.1
    pen.poly([(cx - hgt * 0.13, hgt * 0.24), (cx + hgt * 0.13, hgt * 0.24),
              (cx + hgt * 0.19, hgt * 0.78), (cx - hgt * 0.19, hgt * 0.78)], 190)
    for s in (-1, 1):
        pen.line([(cx + s * hgt * 0.07, hgt * 0.76), (cx + s * hgt * 0.1, hgt)], 220, hgt * 0.06)
    pen.ell(cx, r + 2, r, r * 1.05, 235)
    if hat:
        pen.poly([(cx - hgt * 0.24, r * 1.6), (cx, -r * 0.2), (cx + hgt * 0.24, r * 1.6)], 210)
    return pen.arr(0.5 if hgt > 20 else 0.35)


def palanquin(w):
    h = int(w * 1.1)
    pen, red = Pen(w, h), Pen(w, h)
    pen.poly([(0.12 * w, 0.24 * h), (0.06 * w, 0.17 * h), (0.3 * w, 0.08 * h), (0.7 * w, 0.08 * h),
              (0.94 * w, 0.17 * h), (0.88 * w, 0.24 * h)], 225)
    pen.ell(0.5 * w, 0.05 * h, 0.04 * w, 0.04 * w, 235)
    red.rect(0.22 * w, 0.24 * h, 0.78 * w, 0.6 * h, 255 * 0.55)
    red.poly([(0.22 * w, 0.6 * h), (0.78 * w, 0.6 * h), (0.74 * w, 0.66 * h), (0.26 * w, 0.66 * h)], 255 * 0.4)
    pen.line([(0.22 * w, 0.24 * h), (0.22 * w, 0.62 * h)], 150, 0.015 * w)
    pen.line([(0.78 * w, 0.24 * h), (0.78 * w, 0.62 * h)], 150, 0.015 * w)
    pen.line([(0.0, 0.56 * h), (w, 0.56 * h)], 230, 0.03 * w)
    ph = 0.44 * h
    for bx in (0.07, 0.3, 0.7, 0.93):
        p = person(int(ph), int(bx * 100), hat=True)
        pw = p.shape[1]
        x0, y0 = int(bx * w - pw / 2), int(h - ph - 4)
        sub = Image.fromarray((p * 255).astype(np.uint8))
        pen.im.paste(255, (x0 * 2, y0 * 2), sub.resize((pw * 2, p.shape[0] * 2)))
    return pen.arr(0.6), red.arr(0.7)


_glows = {}


def incense(R, x, top, size, h, t, seed=0):
    """神轎前端閃爍的紅點，象徵香火。"""
    r = max(5, int(size * 0.13))
    if r not in _glows:
        _glows[r] = (glow(r * 3), glow(r))
    g, c = _glows[r]
    fl = 0.65 + 0.2 * math.sin(t * 9.0 + seed) + 0.15 * math.sin(t * 23.0 + seed * 2)
    cx, cy = x, top + h * 0.38  # 神轎中間
    put(R, g, cx - g.shape[1] / 2, cy - g.shape[0] / 2, 0.45 * fl)
    put(R, c, cx - c.shape[1] / 2, cy - c.shape[0] / 2, 0.95 * fl)


def boat(w):
    h = int(w * 0.95)
    pen = Pen(w, h)
    pen.poly([(0.52 * w, 0.08 * h), (0.82 * w, 0.14 * h), (0.88 * w, 0.56 * h), (0.52 * w, 0.56 * h)], 85)
    pen.poly([(0.18 * w, 0.24 * h), (0.44 * w, 0.28 * h), (0.47 * w, 0.56 * h), (0.16 * w, 0.56 * h)], 70)
    for u in np.linspace(0.15, 0.5, 6):
        y = u * h
        pen.line([(0.52 * w, y), (0.82 * w + (y - 0.14 * h) / (0.42 * h) * 0.06 * w, y + 0.02 * h)], 215, 0.006 * w)
    pen.line([(0.52 * w, 0.62 * h), (0.52 * w, 0.04 * h)], 235, 0.013 * w)
    pen.line([(0.46 * w, 0.62 * h), (0.46 * w, 0.22 * h)], 235, 0.01 * w)
    pen.poly([(0.0, 0.56 * h), (0.12 * w, 0.62 * h), (0.9 * w, 0.62 * h), (w, 0.54 * h),
              (0.86 * w, 0.8 * h), (0.16 * w, 0.8 * h)], 235)
    return inkify(pen.arr(0.8), 11, 0.08, 0.25)


def woman(hgt):
    w = int(hgt * 0.75)
    pen = Pen(w, hgt)
    cx = 0.4 * w
    pen.poly([(cx - 0.12 * hgt, 0.15 * hgt), (cx - 0.2 * hgt, 0.55 * hgt), (cx - 0.15 * hgt, 0.62 * hgt),
              (cx - 0.06 * hgt, 0.2 * hgt)], 150)
    pen.poly([(cx - 0.07 * hgt, 0.13 * hgt), (cx + 0.07 * hgt, 0.13 * hgt), (cx + 0.13 * hgt, 0.6 * hgt),
              (cx + 0.22 * hgt, 0.97 * hgt), (cx - 0.18 * hgt, 0.99 * hgt), (cx - 0.11 * hgt, 0.6 * hgt)], 115)
    pen.line([(cx - 0.07 * hgt, 0.13 * hgt), (cx - 0.11 * hgt, 0.6 * hgt), (cx - 0.18 * hgt, 0.99 * hgt)], 225, 0.009 * hgt)
    pen.line([(cx + 0.07 * hgt, 0.13 * hgt), (cx + 0.13 * hgt, 0.6 * hgt), (cx + 0.22 * hgt, 0.97 * hgt)], 225, 0.009 * hgt)
    hand = (cx + 0.24 * hgt, 0.06 * hgt)
    pen.line([(cx + 0.06 * hgt, 0.16 * hgt), (cx + 0.16 * hgt, 0.12 * hgt), hand], 170, 0.03 * hgt)
    pen.ell(cx, 0.075 * hgt, 0.045 * hgt, 0.05 * hgt, 235)
    pen.ell(cx - 0.025 * hgt, 0.03 * hgt, 0.03 * hgt, 0.028 * hgt, 240)
    return inkify(pen.arr(0.8), 3, 0.15), hand


def burner(w):
    h = int(w * 0.85)
    pen = Pen(w, h)
    for s in (-1, 1):
        pen.rect(0.5 * w + s * 0.36 * w - 0.04 * w, 0.02 * h, 0.5 * w + s * 0.36 * w + 0.04 * w, 0.22 * h, 220)
        pen.line([(0.5 * w + s * 0.25 * w, 0.6 * h), (0.5 * w + s * 0.32 * w, 0.98 * h)], 230, 0.05 * w)
    pen.line([(0.5 * w, 0.6 * h), (0.5 * w, 0.98 * h)], 200, 0.05 * w)
    pts = [(0.5 * w + 0.42 * w * math.cos(a), 0.2 * h + 0.55 * h * math.sin(a)) for a in np.linspace(0, math.pi, 30)]
    pen.poly(pts, 215)
    pen.ell(0.5 * w, 0.2 * h, 0.44 * w, 0.06 * h, 120)
    pen.line([(0.1 * w, 0.36 * h), (0.9 * w, 0.36 * h)], 120, 0.01 * w)
    return inkify(pen.arr(0.8), 21, 0.07, 0.25)


def blob(r, seed):
    s = int(r * 2.6)
    yy, xx = np.mgrid[0:s, 0:s].astype(f32)
    d = np.hypot(xx - s / 2, yy - s / 2) / r
    n = fbm2d(s, s, max(4, s // 5), 4, seed)
    a = smooth(1.1 - d - 0.5 * (n - 0.5), 0, 0.35)
    a = gaussian_filter(a, 3) * (0.6 + 0.4 * (1 - d.clip(0, 1)) ** 0.5) * (0.85 + 0.15 * n)
    a += 0.5 * np.clip(a - gaussian_filter(a, 6), 0, None)
    return np.clip(a, 0, 1).astype(f32), radial_field(s, s, s / 2, s / 2, seed, 0.45)


def glow(r):
    s = int(r * 2)
    yy, xx = np.mgrid[0:s, 0:s].astype(f32)
    d = np.hypot(xx - s / 2, yy - s / 2) / r
    return np.exp(-(d * 2.2) ** 2).astype(f32)


def disc(r, soft=2.0):
    s = int(r * 2 + 8)
    yy, xx = np.mgrid[0:s, 0:s].astype(f32)
    d = np.hypot(xx - s / 2, yy - s / 2)
    a = smooth(r - d, -soft, soft) * (0.85 + 0.15 * noise2d(s, s, 5, 5, 4))
    return a.astype(f32)


def blossom(r):
    s = int(r * 3) + 4
    pen = Pen(s, s)
    c = s / 2
    for k in range(5):
        a = k * 2 * math.pi / 5 - math.pi / 2
        pen.ell(c + r * 0.55 * math.cos(a), c + r * 0.55 * math.sin(a), r * 0.5, r * 0.5, 230)
    red = pen.arr(0.6)
    ink = Pen(s, s)
    for k in range(6):
        a = k * 2 * math.pi / 6
        ink.ell(c + r * 0.3 * math.cos(a), c + r * 0.3 * math.sin(a), r * 0.08, r * 0.08, 220)
    return red, ink.arr(0.4)


def load_img(name, height):
    """把生成的水墨圖拆成：遮蓋(clear)、墨(ink)、朱紅(red)。"""
    im = Image.open(os.path.join(HERE, "assets", name)).convert("RGBA")
    w = int(im.width * height / im.height)
    a = np.asarray(im.resize((w, height), Image.LANCZOS), f32) / 255
    rgb, al = a[..., :3], a[..., 3]
    clear = smooth(al, 0.55, 0.97)
    lum = rgb @ np.array([0.3, 0.59, 0.11], f32)
    red = clear * np.clip((rgb[..., 0] - (rgb[..., 1] + rgb[..., 2]) / 2 - 0.12) / 0.3, 0, 1)
    ink = clear * np.clip(1 - lum / 0.93, 0, 1) ** 0.95 * (1 - red)
    return clear.astype(f32), ink.astype(f32), red.astype(f32)


def put_img(A, R, img, x, y, k=1.0):
    clear, ink, red = img
    if np.isscalar(k) and k <= 0:
        return
    h, w = ink.shape
    x0, y0 = int(round(x)), int(round(y))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    sl = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0))
    kk = k if np.isscalar(k) else k[sl]
    c, i, r = clear[sl] * kk, ink[sl] * kk, red[sl] * kk
    rA, rR = A[ya:yb, xa:xb], R[ya:yb, xa:xb]
    rA *= 1 - c
    rA += i
    rR *= 1 - c
    rR += r


# ═════════════════════════ 場景 ═════════════════════════
class Scene:
    fog = ()        # (中心y, 半寬, 濃度)
    fog_speed = 16

    def __init__(self, dur, seed, info=None):
        self.dur, self.seed, self.info = dur, seed, info or {}
        self.layers = []
        self.build()
        if self.fog:
            fw = int(W + self.fog_speed * (dur + 6)) + 8
            n = fbm2d(H, fw, 300, 4, seed + 99)
            yy = np.arange(H, dtype=f32)[:, None]
            band = np.zeros((H, 1), f32)
            for cy, hw, amt in self.fog:
                band = np.maximum(band, amt * np.exp(-((yy - cy) / hw) ** 2))
            self.fogtex = (smooth(n, 0.25, 0.8) * band).astype(f32)

    def wext(self, speed):
        return int(W + abs(speed) * (self.dur + 6)) + 8

    def mid(self, speed):
        return abs(speed) * (self.dur / 2 + 3)

    def plane(self, a, speed, k=1.0):
        self.layers.append(("plane", a, speed, k))

    def fx(self, fn):
        self.layers.append(("fx", fn))

    def fogpass(self):
        self.layers.append(("fog",))

    def slice(self, a, speed, t):
        if speed == 0:
            return a[:, :W]
        off = (t + 3) * abs(speed)
        if speed < 0:
            off = a.shape[1] - W - 2 - off
        off = min(max(off, 0), a.shape[1] - W - 2)
        i = int(off); fr = off - i
        return a[:, i:i + W] * (1 - fr) + a[:, i + 1:i + 1 + W] * fr

    def render(self, t):
        A = np.zeros((H, W), f32); R = np.zeros((H, W), f32)
        fog_done = False
        for L in self.layers:
            if L[0] == "plane":
                s = self.slice(L[1], L[2], t) * L[3]
                A += s * (1 - A); R *= 1 - s
            elif L[0] == "fx":
                L[1](t, A, R)
            elif L[0] == "fog":
                self.apply_fog(t, A, R); fog_done = True
        if self.fog and not fog_done:
            self.apply_fog(t, A, R)
        return A, R

    def apply_fog(self, t, A, R):
        if not self.fog:
            return
        f = self.slice(self.fogtex, self.fog_speed, t)
        A *= 1 - f; R *= 1 - f


class Title(Scene):
    fog = ((640, 170, 0.75),)

    def build(self):
        sp = 6
        we = self.wext(sp)
        self.plane(mountain(ridge(we, 640, 200, 420, 1, [(self.mid(sp) + 1500, 160, 160)]), 0.22,
                            mist=(560, 760), seed=1), sp)
        self.fogpass()
        self.drops = []
        for i, (x, y, r, d, t0) in enumerate([(200, 190, 130, 0.3, 0.1), (330, 930, 90, 0.3, 0.35),
                                               (1080, 130, 55, 0.38, 0.6)]):
            a, F = blob(r, 50 + i)
            self.drops.append((a * d, F, x - a.shape[1] / 2, y - a.shape[0] / 2, t0))
        self.t1 = InkText(text_h(script["title"], 170, bold=2), 5, 0.88)
        self.t2 = InkText(text_h(script["subtitle"], 80, bold=1), 6, 0.86)
        self.seal = make_seal("天上聖母", 128, 9)
        self.mazu = load_img("mazu_main.png", 1000)
        self.mF = radial_field(*self.mazu[1].shape, self.mazu[1].shape[1] / 2, self.mazu[1].shape[0] * 0.9, 61, 0.4)
        self.fx(self.draw)

    def draw(self, t, A, R):
        p = ease((t - 0.9) / 2.6)
        if p > 0:
            put_img(A, R, self.mazu, 1250, 50, reveal(self.mF, p, 0.15))
        for a, F, x, y, t0 in self.drops:
            p = ease((t - t0) / 1.6)
            if p > 0:
                put_ink(A, R, a * reveal(F, p, 0.15), x, y)
        h1, w1 = self.t1.shape
        x1, y1 = 600 - w1 / 2, 300
        a = self.t1.alpha((t - 0.4) / 1.2)
        if a is not None:
            put_ink(A, R, a, x1, y1)
        h2, w2 = self.t2.shape
        a = self.t2.alpha((t - 1.4) / 1.2)
        if a is not None:
            put_ink(A, R, a, 600 - w2 / 2, y1 + h1 + 10)
        k = smooth(t, 3.0, 3.15)
        if k > 0:
            put(R, self.seal, x1 + w1 + 10, y1 + 70, float(k))


class S1(Scene):  # 海濱小村
    fog = ((610, 80, 0.75), (430, 110, 0.45))

    def build(self):
        a, b, c = 5, 9, 14
        self.plane(mountain(ridge(self.wext(a), 520, 170, 380, 11, [(self.mid(a) + 400, 120, 150),
                                                                     (self.mid(a) + 1250, 90, 200)]),
                            0.22, mist=(470, 640), seed=11), a)
        wb = self.wext(b)
        self.plane(mountain(ridge(wb, 700, 110, 300, 12), 0.45, mist=(660, 780), seed=12), b)
        self.fogpass()
        self.plane(houses(wb, np.arange(200, wb - 100, 150) + np.random.default_rng(3).normal(0, 40, len(range(200, wb - 100, 150))),
                          775, 13), b)
        self.plane(waves(self.wext(c), 790, 1080, 14, 6, 0.5, 14), c)
        self.fx(self.draw_birds)

    def draw_birds(self, t, A, R):
        pen = Pen(W, 400, S=1)
        for i in range(4):
            x = 1500 - t * (22 + 4 * i) - i * 70
            y = 180 + i * 28 + 6 * math.sin(t * 1.3 + i)
            wv = 6 * math.sin(t * 7 + i * 1.7)
            pen.line([(x - 12, y - wv), (x, y), (x + 12, y - wv)], 170, 2)
        put_ink(A, R, gaussian_filter(np.asarray(pen.im, f32) / 255, 0.7), 0, 0)


class S2(Scene):  # 湄洲神女
    fog = ((630, 50, 0.6),)

    def build(self):
        self.plane(mountain(ridge(self.wext(4), 610, 60, 200, 21, [(self.mid(4) + 1400, 50, 260)]),
                            0.16, mist=(580, 650), seed=21), 4)
        self.plane(waves(self.wext(16), 640, 1080, 18, 9, 0.55, 22), 16)
        self.fogpass()
        x = np.arange(W + 8, dtype=f32)
        r = 470 + 50 * fbm1d(W + 8, 200, 4, 23) + 0.08 * x
        r = r + np.maximum(x - 690, 0) ** 1.6
        self.cliff = mountain(r.astype(f32), 0.5, fall=200, shun=0.45, seed=24)
        yy = np.arange(H, dtype=f32)[:, None]
        occ = smooth(yy - r[None, :W].astype(f32), 0, 3)
        self.fx(lambda t, A, R: (A.__imul__(1 - occ), R.__imul__(1 - occ)))
        self.plane(self.cliff, 0)
        self.wom, self.hand = woman(240)
        self.wx = 430
        self.wy = r[self.wx + 60] - 240 + 6
        self.boat = np.ascontiguousarray(boat(110)[:, ::-1])
        self.g1, self.g2 = glow(60), glow(14)
        self.fx(self.draw)

    def draw(self, t, A, R):
        bw = self.boat
        put_ink(A, R, bw, 1260 + t * 4 - bw.shape[1] / 2, 680 + 4 * math.sin(t * 1.4) - bw.shape[0] * 0.8, 0.8)
        put_ink(A, R, self.wom, self.wx, self.wy)
        # 衣帶飄動
        pen = Pen(260, 240, S=1)
        pts = [(10 + 20 * k, 90 + 14 * math.sin(t * 2.2 - k * 0.8) + k * 3) for k in range(12)]
        pen.line(pts, 160, 3)
        put_ink(A, R, gaussian_filter(np.asarray(pen.im, f32) / 255, 1.0), self.wx + 105, self.wy)
        hx, hy = self.wx + self.hand[0], self.wy + self.hand[1] + 26
        fl = 0.85 + 0.15 * math.sin(t * 9) * math.sin(t * 3.7)
        put(R, self.g1, hx - 60, hy - 60, 0.35 * fl)
        put(R, self.g2, hx - 14, hy - 14, 0.95)


class S3(Scene):  # 黑水溝
    def build(self):
        sp = 8
        we = self.wext(sp)
        yy = np.arange(H, dtype=f32)[:, None]
        cloud = fbm2d(H, we, 260, 5, 31)
        sky = (0.5 * (1 - smooth(yy, 80, 560)) * (0.55 + 0.6 * cloud)).astype(f32)
        self.plane(np.clip(sky, 0, 1), sp)
        self.plane(waves(self.wext(22), 520, 780, 10, 14, 0.55, 32, storm=True), 22)
        bi = boat(320)
        st = load_img("mazu_statue.png", 74)
        clear, ink, red = bi.copy(), bi.copy(), np.zeros_like(bi)
        sh, sw = st[1].shape
        x0, y0 = int(0.24 * 320 - sw / 2), int(0.6 * bi.shape[0] - sh)
        sl = (slice(y0, y0 + sh), slice(max(0, x0), x0 + sw))
        ss = (slice(0, sh), slice(max(0, -x0), sw))
        clear[sl] = 1 - (1 - clear[sl]) * (1 - st[0][ss])
        ink[sl] = ink[sl] * (1 - st[0][ss]) + st[1][ss]
        red[sl] = st[2][ss]
        # 神像中心（翻轉後、相對船圖中心）
        self.st_c = (bi.shape[1] - (x0 + sw / 2) - bi.shape[1] / 2, y0 + sh / 2 - bi.shape[0] / 2)
        self.boat = [np.ascontiguousarray((c[:, ::-1] * 255).astype(np.uint8)) for c in (clear, ink, red)]  # 船頭朝右（行進方向）
        self.g = glow(40)
        self.gc = glow(6)
        self.fx(self.draw)
        self.plane(waves(self.wext(36), 760, 1100, 8, 40, 0.75, 33, storm=True), 36)

    def draw(self, t, A, R):
        ang = 5 * math.sin(t * 0.9 + 0.5)
        rot = [np.asarray(Image.fromarray(c).rotate(ang, Image.BICUBIC, expand=True), f32) / 255 for c in self.boat]
        b = rot[1]
        x = 960 - b.shape[1] / 2 + 20 * math.sin(t * 0.3)
        y = 720 - b.shape[0] * 0.75 + 16 * math.sin(t * 1.1)
        put_img(A, R, rot, x, y)
        # 香火紅點：疊在神像中間
        dx, dy = self.st_c
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        bx = x + b.shape[1] / 2 + dx * ca + dy * sa
        by = y + b.shape[0] / 2 - dx * sa + dy * ca
        fl = 0.8 + 0.2 * math.sin(t * 8)
        put(R, self.g, bx - 40, by - 40, 0.5 * fl)
        put(R, self.gc, bx - 6, by - 6, 0.9 * fl)


class S4(Scene):  # 拱天宮
    fog = ((715, 60, 0.5),)

    def build(self):
        self.plane(waves(self.wext(8), 560, 690, 6, 3, 0.3, 41), 8)
        self.plane(mountain(ridge(self.wext(6), 720, 50, 500, 42), 0.3, fall=120, shun=0.15, seed=42, mist=(760, 900)), 6)
        we = self.wext(7)
        m = self.mid(7)
        xs = [m + v for v in (-80, 60, 210, 330, 1560, 1690, 1830, 1990)]
        self.plane(trees(we, xs, 760, 43), 7)
        self.fogpass()
        self.tink, self.tred = temple(460)
        self.F = radial_field(*self.tink.shape, self.tink.shape[1] / 2, self.tink.shape[0], 44)
        self.plane(mountain(ridge(self.wext(11), 930, 70, 600, 45), 0.32, fall=150, shun=0.15, seed=45), 11)
        self.layers.insert(-1, ("fx", self.draw))

    def draw(self, t, A, R):
        p = ease((t - 0.8) / 2.8)
        if p <= 0:
            return
        rv = reveal(self.F, p, 0.12)
        h, w = self.tink.shape
        x, y = W / 2 - w / 2, 750 - h
        put_ink(A, R, self.tink * rv, x, y)
        put(R, self.tred * rv, x, y)


def make_path(pts, n=600):
    f = catmull_keys([(i / (len(pts) - 1), x, y) for i, (x, y) in enumerate(pts)])
    P = np.array([f(u) for u in np.linspace(0, 1, n)])
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)]); s /= s[-1]
    return lambda u: np.array([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])])


class Crowd:
    def __init__(self, seed):
        self.sizes = list(range(7, 52, 3))
        self.spr = {(s, v): person(s, seed + s * 7 + v) for s in self.sizes for v in range(3)}

    def draw(self, A, R, x, y, size, v, k=1.0):
        s = min(self.sizes, key=lambda q: abs(q - size))
        a = self.spr[(s, v % 3)]
        put_ink(A, R, a, x - a.shape[1] / 2, y - a.shape[0], k)


class S5(Scene):  # 徒步南下
    fog = ((560, 90, 0.7), (330, 80, 0.35))

    def build(self):
        self.sun = disc(78)
        self.fx(self.draw_sun)
        self.plane(mountain(ridge(self.wext(3), 470, 200, 400, 51, [(self.mid(3) + 600, 140, 180)]),
                            0.24, mist=(430, 610), seed=51), 3)
        self.plane(mountain(ridge(W + 8, 660, 170, 330, 52), 0.5, mist=(620, 800), seed=52), 0)
        self.fogpass()
        self.path = make_path([(250, 1120), (720, 930), (1330, 880), (1180, 720), (850, 640), (1080, 560)])
        pen = Pen(W, H)
        for u in np.linspace(0, 1, 500):
            x, y = self.path(u)
            wd = 150 * (1 - u) ** 1.3 + 10
            pen.ell(x, y, wd, wd * 0.18, 255 * 0.12)
        for side in (-1, 1):
            pts = []
            for u in np.linspace(0, 1, 200):
                x, y = self.path(u)
                wd = 150 * (1 - u) ** 1.3 + 10
                pts.append((x + side * wd * 0.9, y))
            pen.line(pts, 255 * 0.35, 1.6)
        self.plane(inkify(pen.arr(1.5), 53, 0.3), 0)
        self.crowd = Crowd(500)
        pw = 130
        self.pal_ink, self.pal_red = palanquin(pw)
        self.pal_cache = {}
        rng = np.random.default_rng(54)
        self.followers = [(0.012 * (i + 1) + rng.random() * 0.01, rng.normal() * 0.45, i) for i in range(80)]
        self.fx(self.draw)

    def draw_sun(self, t, A, R):
        y = 300 - 70 * t / self.dur
        put(R, self.sun, 1480 - self.sun.shape[1] / 2, y - self.sun.shape[0] / 2, 0.88)

    def scale(self, u):
        return (1 - u) ** 1.25

    def pal(self, size, A, R, x, y, bob):
        size = max(16, int(size / 4) * 4)
        if size not in self.pal_cache:
            self.pal_cache[size] = palanquin(size)
        ink, red = self.pal_cache[size]
        put_ink(A, R, ink, x - size / 2, y - ink.shape[0] + bob)
        put(R, red, x - size / 2, y - ink.shape[0] + bob)
        incense(R, x, y - ink.shape[0] + bob, size, ink.shape[0], self.t)

    def draw(self, t, A, R):
        self.t = t
        uh = 0.2 + 0.55 * t / self.dur
        items = [(uh, None)] + [(uh - du, (lat, i)) for du, lat, i in self.followers]
        for u, f in sorted(items, key=lambda z: -z[0]):
            if not (0.0 < u < 0.97):
                continue
            x, y = self.path(u)
            sc = self.scale(u)
            wd = 150 * (1 - u) ** 1.3 + 10
            if f is None:
                self.pal(130 * sc + 14, A, R, x, y, 2 * math.sin(t * 8))
            else:
                lat, i = f
                self.crowd.draw(A, R, x + lat * wd, y + 3 * math.sin(t * 6 + i), 52 * sc + 6, i)


class S6(Scene):  # 無路之路（神轎指引）
    fog = ((540, 120, 0.85), (860, 70, 0.35))

    def build(self):
        self.plane(mountain(ridge(self.wext(4), 520, 150, 360, 61), 0.22, mist=(470, 630), seed=61), 4)
        self.fogpass()
        self.plane(waves(self.wext(12), 640, 770, 7, 4, 0.42, 62), 12)
        self.key = catmull_keys([(0, -120, 980), (0.16, 640, 950), (0.28, 1150, 905), (0.38, 1060, 870),
                                 (0.5, 720, 840), (0.6, 760, 790), (0.74, 960, 715), (0.86, 1160, 650),
                                 (1.0, 1320, 610)])
        self.crowd = Crowd(600)
        self.pal_cache = {}
        rng = np.random.default_rng(63)
        self.followers = [(0.6 + 0.32 * i + rng.random() * 0.2, rng.normal() * 40, rng.normal() * 12, i)
                          for i in range(36)]
        self.ring = {}
        self.fx(self.draw)

    def scale(self, y):
        return float(np.interp(y, [600, 980], [0.42, 1.0]))

    def in_river(self, y):
        return 640 < y < 775

    def ripple(self, A, R, x, y, sc, ph):
        rx = int(30 * sc * (0.5 + ph)) + 4
        key = rx
        if key not in self.ring:
            pen = Pen(rx * 2 + 8, rx + 8)
            pen.ell(rx + 4, rx / 2 + 4, rx, rx * 0.3, 200)
            pen.ell(rx + 4, rx / 2 + 4, rx - 2.5, rx * 0.3 - 2, 0)
            self.ring[key] = pen.arr(0.6)
        a = self.ring[key]
        put_ink(A, R, a, x - a.shape[1] / 2, y - a.shape[0] / 2, 0.6 * (1 - ph))

    def draw(self, t, A, R):
        T = self.dur
        items = []
        for d, dx, dy, i in self.followers:
            u = (t - d) / T
            if u < 0:
                continue
            x, y = self.key(u)
            sc = self.scale(y)
            items.append((y + dy * sc, x + dx * sc, sc, i))
        x, y = self.key(t / T)
        items.append((y, x, self.scale(y), None))
        for y, x, sc, i in sorted(items, key=lambda z: z[0]):
            if self.in_river(y):
                ph = ((t * 1.2 + (i or 0) * 0.37) % 1.0)
                self.ripple(A, R, x, y, sc, ph)
            if i is None:
                size = max(16, int((170 * sc) / 4) * 4)
                if size not in self.pal_cache:
                    self.pal_cache[size] = palanquin(size)
                ink, red = self.pal_cache[size]
                bob = 3 * math.sin(t * 10)
                put_ink(A, R, ink, x - size / 2, y - ink.shape[0] + bob)
                put(R, red, x - size / 2, y - ink.shape[0] + bob)
                incense(R, x, y - ink.shape[0] + bob, size, ink.shape[0], t)
            else:
                self.crowd.draw(A, R, x, y + 3 * math.sin(t * 7 + i), 58 * sc, i,
                                0.75 if self.in_river(y) else 1.0)


class S7(Scene):  # 刈火（夜）
    def build(self):
        yy, xx = np.mgrid[0:H, 0:W].astype(f32)
        vig = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
        night = 0.5 + 0.18 * vig + 0.08 * (fbm2d(H, W, 300, 4, 71) - 0.5)
        self.plane(np.clip(night, 0, 0.85).astype(f32), 0)
        tw = 2400
        ti, _ = temple(tw, 0.95)
        yo = int(-0.42 * ti.shape[0] + 260)
        rp = np.zeros((H, W + 8), f32)
        x0 = (W - tw) // 2
        crop = ti[max(0, -yo):int(0.43 * ti.shape[0]), max(0, -x0):max(0, -x0) + W]
        rp[max(0, yo):max(0, yo) + crop.shape[0], :crop.shape[1]] = crop
        pen = Pen(W + 8, H)
        for cx in (230, 1690):
            pen.rect(cx - 28, 200, cx + 28, H, 235)
        rp = 1 - (1 - rp) * (1 - inkify(pen.arr(1.0), 72, 0.2))
        self.plane(rp, 0)
        self.bur = burner(360)
        self.lightg = glow(520)
        self.g = glow(160)
        self.fire_n = fbm2d(1400, 300, 40, 4, 73)
        rng = np.random.default_rng(74)
        self.sparks = [(rng.random() * 6, rng.normal() * 40, 40 + rng.random() * 70, rng.random() * 6.28) for _ in range(45)]
        self.dot = glow(5)
        self.carrier = person(130, 75, hat=True)
        self.pot = glow(26)
        self.fx(self.draw)

    def draw(self, t, A, R):
        cx, cy = 960, 690
        fl = 0.85 + 0.1 * math.sin(t * 11) + 0.05 * math.sin(t * 23)
        g = self.lightg
        ya, xa = int(cy - g.shape[0] / 2), int(cx - g.shape[1] / 2)
        y0, y1, x0, x1 = max(0, ya), min(H, ya + g.shape[0]), max(0, xa), min(W, xa + g.shape[1])
        A[y0:y1, x0:x1] *= 1 - 0.6 * fl * g[y0 - ya:y1 - ya, x0 - xa:x1 - xa]
        b = self.bur
        put_ink(A, R, b, cx - b.shape[1] / 2, 940 - b.shape[0])
        # 火焰
        fw, fh = 300, 380
        off = int((t * 260) % 1000)
        n = self.fire_n[off:off + fh, :fw]
        yy, xx = np.mgrid[0:fh, 0:fw].astype(f32)
        v = yy / fh
        wdt = 0.08 + 0.28 * (v ** 0.7)
        sway = 0.06 * math.sin(t * 3) * (1 - v)
        d = np.abs((xx / fw - 0.5 - sway)) / wdt
        flame = smooth(1.0 - d - 0.9 * (n - 0.5) - (1 - v) * 0.55, 0, 0.3) * smooth(v, 0.0, 0.5)
        put(R, flame.astype(f32), cx - fw / 2, 940 - b.shape[0] + 30 - fh, 0.92)
        put(R, self.g, cx - 160, cy - 160 - 60, 0.32 * fl)
        for t0, dx, sp, ph in self.sparks:
            age = (t + t0) % 3.0
            x = cx + dx + 25 * math.sin(age * 2 + ph)
            y = 600 - age * sp * 1.6
            put(R, self.dot, x - 5, y - 5, max(0, 0.9 * (1 - age / 3.0)))
        # 專人護送火爐
        u = (t - self.dur * 0.5) / (self.dur * 0.5)
        if u > 0:
            k = smooth(u, 0, 0.12)
            px = 1110 + 520 * u
            py = 1010 - 40 * u
            c = self.carrier
            put_ink(A, R, c, px - c.shape[1] / 2, py - c.shape[0] + 3 * math.sin(t * 7), k)
            put(R, self.pot, px + 18 - 26, py - 92 - 26, 0.8 * k * fl)


class S8(Scene):  # 回鑾
    fog = ((610, 45, 0.5),)

    def build(self):
        self.sun = disc(95)
        self.fx(self.draw_sun)
        self.plane(waves(self.wext(6), 520, 660, 6, 3, 0.32, 81), 6)
        self.fogpass()
        pen = Pen(W, H)
        for side in (-1, 1):
            pen.line([(960 + side * 40, 650), (960 + side * 560, H + 20)], 255 * 0.3, 1.6)
        self.plane(inkify(pen.arr(1.2), 82, 0.3), 0)
        xs = [150, 300, 430, 560, 1300, 1430, 1580, 1720]
        self.plane(houses(W + 8, xs, 660, 83), 0)
        self.tink, self.tred = temple(260)
        self.crowd = Crowd(800)
        rng = np.random.default_rng(84)
        self.spect = []
        for side in (-1, 1):
            for k in range(40):
                v = (k + rng.random() * 0.6) / 40
                y = 660 + (H + 20 - 660) * v ** 1.25
                x = 960 + side * (40 + 520 * (y - 650) / (H - 630) + 30 + rng.random() * 60)
                self.spect.append((y, x, k + (side > 0) * 100))
        self.pal_cache = {}
        self.fx(self.draw)

    def draw_sun(self, t, A, R):
        y = 520 - 110 * ease(t / self.dur)
        put(R, self.sun, 1500 - self.sun.shape[1] / 2, y - self.sun.shape[0] / 2, 0.85)

    def draw(self, t, A, R):
        h, w = self.tink.shape
        put_ink(A, R, self.tink, 960 - w / 2, 662 - h)
        put(R, self.tred, 960 - w / 2, 662 - h)
        u = t / self.dur
        py = 1060 - 360 * ease(u * 0.95)
        items = [(y, x, i) for y, x, i in self.spect] + [(py, 960, None)]
        for y, x, i in sorted(items, key=lambda z: z[0]):
            sc = float(np.interp(y, [650, H], [0.28, 1.0]))
            if i is None:
                size = max(16, int((160 * sc) / 4) * 4)
                if size not in self.pal_cache:
                    self.pal_cache[size] = palanquin(size)
                ink, red = self.pal_cache[size]
                put_ink(A, R, ink, x - size / 2, y - ink.shape[0] + 2 * math.sin(t * 9))
                put(R, red, x - size / 2, y - ink.shape[0] + 2 * math.sin(t * 9))
                incense(R, x, y - ink.shape[0] + 2 * math.sin(t * 9), size, ink.shape[0], t)
            else:
                self.crowd.draw(A, R, x, y + 2 * math.sin(t * 3 + i), 60 * sc, i)


class S9(Scene):  # 片尾
    fog = ((640, 110, 0.7), (420, 80, 0.35))

    def build(self):
        self.plane(mountain(ridge(self.wext(3), 580, 230, 420, 91, [(self.mid(3) + 1100, 170, 170),
                                                                     (self.mid(3) + 1500, 120, 140)]),
                            0.2, mist=(520, 720), seed=91), 3)
        self.fogpass()
        self.build_plum()
        e = self.info.get("end_at", self.dur - END_HOLD)
        self.end_at = e
        self.c1 = InkText(text_v("天上聖母　林默娘", 92, bold=2), 92, 0.88)
        self.c2 = InkText(text_v("生於北宋建隆元年　西元九六○年", 44), 93, 0.85)
        self.c3 = InkText(text_v("卒於北宋雍熙四年　西元九八七年", 44), 94, 0.85)
        self.seal = make_seal("天上聖母", 120, 95)
        self.mazu = load_img("mazu_main.png", 780)
        self.mF = radial_field(*self.mazu[1].shape, self.mazu[1].shape[1] / 2, self.mazu[1].shape[0] * 0.9, 98, 0.4)
        self.fx(self.draw)

    def build_plum(self):
        rng = np.random.default_rng(96)
        Wp, Hp = 1000, 900
        ink = Pen(Wp, Hp)
        order = Image.new("L", (Wp * 2, Hp * 2), 255)
        od = ImageDraw.Draw(order)
        self.blooms = []

        def branch(x, y, ang, length, width, depth, t0):
            steps = int(length / 14) + 1
            t = t0
            for s in range(steps):
                ang += rng.normal() * 0.18
                nx, ny = x + 14 * math.cos(ang), y + 14 * math.sin(ang)
                wv = width * (1 - 0.6 * s / steps)
                ink.line([(x, y), (nx, ny)], 255 * (0.65 + 0.3 * rng.random()), wv)
                t += 14 / 1400
                od.line([(x * 2, y * 2), (nx * 2, ny * 2)], fill=int(min(254, t * 255)), width=int(wv * 2 + 10))
                if depth > 0 and rng.random() < 0.09 and s > 2:
                    branch(nx, ny, ang + rng.choice([-1, 1]) * (0.5 + rng.random() * 0.5),
                           length * 0.5, wv * 0.6, depth - 1, t)
                if depth < 2 and rng.random() < 0.12:
                    self.blooms.append((nx + rng.normal() * 6, ny + rng.normal() * 6, 9 + rng.random() * 8, t + 0.08))
                x, y = nx, ny
            self.blooms.append((x, y, 12 + rng.random() * 6, t + 0.05))

        branch(-20, 820, -0.55, 760, 24, 3, 0.0)
        branch(-20, 700, -0.2, 420, 14, 2, 0.12)
        a = ink.arr(0.8)
        self.plum = inkify(a, 97, 0.35, 0.3)
        o = np.asarray(order.resize((Wp, Hp), Image.NEAREST), f32) / 255
        self.order = grey_erosion(o, size=(5, 5))
        self.bspr = {}
        self.px, self.py = 0, H - Hp - 40

    def draw(self, t, A, R):
        q = ease((t - 1.0) / 3.0)
        if q > 0:
            put_img(A, R, self.mazu, 770, 90, reveal(self.mF, q, 0.15) * 0.92)
        p = (t - 0.6) / 5.0
        if p > 0:
            rv = np.clip((p - self.order) / 0.03 + 1, 0, 1) * (self.order < 0.999)
            put_ink(A, R, self.plum * rv, self.px, self.py)
        for x, y, r, tb in self.blooms:
            q = smooth(p - tb, 0, 0.12)
            if q <= 0:
                continue
            rr = max(3, int(r * q))
            if rr not in self.bspr:
                self.bspr[rr] = blossom(rr)
            red, dots = self.bspr[rr]
            put(R, red, self.px + x - red.shape[1] / 2, self.py + y - red.shape[0] / 2, 0.85)
            put_ink(A, R, dots, self.px + x - red.shape[1] / 2, self.py + y - red.shape[0] / 2, 0.8 * q)
        e = self.end_at
        x = 1600
        for txt, dx, dy, t0 in ((self.c1, 0, 140, 0.0), (self.c2, -135, 230, 1.0), (self.c3, -215, 230, 1.6)):
            a = txt.alpha((t - e - t0) / 1.6)
            if a is not None:
                put_ink(A, R, a, x + dx, dy)
        k = smooth(t - e, 3.2, 3.35)
        if k > 0:
            put(R, self.seal, 1245, 880, float(k))
        # 最後淡出成宣紙
        fo = smooth(t, self.dur - 1.6, self.dur - 0.1)
        if fo > 0:
            A *= 1 - fo; R *= 1 - fo


# ═════════════════════════ 刻舟求劍：素材 ═════════════════════════
_ring_cache = {}


def ring(r, th=3.0, soft=2.0):
    key = (round(float(r), 1), round(float(th), 1), round(float(soft), 1))
    if key not in _ring_cache:
        s = int(r * 2 + soft * 2 + 8)
        yy, xx = np.mgrid[0:s, 0:s].astype(f32)
        d = np.hypot(xx - s / 2, yy - s / 2)
        _ring_cache[key] = smooth(th / 2 - np.abs(d - r), -soft, soft).astype(f32)
    return _ring_cache[key]


def scale_img(a, k):
    h, w = a.shape
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    im = im.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    return np.asarray(im, f32) / 255


def rot_img(a, deg):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    im = im.rotate(deg, resample=Image.BICUBIC, expand=True)
    return np.asarray(im, f32) / 255


def skiff(w):
    """小船：翹首、平底、一道坐板。"""
    h = int(w * 0.42)
    pen = Pen(w, h)
    top = 0.46 * h
    hull = [(0.02 * w, top + 0.08 * h), (0.14 * w, top), (0.86 * w, top), (0.98 * w, top + 0.08 * h),
            (0.90 * w, top + 0.34 * h), (0.50 * w, top + 0.46 * h), (0.10 * w, top + 0.34 * h)]
    pen.poly(hull, 200)
    inner = [(0.10 * w, top + 0.03 * h), (0.18 * w, top + 0.02 * h), (0.82 * w, top + 0.02 * h),
             (0.90 * w, top + 0.03 * h), (0.82 * w, top + 0.26 * h), (0.50 * w, top + 0.36 * h),
             (0.18 * w, top + 0.26 * h)]
    pen.poly(inner, 72)
    pen.line([(0.02 * w, top + 0.08 * h), (0.14 * w, top), (0.86 * w, top), (0.98 * w, top + 0.08 * h)],
             242, max(2, 0.012 * w))
    pen.line([(0.10 * w, top + 0.03 * h), (0.18 * w, top + 0.02 * h), (0.82 * w, top + 0.02 * h),
              (0.90 * w, top + 0.03 * h)], 198, max(1, 0.006 * w))
    pen.line([(0.02 * w, top + 0.08 * h), (0.0, top - 0.02 * h)], 238, max(2, 0.008 * w))
    pen.line([(0.98 * w, top + 0.08 * h), (w, top - 0.02 * h)], 238, max(2, 0.008 * w))
    for u in (0.18, 0.27, 0.36):
        pen.line([(0.12 * w, top + u * h), (0.50 * w, top + (u + 0.05) * h), (0.88 * w, top + u * h)],
                 174, max(1, 0.004 * w))
    pen.rect(0.34 * w, top + 0.08 * h, 0.66 * w, top + 0.145 * h, 182)
    pen.ell(0.14 * w, top + 0.045 * h, 0.035 * w, 0.018 * h, 216)
    pen.ell(0.14 * w, top + 0.045 * h, 0.022 * w, 0.010 * h, 148)
    return inkify(pen.arr(0.8), 11, 0.10, 0.22)


def sword_img(L=150):
    """劍尖朝下的完整剪影：劍身、護手、握柄、劍首與劍穗。"""
    w = max(30, int(L * 0.42))
    pen = Pen(w, L + 10)
    cx = w / 2
    bw = max(4, int(L * 0.042))
    pen.poly([(cx - bw * 0.9, 0.26 * L), (cx + bw * 0.9, 0.26 * L),
              (cx + bw * 0.35, 0.88 * L), (cx, 0.97 * L),
              (cx - bw * 0.35, 0.88 * L)], 236)
    pen.line([(cx, 0.28 * L), (cx, 0.92 * L)], 178, max(1, int(L * 0.010)))
    pen.rect(cx - 0.20 * L, 0.225 * L, cx + 0.20 * L, 0.265 * L, 242)
    pen.line([(cx - 0.20 * L, 0.245 * L), (cx - 0.22 * L, 0.20 * L)], 240, 3)
    pen.line([(cx + 0.20 * L, 0.245 * L), (cx + 0.22 * L, 0.20 * L)], 240, 3)
    pen.line([(cx, 0.10 * L), (cx, 0.225 * L)], 190, max(7, int(L * 0.075)))
    pen.ell(cx, 0.085 * L, max(4, L * 0.040), max(4, L * 0.040), 228)
    pen.line([(cx + 4, 0.10 * L), (cx + 0.12 * L, 0.15 * L),
              (cx + 0.10 * L, 0.24 * L)], 205, 2)
    return inkify(pen.arr(0.35), 17, 0.05, 0.08)


def bird_img(w=34):
    pen = Pen(w, int(w * 0.5), S=1)
    cy = w * 0.25
    pen.line([(2, cy + 3), (w / 2, cy - 4), (w - 2, cy + 3)], 188, 2)
    return gaussian_filter(pen.arr(0.4), 0.5)


def wake_img(w=320, h=42, seed=12):
    rng = np.random.default_rng(seed)
    pen = Pen(w, h)
    for i in range(8):
        y = h * 0.5 + rng.uniform(-h * 0.22, h * 0.22)
        pen.line([(rng.uniform(0, 0.2) * w, y), (rng.uniform(0.55, 1.0) * w, y + rng.uniform(-2, 2))],
                 int(rng.uniform(115, 205)), rng.uniform(1, 3))
    return inkify(pen.arr(0.5), seed, 0.18, 0.12)


def spray_img(w=120, h=60, seed=78):
    """落水瞬間的低矮水花：扇形短線與幾顆水滴。"""
    rng = np.random.default_rng(seed)
    pen = Pen(w, h, S=1)
    for i in range(7):
        x0 = w * 0.5 + rng.uniform(-0.08, 0.08) * w
        ang = math.pi * (0.12 + 0.76 * (i / 6.0))
        L = rng.uniform(0.30, 0.72) * h
        x1 = x0 + math.cos(ang) * L * 0.85
        y1 = h - math.sin(ang) * L
        pen.line([(x0, h), (x1, y1)], int(rng.uniform(175, 235)),
                 rng.uniform(1.2, 2.3))
    for i in range(6):
        pen.ell(rng.uniform(0.2, 0.8) * w, rng.uniform(0.08, 0.55) * h,
                rng.uniform(1.0, 2.6), rng.uniform(1.0, 2.6), 220)
    return pen.arr(0.4)


def hand_img(w=76):
    h = int(w * 1.1)
    pen = Pen(w, h)
    cx, cy = w * 0.46, h * 0.44
    pen.ell(cx, cy, w * 0.25, h * 0.18, 222)
    for i in range(3):
        pen.line([(cx - w * 0.10, cy + h * 0.00 + i * 3),
                  (cx - w * 0.35, cy + h * 0.08 + i * 2)], 230, 4)
    pen.line([(cx + w * 0.02, cy - h * 0.03), (cx + w * 0.19, cy - h * 0.17)], 226, 5)
    return inkify(pen.arr(0.5), 91, 0.10, 0.20)


def knife_img(hx, hy, tx, ty):
    x0, y0 = int(min(hx, tx) - 30), int(min(hy, ty) - 30)
    w, h = int(abs(hx - tx) + 60), int(abs(hy - ty) + 60)
    pen = Pen(w, h, S=1)
    p1, p2 = (hx - x0, hy - y0), (tx - x0, ty - y0)
    pen.line([p1, p2], 238, 9)
    dx, dy = p1[0] - p2[0], p1[1] - p2[1]
    L = max(1.0, math.hypot(dx, dy))
    ux, uy = dx / L, dy / L
    pen.line([p1, (p1[0] + ux * 34, p1[1] + uy * 34)], 172, 16)
    gx, gy = -uy * 12, ux * 12
    pen.line([(p1[0] - gx, p1[1] - gy), (p1[0] + gx, p1[1] + gy)], 226, 5)
    return pen.arr(0.4), x0, y0


def blade_img(hx, hy, tx, ty):
    """只畫刀身與護手；刀柄藏在袖口裡。"""
    x0, y0 = int(min(hx, tx) - 26), int(min(hy, ty) - 26)
    x1, y1 = int(max(hx, tx) + 26), int(max(hy, ty) + 26)
    pen = Pen(max(1, x1 - x0), max(1, y1 - y0), S=1)
    p1, p2 = (hx - x0, hy - y0), (tx - x0, ty - y0)
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = max(1.0, math.hypot(dx, dy))
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    pen.poly([(p1[0] + px * 6, p1[1] + py * 6), (p2[0] + px * 1.5, p2[1] + py * 1.5),
              (p2[0] - px * 1.5, p2[1] - py * 1.5), (p1[0] - px * 6, p1[1] - py * 6)], 238)
    pen.line([(p1[0] + px * 16, p1[1] + py * 16), (p1[0] - px * 16, p1[1] - py * 16)], 238, 6)
    pen.line([(p1[0], p1[1]), (p2[0], p2[1])], 178, 2)
    return pen.arr(0.45), x0, y0


def grip_knife_img(hx, hy, tx, ty, w=150):
    """手與刀一起畫：刀身、刀柄、護手、拳頭、四指、拇指。"""
    x0, y0 = int(min(hx, tx) - w * 0.62), int(min(hy, ty) - w * 0.62)
    x1, y1 = int(max(hx, tx) + w * 0.62), int(max(hy, ty) + w * 0.62)
    W, H = max(1, x1 - x0), max(1, y1 - y0)
    pen = Pen(W, H, S=1)
    hx0, hy0, tx0, ty0 = hx - x0, hy - y0, tx - x0, ty - y0
    dx, dy = tx0 - hx0, ty0 - hy0
    L = max(1.0, math.hypot(dx, dy))
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    bx, by = hx0 + ux * 28, hy0 + uy * 28
    pen.poly([(bx + px * 6, by + py * 6), (tx0 + px * 1.5, ty0 + py * 1.5),
              (tx0 - px * 1.5, ty0 - py * 1.5), (bx - px * 6, by - py * 6)], 238)
    hx1, hy1 = hx0 - ux * 52, hy0 - uy * 52
    pen.line([(hx0, hy0), (hx1, hy1)], 168, 16)
    pen.line([(bx + px * 12, by + py * 12), (bx - px * 12, by - py * 12)], 238, 6)
    pen.ell(hx0, hy0, 40, 34, 238)
    pen.ell(hx0, hy0, 35, 29, 198)
    for i in range(4):
        cx = hx0 + ux * (-20 + 13 * i)
        cy = hy0 + uy * (-20 + 13 * i)
        pen.line([(cx + px * 24, cy + py * 24), (cx - px * 24, cy - py * 24)],
                 238, 5)
    pen.line([(hx0 - ux * 8 + px * 20, hy0 - uy * 8 + py * 20),
              (hx0 + ux * 16 + px * 16, hy0 + uy * 16 + py * 16),
              (hx0 + ux * 28 + px * 4, hy0 + uy * 28 + py * 4)], 236, 7)
    return pen.arr(0.5), x0, y0


def mark_img(size=120):
    s = float(size)
    pen = Pen(size, size)
    pen.line([(0.25 * s, 0.18 * s), (0.50 * s, 0.80 * s)], 246, max(7, 0.10 * s))
    pen.line([(0.50 * s, 0.80 * s), (0.76 * s, 0.18 * s)], 238, max(6, 0.09 * s))
    pen.poly([(0.44 * s, 0.66 * s), (0.50 * s, 0.82 * s), (0.56 * s, 0.66 * s)], 250)
    return inkify(pen.arr(0.45), 93, 0.15, 0.20)


def interior_img(w=2000, h=240, seed=66):
    pen = Pen(w, h)
    pen.poly([(0, 46), (w, 0), (w, h), (0, h)], 92)
    pen.line([(0, 46), (w, 0)], 224, 8)
    pen.poly([(0.24 * w, 0.56 * h), (0.74 * w, 0.44 * h),
              (0.75 * w, 0.61 * h), (0.23 * w, 0.73 * h)], 158)
    for u in (0.20, 0.38, 0.56):
        pen.line([(0.05 * w, u * h), (0.95 * w, (u - 0.05) * h)], 132, 2)
    pen.ell(0.80 * w, 0.40 * h, 30, 12, 208)
    pen.ell(0.80 * w, 0.40 * h, 18, 7, 140)
    return inkify(pen.arr(0.9), seed, 0.10, 0.22)


def carver_body(w=520, h=500, seed=67):
    pen = Pen(w, h)
    pen.poly([(150, 180), (390, 160), (470, 500), (120, 500)], 120)
    pen.poly([(180, 100), (330, 80), (390, 180), (360, 300), (190, 300)], 138)
    pen.ell(300, 150, 82, 55, 146)
    pen.poly([(224, 138), (204, 154), (226, 164)], 150)
    pen.ell(300, 42, 22, 27, 224)
    pen.ell(290, 75, 40, 46, 228)
    pen.poly([(243, 62), (290, 38), (337, 62), (326, 74), (254, 74)], 212)
    pen.line([(250, 120), (290, 178), (330, 120)], 214, 5)
    pen.line([(170, 270), (400, 280)], 180, 7)
    pen.line([(390, 160), (470, 500)], 196, 4)
    for u in (0.34, 0.46, 0.58):
        pen.line([(0.20 * w, u * h), (0.46 * w, u * h + 0.07 * h), (0.70 * w, u * h)], 160, 2)
    return inkify(pen.arr(0.9), seed, 0.08, 0.20)


def carver_arm(w=300, h=340, seed=68):
    """彎曲的短袖：肩 → 肘 → 袖口；手掌與刀另外疊。"""
    pen = Pen(w, h)
    body = [(270, 0), (300, 70), (285, 160), (250, 220), (175, 285),
            (115, 265), (135, 215), (195, 160), (215, 80), (225, 20)]
    pen.poly(body, 150)
    pen.line([(270, 0), (300, 70), (285, 160), (250, 220), (175, 285)], 214, 5)
    pen.poly([(105, 248), (180, 288), (190, 322), (112, 282)], 226)
    pen.line([(285, 70), (245, 150), (200, 210), (150, 255)], 180, 2)
    pen.line([(250, 220), (195, 240), (150, 258)], 180, 2)
    pen.line([(225, 20), (220, 90), (205, 150)], 180, 2)
    pen.line([(135, 215), (195, 160), (215, 80)], 106, 6)
    return inkify(pen.arr(0.9), seed, 0.08, 0.20)


def sleeve_band(w=760, h=260, seed=68):
    """只從畫面右緣伸入的寬袖；帶狀，不畫身體。"""
    pen = Pen(w, h)
    body = [(w, 0), (0.55 * w, 40), (0.33 * w, 90), (80, 110),
            (80, 190), (0.33 * w, 220), (0.55 * w, 250), (w, 260)]
    pen.poly(body, 150)
    pen.line([(w, 0), (0.55 * w, 40), (0.33 * w, 90), (80, 110)], 214, 5)
    pen.line([(80, 190), (0.33 * w, 220), (0.55 * w, 250), (w, 260)], 210, 4)
    pen.poly([(58, 100), (138, 126), (138, 206), (58, 180)], 226)
    pen.line([(58, 100), (138, 126)], 242, 4)
    pen.line([(0.62 * w, 55), (0.40 * w, 105), (0.28 * w, 145)], 182, 2)
    pen.line([(0.62 * w, 205), (0.40 * w, 175), (0.28 * w, 165)], 182, 2)
    pen.line([(0.82 * w, 30), (0.60 * w, 90), (0.44 * w, 135)], 186, 2)
    return inkify(pen.arr(0.85), seed, 0.07, 0.20)


def grip_hand(w=130, seed=69):
    """握刀的拳頭：淡墨掌背、四指橫扣、拇指與腕口。"""
    h = int(w * 1.0)
    pen = Pen(w, h)
    cx, cy = w * 0.50, h * 0.48
    pen.ell(cx, cy, w * 0.29, h * 0.23, 235)
    pen.ell(cx, cy, w * 0.25, h * 0.19, 188)
    for i in range(4):
        y = h * (0.42 + 0.10 * i)
        pen.line([(w * 0.26, y), (w * 0.72, y + h * 0.035)],
                 238, max(4, int(w * 0.050)))
        pen.ell(w * 0.26, y, w * 0.038, w * 0.032, 238)
    pen.line([(w * 0.30, h * 0.30), (w * 0.64, h * 0.22), (w * 0.74, h * 0.40)],
             236, max(5, int(w * 0.060)))
    pen.line([(w * 0.70, h * 0.36), (w * 0.88, h * 0.48)],
             210, max(4, int(w * 0.040)))
    return inkify(pen.arr(0.5), seed, 0.08, 0.18)



def hull_closeup(w=2000, h=500, seed=61):
    pen = Pen(w, h)

    def edge(x):
        return 80 + 58 * (x / w) + 7 * math.sin(x / w * math.pi * 1.15)

    xs = np.linspace(0, w, 64)
    pts = [(float(x), float(edge(x))) for x in xs] + [(w, h), (0, h)]
    pen.poly(pts, 82)
    for u in (0.22, 0.40, 0.58, 0.76):
        pp = [(float(x), float(edge(x) + u * (h - edge(x)))) for x in np.linspace(0, w, 36)]
        pen.line(pp, 138, 3)
    rng = np.random.default_rng(seed)
    for i in range(100):
        x0 = rng.uniform(0, w)
        y0 = rng.uniform(edge(x0) + 40, h - 8)
        L = rng.uniform(35, 180)
        pen.line([(x0, y0), (x0 + L, y0 + rng.uniform(-6, 6))],
                 int(rng.uniform(55, 115)), rng.uniform(0.5, 2.0))
    for x in (430, 930, 1430):
        pen.line([(x, edge(x)), (x + 4, h)], 108, 2)
    for i in range(10):
        cx = rng.uniform(40, w - 40)
        cy = rng.uniform(edge(cx) + 60, h - 30)
        rx = rng.uniform(8, 24)
        pen.ell(cx, cy, rx, rx * rng.uniform(0.35, 0.62), 112)
    # 船舷上緣：厚木條 + 下方陰影
    rail = [(float(x), float(edge(x) - 7)) for x in np.linspace(0, w, 60)]
    rail += [(float(x), float(edge(x) + 23)) for x in np.linspace(w, 0, 60)]
    pen.poly(rail, 226)
    pen.poly([(float(x), float(edge(x) + 23)) for x in np.linspace(0, w, 50)] +
             [(float(x), float(edge(x) + 48)) for x in np.linspace(w, 0, 50)], 58)
    pen.line([(x, edge(x) - 3) for x in np.linspace(0, w, 50)], 246, 4)
    # 纜繩盤
    rx, ry = 0.35 * w, edge(0.35 * w) + 62
    for k in range(3):
        pen.ell(rx, ry, 34 - k * 5, 13 - k * 2, 214)
    pen.line([(rx + 30, ry), (rx + 90, ry + 34)], 208, 3)
    # 釘頭
    for x in np.linspace(90, w - 80, 18):
        pen.ell(x, edge(x) + 14, 2.2, 2.2, 242)
    a = pen.arr(1.0) * np.linspace(1.10, 0.84, h)[:, None]
    return inkify(np.clip(a, 0, 1), seed, 0.07, 0.15)


def sleeve_img(w=920, h=430, seed=62):
    pen = Pen(w, h)
    body = [(w, 0), (w * 0.72, 0.10 * h), (w * 0.45, 0.28 * h), (w * 0.23, 0.48 * h),
            (w * 0.18, 0.62 * h), (w * 0.26, 0.72 * h), (w * 0.42, 0.62 * h),
            (w * 0.62, 0.48 * h), (w * 0.82, 0.30 * h), (w, 0.22 * h)]
    pen.poly(body, 168)
    pen.poly([(w * 0.18, 0.55 * h), (w * 0.25, 0.50 * h), (w * 0.30, 0.62 * h),
              (w * 0.22, 0.70 * h)], 226)
    for u in (0.35, 0.48, 0.60, 0.72):
        pen.line([(w * 0.9, u * h), (w * 0.55, u * h + 0.12 * h), (w * 0.3, u * h + 0.2 * h)], 208, 2)
    pen.line([(w, 0), (w * 0.72, 0.10 * h), (w * 0.45, 0.28 * h), (w * 0.23, 0.48 * h)], 226, 5)
    return inkify(pen.arr(0.9), seed, 0.08, 0.20)


def bank_img(w=520, h=300, seed=81):
    """低矮沙岸：從右下角斜入水面，只有濕邊較深。"""
    pen = Pen(w, h)
    top = [(0, 0.88 * h), (0.08 * w, 0.76 * h), (0.20 * w, 0.70 * h),
           (0.35 * w, 0.62 * h), (0.55 * w, 0.58 * h), (0.75 * w, 0.50 * h),
           (w, 0.54 * h)]
    pts = top + [(w, h), (0, h)]
    pen.poly(pts, 165)
    rng = np.random.default_rng(seed)
    dense = []
    for i in range(len(top) - 1):
        for u in np.linspace(0, 1, 14, endpoint=False):
            dense.append((top[i][0] + (top[i + 1][0] - top[i][0]) * u,
                          top[i][1] + (top[i + 1][1] - top[i][1]) * u))
    dense.append(top[-1])
    # 濕邊：斷續的深線，避免變成一塊硬梆梆的平台
    for i in range(7):
        x0 = (i / 7.0) * w + rng.uniform(-10, 10)
        x1 = x0 + rng.uniform(0.10, 0.20) * w
        seg = [(x, y) for x, y in dense if x0 <= x <= x1]
        if len(seg) >= 2:
            pen.line(seg, 182, 3)
    for i in range(12):
        y0 = rng.uniform(0.62 * h, h)
        x0 = rng.uniform(0, 0.82 * w)
        pen.line([(x0, y0), (x0 + rng.uniform(30, 120), y0 + rng.uniform(-2, 2))],
                 int(rng.uniform(95, 150)), rng.uniform(1.0, 2.2))
    for i in range(5):
        cx = rng.uniform(0.05, 0.36) * w
        cy = rng.uniform(0.62, 0.80) * h
        rx = rng.uniform(0.02, 0.05) * w
        pen.ell(cx, cy, rx, rx * rng.uniform(0.5, 0.7), 195)
    a = pen.arr(1.0) * np.linspace(1.02, 0.94, h)[:, None]
    return inkify(np.clip(a, 0, 1), seed, 0.10, 0.22)


def reeds_img(w=360, h=320, seed=82, n=10):
    rng = np.random.default_rng(seed)
    pen = Pen(w, h)
    for i in range(n):
        x = w * (0.12 + 0.76 * rng.random())
        tipx = x + rng.uniform(-0.20, 0.20) * w
        tipy = h * (0.05 + 0.45 * rng.random())
        bend = rng.uniform(-0.10, 0.10) * w
        pts = [(x, h), (x + bend * 0.3, h * 0.78), (x + bend * 0.7, h * 0.52),
               (tipx - bend * 0.4, h * 0.30), (tipx, tipy)]
        pen.line(pts, 222, rng.uniform(2.0, 3.5))
        for k in range(3):
            yy = h * rng.uniform(0.25, 0.68)
            xx = x + bend * (1 - yy / h)
            pen.line([(xx, yy), (xx + rng.uniform(-28, 28), yy - rng.uniform(20, 55))], 205, 1.5)
        if rng.random() < 0.55:
            pen.ell(tipx, tipy, rng.uniform(2.5, 4.5), rng.uniform(6, 11), 230)
    return inkify(pen.arr(0.75), seed, 0.10, 0.20)


# ═════════════════════════ 刻舟求劍：場景 ═════════════════════════
class KTitle(Scene):
    fog = ((620, 150, 0.65),)

    def build(self):
        sp = 5
        self.plane(mountain(ridge(self.wext(sp), 580, 170, 420, 71,
                                  [(self.mid(sp) + 900, 120, 220)]),
                            0.16, mist=(520, 700), seed=71), sp)
        self.fogpass()
        self.plane(waves(self.wext(8), 760, 1080, 10, 4, 0.28, 72), 8)
        self.t1 = InkText(text_h(script["title"], 180, bold=2), 5, 0.90)
        self.t2 = InkText(text_h(script["subtitle"], 76, bold=1), 6, 0.86)
        self.seal = make_seal("求劍", 132, 9)
        self.skiff = skiff(220)
        self.man = person(96, 73, hat=True)
        self.fx(self.draw)

    def draw(self, t, A, R):
        bx = 1280 - 8 * t
        by = 760 + 3 * math.sin(0.8 * t)
        put_ink(A, R, self.skiff, bx, by)
        px = bx + 0.55 * self.skiff.shape[1] - self.man.shape[1] / 2
        py = by + 0.46 * self.skiff.shape[0] - self.man.shape[0] + 4
        put_ink(A, R, self.man, px, py)
        h1, w1 = self.t1.shape
        x1, y1 = 220, 250
        a = self.t1.alpha((t - 0.7) / 1.8)
        if a is not None:
            put_ink(A, R, a, x1, y1)
        h2, w2 = self.t2.shape
        a = self.t2.alpha((t - 2.0) / 1.5)
        if a is not None:
            put_ink(A, R, a, x1, y1 + h1 + 10)
        k = float(smooth(t, 3.3, 3.45))
        if k > 0:
            put(R, self.seal, x1 + w1 + 14, y1 + 60, k)


class K1(Scene):
    fog = ((620, 90, 0.65), (460, 120, 0.35))

    def build(self):
        a, b, c = 4, 7, 11
        self.plane(mountain(ridge(self.wext(a), 560, 180, 380, 31,
                                  [(self.mid(a) + 300, 120, 180), (self.mid(a) + 1150, 90, 240)]),
                            0.17, mist=(510, 690), seed=31), a)
        self.plane(mountain(ridge(self.wext(b), 675, 85, 300, 32), 0.30, mist=(640, 760), seed=32), b)
        self.fogpass()
        self.plane(waves(self.wext(c), 720, 1080, 16, 6, 0.45, 33), c)
        self.skiff = skiff(300)
        self.man = person(140, 41, hat=True)
        self.man_lean = rot_img(self.man, -22)
        self.sword = rot_img(scale_img(sword_img(125), 0.85), 18)
        self.sword_lean = rot_img(sword_img(125), -25)
        self.bird = bird_img(34)
        self.wake = wake_img(330, 42, 34)
        self.spray = spray_img(120, 60, 78)
        self.impact_wake = wake_img(200, 38, 79)
        self.drop = disc(3.0, 1.0)
        self.fx(self.draw)

    def draw(self, t, A, R):
        bx = 420 + 52 * t
        by = 742 + 4 * math.sin(1.05 * t)
        bw, bh = self.skiff.shape[1], self.skiff.shape[0]
        put_ink(A, R, self.wake, bx - 20, by + 0.80 * bh, 0.22)
        put_ink(A, R, self.skiff, bx, by)
        man = self.man if t < 5.75 else self.man_lean
        mw, mh = man.shape
        px = bx + 0.75 * bw - mw / 2
        py = by + 0.46 * bh - mh + 5
        put_ink(A, R, man, px, py)
        if t < 5.75:
            sx0, sy0 = px + 0.55 * mw, py + 0.30 * mh
            put_ink(A, R, self.sword_lean, sx0, sy0)
        elif t < 6.25:
            p = float(smooth(t, 5.75, 6.25))
            sx0, sy0 = px + 0.55 * mw, py + 0.30 * mh
            sw = rot_img(scale_img(sword_img(125), 1.0 - 0.1 * p), -25 + 100 * p)
            put_ink(A, R, sw, sx0 + 95 * p, sy0 + 55 * p * p, 1 - 0.3 * p)
        if t >= 6.25:
            dt = t - 6.25
            fx, fy = 1065, 842
            if dt < 0.75:
                put_ink(A, R, self.spray, fx - 60, fy - 55, 0.70 * (1 - dt / 0.75))
            if dt < 1.4:
                put_ink(A, R, self.impact_wake, fx - 100, fy - 14, 0.46 * (1 - dt / 1.4))
            for i in range(9):
                ang = 0.30 + i * 0.30
                vx, vy = 64 * math.cos(ang), 112 * math.sin(ang)
                dx = vx * dt
                dy = -vy * dt + 95 * dt * dt
                if dt < 0.6 and fy + dy < fy + 4:
                    put_ink(A, R, self.drop, fx + dx - 3, fy + dy - 3, 0.68 * (1 - dt / 0.6))
            for i in range(3):
                d = dt - i * 0.22
                if d > 0:
                    rr = ring(8 + 55 * d, 2.2, 2.0)
                    a = 0.42 * (1 - smooth(d, 0, 3.5))
                    put_ink(A, R, rr, fx - rr.shape[1] / 2, fy - rr.shape[0] / 2, a)
        for i in range(3):
            x = 1500 - t * (18 + 3 * i) - i * 80
            y = 180 + i * 38 + 6 * math.sin(t * 1.3 + i)
            put_ink(A, R, self.bird, x, y, 0.55)


class K2(Scene):
    fog = ((360, 80, 0.25),)

    def build(self):
        sp = 3
        self.plane(mountain(ridge(self.wext(sp), 350, 45, 300, 51), 0.13, mist=(320, 430), seed=51), sp)
        self.fogpass()
        self.plane(waves(self.wext(9), 820, 1080, 15, 6, 0.34, 52), 9)
        self.interior = interior_img(2000, 240, 66)
        self.hull = hull_closeup(2000, 430, 61)
        self.wash = waves(W, 0, 70, 5, 2, 0.50, 63)[:70]
        self.sleeve = sleeve_band(860, 260, 68)
        self.mark = mark_img(105)
        self.markF = radial_field(105, 105, 52, 52, 64, 0.35)
        self.chip = disc(3.0, 1.0)
        self.fx(self.draw)

    def draw(self, t, A, R):
        bob = 2.0 * math.sin(0.55 * t)
        hy = 450 + bob
        put_ink(A, R, self.interior, -40, 380 + bob * 0.6)
        kin = float(smooth(t, 0.6, 1.5))
        put_ink(A, R, self.hull, -40, hy)
        put_ink(A, R, self.wash, -40, 850, 0.55)
        pmark = float(smooth(t, 2.4, 5.4))
        if pmark > 0:
            put_ink(A, R, self.mark * reveal(self.markF, pmark, 0.18), 900, 680, 0.94)
        if kin > 0:
            put_ink(A, R, self.sleeve, 1060, 560 + bob * 0.4, kin)
            u = 0.5
            if 1.6 < t < 6.2:
                u = 0.5 + 0.5 * math.sin(2 * math.pi * 0.85 * (t - 2.0))
            hx, hyh = 1100 + 6 * (u - 0.5), 660 + bob + 3 * (u - 0.5)
            tx, ty = 960 + 6 * u, 740 + bob + 3 * u
            kimg, kx, ky = grip_knife_img(hx, hyh, tx, ty)
            put_ink(A, R, kimg, kx, ky, 0.95 * kin)
            for i in range(5):
                if t > 2.9 + i * 0.18:
                    a = 0.30 * (0.5 + 0.5 * math.sin(t * 7 + i))
                    put_ink(A, R, self.chip, 1000 + 20 * i, 780 + 8 * i, a)


class K3(Scene):
    fog = ((600, 100, 0.55), (430, 120, 0.30))

    def build(self):
        sp = 3
        self.plane(mountain(ridge(self.wext(sp), 560, 160, 380, 81), 0.16, mist=(510, 690), seed=81), sp)
        self.fogpass()
        self.plane(waves(self.wext(11), 720, 1080, 16, 6, 0.42, 82), 11)
        self.skiff = skiff(300)
        self.man = person(140, 83, hat=True)
        self.man_j = rot_img(self.man, 18)
        self.wake = wake_img(330, 40, 84)
        self.bank = bank_img(520, 300, 81)
        self.reeds1 = reeds_img(320, 320, 82, n=9)
        self.reeds2 = reeds_img(260, 280, 83, n=7)
        self.notch = scale_img(mark_img(80), 0.55)
        self.splash, _ = blob(24, 85)
        self.spray = spray_img(120, 70, 86)
        self.drop = disc(3.2, 1.0)
        self.fx(self.draw)

    def draw(self, t, A, R):
        put_ink(A, R, self.bank, 1500, 800, 0.92)
        put_ink(A, R, self.reeds1, 1600 + 3 * math.sin(0.8 * t), 760, 0.65)
        if t < 3.3:
            bx = 520 + 600 * ease(t / 3.2)
        else:
            bx = 1120 - 85 * max(0.0, t - 5.0)
        by = 750 + 4 * math.sin(1.1 * t)
        bw, bh = self.skiff.shape[1], self.skiff.shape[0]
        put_ink(A, R, self.wake, bx - 20, by + 0.80 * bh, 0.22)
        put_ink(A, R, self.skiff, bx, by)
        mw, mh = self.man.shape
        px = bx + 0.55 * bw - mw / 2
        py = by + 0.46 * bh - mh + 4
        if t < 3.3:
            put_ink(A, R, self.man, px, py)
        elif t < 4.15:
            p = (t - 3.3) / 0.85
            jx = px + 90 * p
            jy = py + (850 - py) * p - 150 * math.sin(math.pi * p)
            put_ink(A, R, self.man_j, jx, jy)
        if t > 4.3 and bx > -300:
            put_ink(A, R, self.notch, bx + 0.52 * bw - self.notch.shape[1] / 2,
                    by + 0.46 * bh - self.notch.shape[0] / 2, 0.75)
        if t >= 4.15:
            dt = t - 4.15
            ix, iy = 1375, 850
            if dt < 0.6:
                k = 0.65 * (1 - dt / 0.6)
                put_ink(A, R, self.splash, ix - self.splash.shape[1] / 2,
                        iy - self.splash.shape[0] / 2, k)
            if dt < 0.7:
                put_ink(A, R, self.spray, ix - 60, iy - 60, 0.62 * (1 - dt / 0.7))
            for i in range(10):
                ang = 0.20 + i * 0.28
                vx, vy = 62 * math.cos(ang), 108 * math.sin(ang)
                dx, dy = vx * dt, -vy * dt + 100 * dt * dt
                if dt < 0.6 and iy + dy < iy + 5:
                    put_ink(A, R, self.drop, ix + dx - 3, iy + dy - 3, 0.58 * (1 - dt / 0.6))
            for i in range(3):
                d = dt - i * 0.20
                if d > 0:
                    rr = ring(8 + 48 * d, 2.2, 2.0)
                    a = 0.28 * (1 - smooth(d, 0, 4.8))
                    put_ink(A, R, rr, ix - rr.shape[1] / 2, iy - rr.shape[0] / 2, a)
            if 0.8 < dt < 4.0:
                for i in range(6):
                    bx2 = ix + 18 * math.sin(i * 2.3 + dt * 2)
                    by2 = iy - 8 - 22 * ((dt + i * 0.3) % 1.2)
                    put_ink(A, R, self.drop, bx2, by2, 0.20 * (1 - smooth(dt, 2.5, 4.0)))
        put_ink(A, R, self.reeds2, 1760 + 3 * math.sin(0.7 * t + 1), 800, 0.90)


SCENES = {"title": KTitle, "s1": K1, "s2": K2, "s3": K3}


# ═════════════════════════ 疊加：題字、印章、字幕 ═════════════════════════
class Overlay:
    def __init__(self, tl):
        self.tl = tl
        self.tags = {}
        self.seal = make_seal("求劍", 66, 300)
        for i, sc in enumerate(script["scenes"]):
            if sc["tag"]:
                self.tags[sc["id"]] = (InkText(text_v(sc["tag"], 62, bold=1), 200 + i), sc["seal"])
        self.subs = []
        for s in tl["subs"]:
            self.subs.append((s["start"], s["end"], s["text"]))
        self.sub_cache = {}

    def tag(self, sid, tl_local, A, R):
        if sid not in self.tags:
            return
        it, seal = self.tags[sid]
        h, w = it.shape
        x, y = int(W - 60 - w), 50
        a = it.alpha((tl_local - 0.35) / 0.9)
        if a is not None:
            k = float(smooth(tl_local, 0.5, 1.5)) * 0.7
            reg = A[y:y + h, x:x + w]
            reg *= 1 - k * it.clear[:reg.shape[0], :reg.shape[1]]
            put_ink(A, R, a, x, y)
        if seal:
            k = smooth(tl_local, 2.4, 2.55)
            if k > 0:
                put(R, self.seal, x + w / 2 - 33, y + h - 6, float(k))

    def sub_img(self, text):
        if text not in self.sub_cache:
            a = text_h(text, 50, bold=1)
            h, w = a.shape
            bw, bh = w + 90, 86
            yy, xx = np.mgrid[0:bh, 0:bw].astype(f32)
            band = smooth(np.minimum(xx, bw - xx), 0, 40) * smooth(np.minimum(yy, bh - yy), 0, 12)
            band *= 0.92 + 0.08 * noise2d(bh, bw, 6, 20, len(text))
            txt = np.zeros((bh, bw), f32)
            oy = (bh - h) // 2 + 4
            txt[max(0, oy):oy + h, 45:45 + w] = a[:bh - max(0, oy)]
            txt = np.clip(inkify(txt, 7, 0.1, 0.2) * 0.95 + gaussian_filter(txt, 1.5) * 0.12, 0, 1)
            self.sub_cache[text] = (band.astype(f32), txt)
        return self.sub_cache[text]

    def subtitle(self, T, A, R):
        for s0, s1, text in self.subs:
            if s0 - 0.15 <= T <= s1 + 0.15:
                k = float(min(smooth(T, s0 - 0.15, s0), 1 - smooth(T, s1, s1 + 0.15)))
                band, txt = self.sub_img(text)
                bh, bw = band.shape
                x, y = int((W - bw) / 2), H - 52 - bh
                reg = (slice(y, y + bh), slice(x, x + bw))
                A[reg] *= 1 - 0.72 * k * band
                R[reg] *= 1 - 0.72 * k * band
                put(A, txt, x, y, k)


# ═════════════════════════ 影格 ═════════════════════════
_paper = None
_tfield = None


def paper():
    global _paper
    if _paper is None:
        lum = 1 + 0.035 * (fbm2d(H, W, 128, 5, 1) - 0.5) + 0.025 * (noise2d(H, W, 2, 24, 2) - 0.5) \
              + 0.012 * (noise2d(H, W, 1, 1, 3) - 0.5)
        yy, xx = np.mgrid[0:H, 0:W].astype(f32)
        r = ((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2
        lum *= 1 - 0.06 * r
        _paper = (PAPER[None, None, :] * lum[..., None]).astype(f32)
    return _paper


def tfield():
    global _tfield
    if _tfield is None:
        _tfield = radial_field(H, W, W / 2, H / 2, 777, 0.55)
    return _tfield


class Renderer:
    def __init__(self, tl):
        self.tl = tl
        self.segs = tl["segments"]
        self.cache = {}
        self.ov = Overlay(tl)

    def scene(self, i):
        if i not in self.cache:
            sg = self.segs[i]
            # 只保留最近用到的場景，省記憶體
            for k in list(self.cache):
                if abs(k - i) > 1:
                    del self.cache[k]
            self.cache[i] = SCENES[sg["id"]](sg["dur"], 1000 + i * 37, sg)
        return self.cache[i]

    def layer(self, i, T):
        sg = self.segs[i]
        lt = T - sg["start"]
        A, R = self.scene(i).render(lt)
        self.ov.tag(sg["id"], lt, A, R)
        return A, R

    def frame(self, T):
        segs = self.segs
        i = 0
        while i + 1 < len(segs) and T >= segs[i + 1]["start"]:
            i += 1
        A, R = None, None
        for j, other in ((i, i + 1), (i - 1, i)):
            if 0 <= j and other < len(segs):
                B = segs[other]["start"]
                if abs(T - B) < TR / 2:
                    p = (T - (B - TR / 2)) / TR
                    A0, R0 = self.layer(j, T)
                    A1, R1 = self.layer(other, T)
                    if p < 0.5:
                        k = 1 - smooth(p, 0.0, 0.5)
                        A, R = A0 * k, R0 * k
                    else:
                        k = smooth(p, 0.5, 1.0)
                        A, R = A1 * k, R1 * k
                    break
        if A is None:
            A, R = self.layer(i, T)
        self.ov.subtitle(T, A, R)
        P = paper()
        img = P * (1 - A[..., None]) + INK * A[..., None]
        img = img * (1 - R[..., None]) + RED * R[..., None]
        return (np.clip(img, 0, 1) * 255).astype(np.uint8)


# ═════════════════════════ 聲音 ═════════════════════════
def read_wav(path):
    with wave.open(path) as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(f32) / 32768
    return a, sr


def declick(a, sr):
    """把前後都安靜的孤立突波（TTS 開頭爆音）清掉。"""
    a = a.copy()
    fr = int(sr * 0.01)
    n = len(a) // fr
    pk = np.abs(a[:n * fr]).reshape(n, fr).max(axis=1)
    for i in range(n):
        prev = pk[i - 1] if i > 0 else 0
        nxt = pk[i + 1:i + 4].max() if i + 1 < n else 0
        if pk[i] > 0.15 and prev < 0.02 and nxt < 0.02:
            a[i * fr:(i + 1) * fr] = 0
    # 被安靜段隔開、又短又滿格的片段（TTS 結尾雜訊爆音）整段刪除
    loud = pk > 0.02
    i = 0
    while i < n:
        if loud[i]:
            j = i
            while j < n and loud[j]:
                j += 1
            gap_before = i == 0 or not loud[max(0, i - 10):i].any()
            gap_after = j >= n or not loud[j:j + 10].any()
            if gap_before and gap_after and (j - i) <= 40 and pk[i:j].max() > 0.9:
                a[i * fr:j * fr] = 0
            i = j
        else:
            i += 1
    a -= a.mean()
    return a


def fade_edges(x, sr, ms=6):
    m = min(len(x) // 2, int(sr * ms / 1000))
    if m > 1:
        r = np.linspace(0, 1, m, dtype=f32)
        x = x.copy()
        x[:m] *= r
        x[-m:] *= r[::-1]
    return x


def compress_pauses(a, sr, max_pause=0.32, keep_edge=0.06):
    a = declick(a, sr)
    fr = int(sr * 0.01)
    n = len(a) // fr
    rms = np.sqrt(np.mean(a[:n * fr].reshape(n, fr) ** 2, axis=1) + 1e-12)
    thr = rms.max() * 10 ** (-36 / 20)
    voiced = rms > thr
    idx = np.where(voiced)[0]
    if len(idx) == 0:
        return a
    s, e = max(0, idx[0] - int(keep_edge * 100)), min(n, idx[-1] + int(keep_edge * 100) + 1)
    out, i, maxf = [], s, int(max_pause * 100)
    while i < e:
        if not voiced[i]:
            j = i
            while j < e and not voiced[j]:
                j += 1
            L = j - i
            if L > maxf:
                h = maxf // 2
                out.append(fade_edges(a[i * fr:(i + h) * fr], sr)); out.append(fade_edges(a[(j - h) * fr:j * fr], sr))
            else:
                out.append(a[i * fr:j * fr])
            i = j
        else:
            j = i
            while j < e and voiced[j]:
                j += 1
            out.append(a[i * fr:j * fr]); i = j
    return fade_edges(np.concatenate(out), sr, 15)


def pauses(a, sr, min_len=0.1):
    fr = int(sr * 0.01)
    n = len(a) // fr
    rms = np.sqrt(np.mean(a[:n * fr].reshape(n, fr) ** 2, axis=1) + 1e-12)
    voiced = rms > rms.max() * 10 ** (-34 / 20)
    res, i = [], 0
    while i < n:
        if not voiced[i]:
            j = i
            while j < n and not voiced[j]:
                j += 1
            if (j - i) >= min_len * 100 and i > 0 and j < n:
                res.append((i + j) / 2 / 100)
            i = j
        else:
            i += 1
    return res


PUNCT = "，。、；：？！"


def clean_len(s):
    return len([c for c in s if c not in PUNCT + "「」——　 "])


def split_sub(text):
    parts = [p for p in re.split(r"(?<=[，。、；：？！])|(?<=——)", text) if p]
    chunks, cur = [], ""
    for p in parts:
        if cur and clean_len(cur + p) > 16:
            chunks.append(cur); cur = p
        else:
            cur += p
    if cur:
        chunks.append(cur)
    return chunks


def disp(s):
    s = s.strip()
    s = re.sub(r"[，。、；：——]+$", "", s)
    s = s.replace("——", "　").replace("，", "　").replace("、", "　").replace("；", "　")
    s = re.sub(r"　+([」』）])", r"\1", s)
    s = re.sub(r"([「『（])　+", r"\1", s)
    s = re.sub(r"　{2,}", "　", s)
    return s


def mood_of(sid):
    return {
        "title": dict(dens=0.35, lo=3, hi=9, sad=False, drum=0, drone=0.9),
        "s1": dict(dens=0.85, lo=4, hi=11, sad=False, drum=0, drone=0.8),
        "s2": dict(dens=0.4, lo=2, hi=8, sad=True, drum=0, drone=0.9),
        "s3": dict(dens=0.45, lo=1, hi=7, sad=True, drum=0, drone=1.2),
        "s4": dict(dens=0.8, lo=4, hi=11, sad=False, drum=0, drone=0.8),
        "s5": dict(dens=1.05, lo=4, hi=12, sad=False, drum=0.35, drone=0.9),
        "s6": dict(dens=1.25, lo=4, hi=12, sad=False, drum=1.0, drone=1.0),
        "s7": dict(dens=0.95, lo=3, hi=11, sad=False, drum=1.2, drone=1.2),
        "s8": dict(dens=0.85, lo=5, hi=12, sad=False, drum=0, drone=0.8),
        "s9": dict(dens=0.4, lo=3, hi=10, sad=True, drum=0, drone=0.7),
    }[sid]


def pluck(f, dur, amp, rng, sad=False):
    n = int(dur * SR)
    t = np.arange(n, dtype=f32) / SR
    freq = np.full(n, f, f32)
    if rng.random() < 0.3:  # 吟揉
        freq *= 1 + 0.007 * np.sin(2 * np.pi * 5.2 * t) * smooth(t, 0.25, 0.7)
    if rng.random() < 0.18:  # 滑音
        freq *= 2 ** ((-1.0 if sad else 1.0) * 2 / 12 * smooth(t, 0.35, 0.7))
    ph = 2 * np.pi * np.cumsum(freq) / SR
    y = np.zeros(n, f32)
    for k in range(1, 9):
        y += (1 / k ** 1.25) * np.exp(-t * (1.4 + 1.3 * k) * (0.7 if sad else 1.0)) * np.sin(k * ph + rng.random())
    y += 0.25 * np.exp(-t * 60) * np.sin(ph * 6.3)
    y *= np.minimum(1, t / 0.003)
    return y * amp


def drum(amp):
    n = int(1.0 * SR)
    t = np.arange(n, dtype=f32) / SR
    f = 42 + 38 * np.exp(-t * 18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t * 4.5) + 0.3 * np.sin(2 * np.pi * 170 * t) * np.exp(-t * 45)
    return y * amp


def make_music(tl, total):
    rng = np.random.default_rng(2026)
    N = int(total * SR) + SR * 2
    L, Rc = np.zeros(N, f32), np.zeros(N, f32)
    base = 146.83  # D3
    scale = [0, 2, 4, 7, 9]
    notes = [base * 2 ** ((12 * (i // 5) + scale[i % 5] - 12) / 12) for i in range(20)]

    def add(sig, t0, pan):
        i = int(t0 * SR)
        if i >= N:
            return
        s = sig[:N - i]
        L[i:i + len(s)] += s * math.cos(pan * math.pi / 2)
        Rc[i:i + len(s)] += s * math.sin(pan * math.pi / 2)

    segs = tl["segments"]
    for si, sg in enumerate(segs):
        m = mood_of(sg["id"])
        t0, t1 = sg["start"], sg["start"] + sg["dur"]
        if sg["id"] == "s9":
            t1 = total - 3
        idx = (m["lo"] + m["hi"]) // 2
        t = t0 + 0.2
        step = 0.5
        while t < t1:
            beat = round((t - t0) / step)
            p = m["dens"] * (0.75 if beat % 2 == 0 else 0.35)
            if rng.random() < p:
                idx = int(np.clip(idx + rng.choice([-2, -1, -1, 1, 1, 2, 0]), m["lo"], m["hi"]))
                if m["sad"] and rng.random() < 0.3:
                    idx = int(np.clip(idx - 1, m["lo"], m["hi"]))
                amp = 0.16 * (0.7 + 0.5 * rng.random())
                add(pluck(notes[idx], 3.5, amp, rng, m["sad"]), t + rng.normal() * 0.012, 0.3 + 0.4 * rng.random())
                if beat % 8 == 0 and rng.random() < 0.5:
                    add(pluck(notes[max(0, idx - 5)], 3.5, amp * 0.6, rng, m["sad"]), t + 0.02, 0.5)
            t += step
        if m["drum"]:
            t = t0 + 0.5
            pat = [1, 0, 0, 0.6, 1, 0, 0.5, 0]
            k = 0
            while t < t1 - 0.5:
                v = pat[k % 8]
                ramp = smooth(t, t0, t0 + 3) * (smooth(t, t0 + sg["dur"] * 0.55, t1) if m["drum"] < 0.5 else 1)
                if v:
                    add(drum(0.5 * m["drum"] * v * ramp), t, 0.5)
                t += 0.5; k += 1
    # 低沉長音
    t = np.arange(N, dtype=f32) / SR
    lvl = np.zeros(N, f32)
    for sg in segs:
        m = mood_of(sg["id"])
        a, b = int(sg["start"] * SR), int((sg["start"] + sg["dur"]) * SR)
        lvl[a:b] = m["drone"]
    lvl = gaussian_filter(lvl[::441], 300)  # 平滑轉換
    lvl = np.interp(np.arange(N), np.arange(len(lvl)) * 441, lvl).astype(f32)
    d1 = 73.42
    drone = (np.sin(2 * np.pi * d1 * t) + 0.35 * np.sin(2 * np.pi * 2 * d1 * t) + 0.5 * np.sin(2 * np.pi * 1.5 * d1 * t + 1)
             + 0.15 * np.sin(2 * np.pi * 3 * d1 * t)) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * t))
    drone *= 0.045 * lvl * smooth(t, 0, 3)
    L += drone; Rc += drone * 0.97
    # 殘響
    ir_t = np.arange(int(2.4 * SR), dtype=f32) / SR
    rng2 = np.random.default_rng(5)
    for ch in (L, Rc):
        ir = gaussian_filter(rng2.normal(size=len(ir_t)).astype(f32), 2) * np.exp(-ir_t * 2.6)
        ir /= np.sqrt(np.sum(ir ** 2))
        wet = fftconvolve(ch, ir)[:N].astype(f32)
        ch += 0.35 * wet
    fade = smooth(t, 0, 1.5) * (1 - smooth(t, total - 3.5, total))
    return L * fade, Rc * fade


def do_audio():
    os.makedirs(WORK, exist_ok=True)
    segs = [{"id": "title", "start": 0.0, "dur": TITLE_DUR}]
    lines, subs = [], []
    T = TITLE_DUR
    voice_parts = []
    for sc in script["scenes"]:
        start = T
        cur = T + LEAD
        for i, text in enumerate(sc["lines"]):
            a, sr = read_wav(os.path.join(HERE, "tts", f"{sc['id']}_{i}.wav"))
            a = compress_pauses(a, sr)
            rms = np.sqrt(np.mean(a ** 2))
            a = a * float(np.clip(0.09 / max(rms, 1e-4), 0.6, 2.0))
            a = np.tanh(a * 1.2) / 1.2  # 柔性限幅，避免削波刺耳
            a44 = resample_poly(a, SR, sr).astype(f32)
            dur = len(a44) / SR
            voice_parts.append((cur, a44))
            lines.append({"scene": sc["id"], "start": cur, "dur": dur, "text": text})
            chunks = split_sub(text)
            ps = pauses(a44, SR)
            tot = sum(clean_len(c) for c in chunks)
            bounds, acc = [0.0], 0
            for c in chunks[:-1]:
                acc += clean_len(c)
                target = dur * acc / tot
                cand = [p for p in ps if p > bounds[-1] + 0.4]
                best = min(cand, key=lambda p: abs(p - target)) if cand else None
                bounds.append(best if best is not None and abs(best - target) < 0.9 else target)
            bounds.append(dur)
            for k, c in enumerate(chunks):
                subs.append({"start": cur + bounds[k], "end": cur + bounds[k + 1] + (0.25 if k == len(chunks) - 1 else 0),
                             "text": disp(c)})
            cur += dur + GAP
        end = cur - GAP + TAIL
        info = {"id": sc["id"], "start": start, "dur": end - start}
        if sc["id"] == "s9":
            info["end_at"] = end - start - 0.3
            info["dur"] = end - start + END_HOLD
        elif sc["id"] == "s3":
            info["dur"] = end - start + 2.5
        segs.append(info)
        T = start + info["dur"]
    total = T
    for i in range(len(subs) - 1):  # 字幕不重疊
        subs[i]["end"] = min(subs[i]["end"], subs[i + 1]["start"] - 0.05)
    N = int(total * SR) + SR * 2
    voice = np.zeros(N, f32)
    for t0, a in voice_parts:
        i = int(t0 * SR); voice[i:i + len(a)] += a
    voice *= 0.89 / np.abs(voice).max()
    # 旁白出現時壓低配樂
    hop = SR // 100
    nh = N // hop
    env = np.sqrt(np.mean(voice[:nh * hop].reshape(nh, hop) ** 2, axis=1))
    act = gaussian_filter((env > 0.02).astype(f32), 15)
    act = np.clip(act * 1.6, 0, 1)
    duck = 1 - 0.62 * np.interp(np.arange(N), np.arange(nh) * hop + hop / 2, act).astype(f32)
    L, Rm = make_music({"segments": segs}, total)
    mus_peak = max(np.abs(L).max(), np.abs(Rm).max())
    L, Rm = L / mus_peak * 0.42 * duck, Rm / mus_peak * 0.42 * duck
    mix = np.stack([voice + L, voice + Rm], 1)
    mix *= 0.95 / np.abs(mix).max()
    n = int(total * SR)
    with wave.open(os.path.join(WORK, "mix.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix[:n] * 32767).astype(np.int16).tobytes())
    tl = {"segments": segs, "lines": lines, "subs": subs, "total": total}
    json.dump(tl, open(os.path.join(WORK, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"總長 {total:.1f}s，旁白 {len(lines)} 句，字幕 {len(subs)} 段")
    for s in segs:
        print(f"  {s['id']:6s} {s['start']:7.2f}  {s['dur']:6.2f}s")


# ═════════════════════════ 輸出 ═════════════════════════
def load_tl():
    return json.load(open(os.path.join(WORK, "timeline.json"), encoding="utf-8"))


def do_stills(which=None):
    tl = load_tl()
    rd = Renderer(tl)
    os.makedirs(os.path.join(WORK, "stills"), exist_ok=True)
    for i, sg in enumerate(tl["segments"]):
        if which and sg["id"] not in which:
            continue
        if sg["id"] == "s3":
            fracs = (0.22, 0.30, 0.55, 0.82)
        elif sg["id"] == "s1":
            fracs = (0.30, 0.52, 0.55, 0.58, 0.82)
        else:
            fracs = (0.30, 0.55, 0.82)
        for fr in fracs:
            T = sg["start"] + sg["dur"] * fr
            img = rd.frame(T)
            Image.fromarray(img).save(os.path.join(WORK, "stills", f"{i:02d}_{sg['id']}_{int(fr*100)}.jpg"), quality=88)
            print("still", sg["id"], fr, flush=True)
    # 轉場
    B = tl["segments"][3]["start"]
    Image.fromarray(rd.frame(B)).save(os.path.join(WORK, "stills", "trans.jpg"), quality=88)


def render_block(args):
    k, f0, f1 = args
    tl = load_tl()
    rd = Renderer(tl)
    path = os.path.join(WORK, f"part{k:02d}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast",
                          "-crf", "12", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(rd.frame(f / FPS).tobytes())
    p.stdin.close(); p.wait()
    return path


def do_video(draft=False):
    from multiprocessing import Pool
    tl = load_tl()
    nf = int(tl["total"] * FPS)
    nb = 8
    edges = np.linspace(0, nf, nb + 1).astype(int)
    jobs = [(k, edges[k], edges[k + 1]) for k in range(nb)]
    with Pool(min(nb, os.cpu_count() or 4)) as pool:
        parts = pool.map(render_block, jobs)
    lst = os.path.join(WORK, "parts.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    inter = os.path.join(WORK, "video_hq.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", inter], check=True)
    if draft:
        encode_draft()
    else:
        encode_final(tl["total"])


def encode_draft():
    """初版：單次快速壓縮，不做兩階段位元率控制。"""
    os.makedirs(OUTDIR, exist_ok=True)
    inter = os.path.join(WORK, "video_hq.mp4")
    mix = os.path.join(WORK, "mix.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", inter, "-i", mix, "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "128k",
                    "-shortest", "-movflags", "+faststart", OUTFILE], check=True)
    print(f"初版輸出 {OUTFILE}  {os.path.getsize(OUTFILE)/1024/1024:.2f} MB")


def encode_final(total, target_mb=19.2):
    os.makedirs(OUTDIR, exist_ok=True)
    inter = os.path.join(WORK, "video_hq.mp4")
    mix = os.path.join(WORK, "mix.wav")
    abr = 128
    vbr = int(min(4000, target_mb * 8 * 1024 / total - abr - 20))
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{vbr}k", "-pix_fmt", "yuv420p", "-tune", "animation"]
    passlog = os.path.join(WORK, "x264pass")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", inter] + common +
                   ["-pass", "1", "-passlogfile", passlog, "-an", "-f", "mp4", "NUL"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", inter, "-i", mix] + common +
                   ["-pass", "2", "-passlogfile", passlog, "-c:a", "aac", "-b:a", f"{abr}k", "-shortest",
                    "-movflags", "+faststart", OUTFILE], check=True)
    print(f"輸出 {OUTFILE}  {os.path.getsize(OUTFILE)/1024/1024:.2f} MB（影像 {vbr} kbps）")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "audio":
        do_audio()
    elif cmd == "stills":
        do_stills(sys.argv[2:] or None)
    elif cmd == "video":
        do_video()
    elif cmd == "draft":
        do_video(draft=True)
    elif cmd == "encode":
        encode_final(load_tl()["total"])
    else:
        print(__doc__)
