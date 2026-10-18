#!/usr/bin/env python3
"""生成式配樂合成器：五聲音階毛毛鋼琴 + 暖長音墊底 + 簡易混響
用法: python generate_bgm.py [--seconds N] [--seed S] [--out file.wav]
       [--style calm|tense] [--style-b calm|tense] [--switch-at SEC]
       [--mute START:DUR]
例:   對齊影片 26-27.5 靜音、27.5 後轉懸疑:
       python generate_bgm.py --seconds 50 --style calm --style-b tense \
         --switch-at 27.5 --mute 26:1.5 --out film.wav
只用 Python 標準庫，輸出 44.1kHz 立體聲 WAV（再用 ffmpeg 轉 mp3）
"""
import argparse, math, random, struct, wave

SR = 44100

# 五聲音階（C 大調五聲：C D E G A），跨 3 個八度
def pentatonic():
    base = [261.63, 293.66, 329.63, 392.00, 440.00]  # C4 D4 E4 G4 A4
    out = []
    for octv in (-1, 0, 1):
        out += [f * (2 ** octv) for f in base]
    return out

def piano(freq, dur, sr=SR, amp=0.5):
    """毛毛鋼琴：正弦基音 + 輕八度 + 輕五度泛音，快起慢收包絡"""
    n = int(dur * sr)
    buf = [0.0] * n
    atk = int(0.008 * sr)          # 快起 8ms
    # 快起慢收：attack 後指數衰減
    decay = math.exp(-3.0 / (dur * sr))
    for i in range(n):
        if i < atk:
            env = i / atk
        else:
            env = decay ** (i - atk)
        t = i / sr
        v = math.sin(2 * math.pi * freq * t)                 # 基音
        v += 0.32 * math.sin(2 * math.pi * freq * 2 * t)     # 輕八度（亮度）
        v += 0.10 * math.sin(2 * math.pi * freq * 3 * t)     # 輕五度泛音
        buf[i] = v * env * amp
    return buf

def pad(freqs, dur, sr=SR, amp=0.16):
    """暖長音墊底：多音正弦 + 慢起慢收 + 輕微顫音"""
    n = int(dur * sr)
    buf = [0.0] * n
    atk = int(min(1.5, dur * 0.3) * sr)
    rls = int(min(2.0, dur * 0.35) * sr)
    for i in range(n):
        t = i / sr
        if i < atk: env = i / atk
        elif i > n - rls: env = (n - i) / rls
        else: env = 1.0
        # 顫音讓長音不呆板（慢速 LFO，非鋸齒）
        vib = 1.0 + 0.0015 * math.sin(2 * math.pi * 0.18 * t)
        v = 0.0
        for k, f in enumerate(freqs):
            v += math.sin(2 * math.pi * f * vib * t) / len(freqs)
        buf[i] = v * env * amp
    return buf

def reverb(buf, sr=SR, mix=0.28):
    """卷積式長混響的輕量替代：多組延遲回授，代替 echos"""
    delays = [(int(0.043 * sr), 0.34), (int(0.071 * sr), 0.26),
              (int(0.113 * sr), 0.20), (int(0.157 * sr), 0.14)]
    out = buf[:]
    for d, g in delays:
        for i in range(d, len(buf)):
            out[i] += g * buf[i - d] * math.exp(-i / (len(buf) * 1.6))
    return [x * (1 - mix) + y * mix / 1.0 for x, y in zip(buf, out)]

def add(dst, src, at):
    """把 src 疊到 dst 的 at 采樣位置（超出長度則截斷）"""
    for i, v in enumerate(src):
        j = at + i
        if 0 <= j < len(dst):
            dst[j] += v

def generate(seconds, seed, style, style_b=None, switch_at=None, mute=None):
    rng = random.Random(seed)
    n = int(seconds * SR)
    L = [0.0] * n
    R = [0.0] * n

    scale = pentatonic()
    bpm = {"calm": 66, "tense": 58}[style]
    beat = 60.0 / bpm
    beats = int(seconds / beat)

    def style_at(t):
        """t 秒時生效的風格（支援前後段切換）"""
        if style_b and switch_at is not None and t >= switch_at:
            return style_b
        return style

    # ---- 主旋律：每拍至多一音，常留空（35~55% 機率休止）----
    for b in range(beats):
        st = style_at(b * beat)
        rest_p = {"calm": 0.45, "tense": 0.55}[st]
        low_limit = 6 if st == "tense" else 4   # tense 偏低音區
        if rng.random() < rest_p:
            continue
        idx = rng.randint(low_limit, len(scale) - 1)
        freq = scale[idx]
        dur = rng.uniform(1.6, 3.2)
        amp = rng.uniform(0.22, 0.34) * (1.0 if b % 4 == 0 else 0.72)
        note = piano(freq, dur, amp=amp)
        at = int(b * beat * SR)
        pan = rng.uniform(0.35, 0.65)          # 輕微左右分布
        add(L, [v * (1 - pan) for v in note], at)
        add(R, [v * pan for v in note], at)
        # 偶爾疊一個高八度輕音（毛毛感），間隔才疊
        if rng.random() < 0.22:
            hi = piano(freq * 2, dur * 0.6, amp=amp * 0.3)
            add(L, [v * (1 - pan) for v in hi], at + int(0.09 * SR))
            add(R, [v * pan for v in hi], at + int(0.09 * SR))

    # ---- 暖長音墊底：每 4 拍換一次和聲（根音 + 五度），低音只在小節頭 ----
    roots = [scale[3], scale[4], scale[5]]     # G3 A3 C4 區域
    bar = int(beat * 4 * SR)
    for s in range(0, n, bar):
        st = style_at(s / SR)
        f = roots[(s // bar) % len(roots)]
        if st == "tense":
            f *= 0.5                            # tense 墊更低
        seg = pad([f, f * 1.5, f * 2], min(bar * 1.2 / SR, (n - s) / SR))
        add(L, seg, s)
        add(R, seg, s)

    # ---- 分離左右聲道各自混響 ----
    L = reverb(L); R = reverb(R)

    # ---- 指定時點靜音（對齊影片 cue，如熄燈死寂）：前後各 80ms 防爆音 ----
    if mute:
        st, dur = mute
        i0, i1 = int(st * SR), int(min(st + dur, seconds) * SR)
        ramp = int(0.08 * SR)
        for i in range(ramp):
            g = i / ramp
            if i0 - i + ramp >= 0:
                L[i0 - i + ramp - 1] *= g; R[i0 - i + ramp - 1] *= g
        for i in range(ramp):
            g = i / ramp
            if i0 + i < n: L[i0 + i] *= g; R[i0 + i] *= g
        for i in range(i0, i1):
            L[i] = 0.0; R[i] = 0.0
        for i in range(ramp):
            g = i / ramp
            if i1 + i < n: L[i1 + i] *= g; R[i1 + i] *= g

    # ---- 淡入 1.5s / 淡出 3s ----
    fi, fo = int(1.5 * SR), int(3 * SR)
    for i in range(fi):
        g = i / fi; L[i] *= g; R[i] *= g
    for i in range(fo):
        g = i / fo; L[n - 1 - i] *= g; R[n - 1 - i] *= g

    # ---- 峰值正規化到 0.7（留 headroom，避免爆音）----
    peak = max(max(abs(x) for x in L), max(abs(x) for x in R)) or 1.0
    k = 0.7 / peak
    return [(x * k, y * k) for x, y in zip(L, R)]

def write_wav(path, frames):
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<hh", int(l * 32767), int(r * 32767))
                               for l, r in frames))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seconds", type=float, default=30)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--style", choices=["calm", "tense"], default="calm")
    p.add_argument("--style-b", dest="style_b", choices=["calm", "tense"],
                   default=None, help="切換後的風格（需搭配 --switch-at）")
    p.add_argument("--switch-at", dest="switch_at", type=float, default=None,
                   help="風格切換時間點（秒）")
    p.add_argument("--mute", default=None,
                   help="指定時點靜音，格式 START:DUR（秒），例 26:1.5")
    p.add_argument("--out", default="bgm_generated.wav")
    a = p.parse_args()
    mute = None
    if a.mute:
        st, dr = a.mute.split(":")
        mute = (float(st), float(dr))
    write_wav(a.out, generate(a.seconds, a.seed, a.style,
                              a.style_b, a.switch_at, mute))
    print(f"written: {a.out} ({a.seconds}s, seed={a.seed}, style={a.style}"
          + (f"->{a.style_b}@{a.switch_at}" if a.style_b else "")
          + (f", mute={a.mute}" if a.mute else "") + ")")
