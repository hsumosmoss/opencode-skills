#!/usr/bin/env python3
"""音效合成器（示範生成式 SFX 的能力邊界）
用法: python generate_sfx.py --kind hum|beep|chime|click|rain|water [--seconds N] [--out f.wav]
只用 Python 標準庫，輸出 44.1kHz 單聲道 WAV（再用 ffmpeg 轉 mp3）
"""
import argparse, math, random, struct, wave

SR = 44100


def lowpass(buf, cutoff):
    a = 1 - math.exp(-2 * math.pi * cutoff / SR)
    out, y = [], 0.0
    for x in buf:
        y += a * (x - y)
        out.append(y)
    return out


def highpass(buf, cutoff):
    lp = lowpass(buf, cutoff)
    return [x - y for x, y in zip(buf, lp)]


def add(dst, src, at):
    for i, v in enumerate(src):
        j = at + i
        if 0 <= j < len(dst):
            dst[j] += v


def env_exp(n, tau):
    return [math.exp(-i / (tau * SR)) for i in range(n)]


def hum(seconds):
    """螢光燈管嗡聲：100Hz 基音 + 諧波 + 微弱雜訊（工頻哼聲）"""
    n = int(seconds * SR)
    rng = random.Random(1)
    buf = []
    for i in range(n):
        t = i / SR
        v = (math.sin(2 * math.pi * 100 * t)
             + 0.45 * math.sin(2 * math.pi * 200 * t + 0.7)
             + 0.22 * math.sin(2 * math.pi * 300 * t)
             + 0.10 * math.sin(2 * math.pi * 400 * t))
        # 微弱 50Hz 拍頻讓聲音不呆板
        v *= 1.0 + 0.06 * math.sin(2 * math.pi * 0.7 * t)
        v += 0.05 * rng.uniform(-1, 1)
        buf.append(v * 0.12)
    return buf


def beep(seconds):
    """掃描器嗶聲：兩聲方波感純音（帶輕微 FM 讓它像壓電蜂鳴器）"""
    n = int(seconds * SR)
    buf = [0.0] * n

    def one(at_ms, f, dur):
        m = int(dur * SR)
        seg = []
        for i in range(m):
            t = i / SR
            v = (math.sin(2 * math.pi * f * t)
                 + 0.3 * math.sin(2 * math.pi * f * 2.01 * t))
            # 快起快收
            e = min(1.0, i / (0.004 * SR)) if i < 0.004 * SR else 1.0
            e *= min(1.0, (m - i) / (0.01 * SR))
            seg.append(v * e * 0.5)
        add(buf, seg, int(at_ms * SR))

    one(0, 1150, 0.10)
    one(0.16, 1150, 0.10)
    one(0.40, 1720, 0.14)   # 成功確認音
    return buf[:n]


def chime(seconds):
    """門鈴叮咚：雙音，鐘體用非諧波泛音 + 指數衰減"""
    n = int(seconds * SR)
    buf = [0.0] * n

    def strike(at_s, f, gain, tau):
        m = int(min(2.5, seconds - at_s) * SR)
        if m <= 0:
            return
        seg = []
        partials = [(1.0, 1.0), (2.76, 0.35), (5.40, 0.14), (8.93, 0.05)]
        for i in range(m):
            t = i / SR
            v = sum(a * math.sin(2 * math.pi * f * r * t)
                    for r, a in partials)
            seg.append(v * math.exp(-t / tau) * gain * 0.3)
        add(buf, seg, int(at_s * SR))

    strike(0.0, 659.3, 1.0, 0.9)      # ding (E5)
    strike(0.35, 523.3, 0.9, 1.2)     # dong (C5)
    return buf


def click(seconds):
    """打火機喀噠：摩擦短脈衝 + 金屬簧片共振"""
    n = int(seconds * SR)
    rng = random.Random(3)
    buf = [0.0] * n
    # 第一聲：摩擦/按壓
    m = int(0.02 * SR)
    for i in range(m):
        t = i / SR
        v = rng.uniform(-1, 1) * math.exp(-t / 0.004)
        buf[i] += v * 0.7
    # 第二聲（+90ms）：簧片撞擊金屬，帶共振
    at = int(0.09 * SR)
    m = int(0.12 * SR)
    for i in range(m):
        t = i / SR
        v = (math.sin(2 * math.pi * 3100 * t) * 0.6
             + math.sin(2 * math.pi * 4700 * t) * 0.3
             + rng.uniform(-1, 1) * 0.4)
        buf[at + i] += v * math.exp(-t / 0.02) * 0.6
    return buf


def rain(seconds):
    """雨聲：濾波噪聲底 + 隨機水滴高頻點綴（示範：能像但細節偏假）"""
    n = int(seconds * SR)
    rng = random.Random(5)
    buf = [rng.uniform(-1, 1) for _ in range(n)]
    buf = highpass(lowpass(buf, 5500), 400)
    buf = [v * 0.35 for v in buf]
    # 水滴打在表面的高頻點
    for _ in range(int(seconds * 26)):
        at = rng.randint(0, n - int(0.01 * SR))
        m = int(0.012 * SR)
        f = rng.uniform(2500, 6000)
        for i in range(m):
            t = i / SR
            buf[at + i] += (math.sin(2 * math.pi * f * t)
                            * math.exp(-t / 0.003) * rng.uniform(0.05, 0.16))
    return buf


def water(seconds):
    """倒水進杯：水柱噪聲 + 氣泡 + 音高隨水位上升（誠實示範：困難組）"""
    n = int(seconds * SR)
    rng = random.Random(7)
    raw = [rng.uniform(-1, 1) for _ in range(n)]
    # 水柱：帶通噪聲，中心頻率隨水位（時間）上升
    buf = [0.0] * n
    lp = [0.0] * n
    y = 0.0
    for i in range(n):
        p = i / n
        fc = 700 + 1800 * p
        a = 1 - math.exp(-2 * math.pi * fc / SR)
        y += a * (raw[i] - y)
        lp[i] = y
    hp = highpass(lp, 350)
    for i in range(n):
        p = i / n
        gain = min(1.0, p / 0.08) * (1.0 if p < 0.92 else (1 - p) / 0.08)
        buf[i] = hp[i] * gain * 0.55
    # 氣泡聲：隨機短音，音高隨水位上升
    for _ in range(int(seconds * 14)):
        p = rng.uniform(0.05, 0.95)
        at = int(p * n)
        f = rng.uniform(400, 700) * (1 + 1.2 * p)
        m = int(0.05 * SR)
        for i in range(m):
            t = i / SR
            if at + i < n:
                buf[at + i] += (math.sin(2 * math.pi * f * t)
                                * math.exp(-t / 0.015) * rng.uniform(0.1, 0.3))
    return buf


KINDS = {"hum": hum, "beep": beep, "chime": chime, "click": click,
         "rain": rain, "water": water}
DEFAULT_SEC = {"hum": 6, "beep": 1, "chime": 2, "click": 0.4,
               "rain": 4, "water": 3}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--kind", required=True, choices=sorted(KINDS))
    p.add_argument("--seconds", type=float, default=None)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default="sfx.wav")
    a = p.parse_args()
    sec = a.seconds or DEFAULT_SEC[a.kind]
    buf = KINDS[a.kind](sec)
    # 峰值正規化到 0.8
    peak = max(abs(v) for v in buf) or 1.0
    k = 0.8 / peak
    with wave.open(a.out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(v * k * 32767))
                               for v in buf))
    print(f"written: {a.out} ({sec}s, kind={a.kind})")
