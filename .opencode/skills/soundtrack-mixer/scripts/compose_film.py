#!/usr/bin/env python3
"""影片配樂作曲（作曲層）：用 pretty_midi 描述「音樂走向」，輸出 .mid
再由 FluidSynth + SoundFont 發聲（發聲層），完全不用寫振盪器。

用法: python compose_film.py [--out film.mid] [--seed N]
對齊《便利店的最後一盞燈》50 秒時間軸:
  00:00-26   calm   治癒（雨夜開店）
  00:26-27.5 靜音   燈管熄滅死寂（不寫任何音符）
  00:27.5-50 tense  低音區、休止多（黑暗中的行動）

音樂走向的控制都在這個檔案：
  - 曲式: SECTIONS 定義段落邊界與情緒
  - 節奏: BPM、每拍休止率、音符時值
  - 和聲: PROGRESSION 和弦進行（小節制）
  - 轉折: switch_at 前後換音區/密度/音色
"""
import argparse
import pretty_midi

# ---------------- 曲式與走向（改這裡就是改音樂結構） ----------------
BPM = 66
TOTAL = 50.0
MUTE = (26.0, 27.5)          # 燈管熄滅：全靜音區
SWITCH_AT = 27.5             # 轉折點：calm -> tense

# 和弦進行（根音 MIDI 音高，每 4 拍一小節）——calm 用 maj9 色彩、tense 用低八度
PROGRESSION_CALM = [43, 45, 48]        # G2 A2 C3（偏低鋪底）
PROGRESSION_TENSE = [43, 40, 43]       # G2 E2 G2（更沉、半音階壓迫感）

# 五聲音階（C 大調五聲，跨 3 八度）——旋律只能用這些音，保證不難聽
SCALE = [48, 50, 52, 55, 57, 60, 62, 64, 67, 69, 72, 74, 76, 79, 81]

# 走向參數（前段/後段）
MOOD = {
    "calm":  dict(rest=0.45, lo=4, hi=11, vel=(48, 72), octave_up=0.22),
    "tense": dict(rest=0.62, lo=0, hi=7,  vel=(38, 60), octave_up=0.0),
}


def mood_at(t):
    return "tense" if t >= SWITCH_AT else "calm"


def in_mute(t):
    return MUTE[0] <= t < MUTE[1]


def compose(seed=42):
    import random
    rng = random.Random(seed)
    pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    beat = 60.0 / BPM
    bar = beat * 4

    piano = pretty_midi.Instrument(program=0, name="piano")   # GM: Acoustic Grand
    pad = pretty_midi.Instrument(program=89, name="warm pad")  # GM: Warm Pad

    # ---- 主旋律：每拍至多一音、常留空、避開靜音區 ----
    t = 0.0
    first_tense_done = False
    while t < TOTAL:
        m = MOOD[mood_at(t)]
        # 黑暗後的第一個音強制出現（轉折不能是空的）
        force = (mood_at(t) == "tense" and not first_tense_done)
        if not in_mute(t) and (force or rng.random() >= m["rest"]):
            first_tense_done = first_tense_done or force
            pitch = SCALE[rng.randint(m["lo"], m["hi"])]
            dur = rng.uniform(1.6, 3.2) * beat
            dur = min(dur, TOTAL - t)
            # 音符中途遇靜音區 => 截斷在 26.0
            if t < MUTE[0] < t + dur:
                dur = MUTE[0] - t
            vel = rng.randint(*m["vel"])
            if abs(t % bar) < 1e-6:
                vel = min(100, vel + 12)          # 小節頭重音
            if dur > 0.05:
                piano.notes.append(pretty_midi.Note(
                    velocity=vel, pitch=pitch, start=t, end=t + dur))
            # 毛毛感：偶爾疊高八度輕音
            if rng.random() < m["octave_up"] and pitch + 12 <= 96:
                piano.notes.append(pretty_midi.Note(
                    velocity=max(20, vel - 24), pitch=pitch + 12,
                    start=t + 0.09, end=t + min(dur, 1.6 * beat)))
        t += beat

    # ---- 墊底和聲：每小節一換，低音只在小節頭；靜音區整段跳過 ----
    prog_i = 0
    s = 0.0
    while s < TOTAL:
        mood = mood_at(s)
        root = (PROGRESSION_CALM if mood == "calm" else PROGRESSION_TENSE)[prog_i % 3]
        prog_i += 1
        # 和弦音：根音 + 五度 + 九度（calm）／根音 + 小三度（tense）
        chord = [root, root + 7, root + 14] if mood == "calm" else [root, root + 3, root + 10]
        seg_start, seg_end = s, min(s + bar * 1.2, TOTAL)
        if not in_mute(seg_start):
            # 若和弦跨入靜音區，截斷
            if seg_start < MUTE[0] < seg_end:
                seg_end = MUTE[0]
            for p in chord:
                pad.notes.append(pretty_midi.Note(
                    velocity=34 if mood == "calm" else 30,
                    pitch=p, start=seg_start, end=seg_end))
        s += bar

    # ---- 轉折點 27.5 強制補一個墊底和弦（小節對齊會留下 26~29 的空洞）----
    t_root = PROGRESSION_TENSE[0]
    pad.notes.append(pretty_midi.Note(
        velocity=32, pitch=t_root,
        start=SWITCH_AT, end=min(SWITCH_AT + bar * 1.2, TOTAL)))

    # ---- 片尾：47 秒後不再起新音，讓風鈴收尾（fade 由混音階段做）----
    pm.instruments += [piano, pad]
    return pm


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="film.mid")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    pm = compose(a.seed)
    pm.write(a.out)
    n = sum(len(i.notes) for i in pm.instruments)
    print(f"written: {a.out} ({n} notes, {len(pm.instruments)} tracks, "
          f"end={pm.get_end_time():.1f}s)")
