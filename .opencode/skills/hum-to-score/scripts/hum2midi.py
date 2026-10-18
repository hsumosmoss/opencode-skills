#!/usr/bin/env python3
"""哼唱旋律抽取（Hum → MIDI）：人聲錄音 → 音符 → .mid
管線: librosa.pyin 逐幀音高追蹤 → 合併成音符 → 音高對齊音階/半音 → pretty_midi

用法: python hum2midi.py --in hum.wav [--out out.mid] [--snap scale|chromatic]
                      [--min-dur 0.12] [--vibrato-filter]
不依賴 TensorFlow / 神經網路：pyin 是統計式演算法，CPU 即可跑
"""
import argparse

import numpy as np
import pretty_midi


def track_notes(path, fmin=75, fmax=650, min_dur=0.12):
    """錄音 → [(pitch, start, end, confidence)]"""
    import librosa
    # m4a/aac 等 libsndfile 不認的格式 → 先用 ffmpeg 轉 wav
    if not path.lower().endswith((".wav", ".flac", ".ogg")):
        import subprocess, tempfile, os
        tmp = os.path.join(tempfile.gettempdir(), "_hum2midi_conv.wav")
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path,
                            "-ar", "22050", "-ac", "1", tmp],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"ffmpeg 轉檔失敗: {r.stderr.strip()}")
        path = tmp
    y, sr = librosa.load(path, sr=22050, mono=True)
    # pyin: 逐幀 f0 + 有聲/無聲判定（voiced_flag）+ 信心分數
    f0, voiced, prob = librosa.pyin(
        y, fmin=fmin, fmax=fmax, sr=sr,
        frame_length=2048, hop_length=256)
    times = librosa.times_like(f0, sr=sr, hop_length=256)

    # 中值濾波（~104ms 窗）壓掉顫音/起音滑音的微抖，避免切音時在閾值邊緣震盪
    from scipy.ndimage import median_filter
    midi_all = librosa.hz_to_midi(np.where(np.isnan(f0), f0[~np.isnan(f0)].mean(), f0))
    voiced = voiced & ~np.isnan(f0)
    midi_smooth = median_filter(midi_all, size=9, mode="nearest")

    notes = []
    cur = []   # 目前音符的 (midi_pitch, time, prob)
    # 把連續「有聲、音高相近」的幀聚合成一個音符
    for i in range(len(f0)):
        if voiced[i]:
            midi = midi_smooth[i]
            if cur and abs(np.median([c[0] for c in cur]) - midi) > 0.75:
                # 音高跳了 >= 半音的 3/4 → 切音符
                _flush(cur, notes, min_dur)
                cur = []
            cur.append((midi, times[i], prob[i]))
        else:
            _flush(cur, notes, min_dur)
            cur = []
    _flush(cur, notes, min_dur)

    # 合併間隔 < 40ms 的相鄰同音（補哼唱中的小破綻）
    merged = []
    for n in notes:
        if merged and n[0] == merged[-1][0] and n[1] - merged[-1][2] < 0.04:
            merged[-1] = (merged[-1][0], merged[-1][1], n[2],
                          min(merged[-1][3], n[3]))
        else:
            merged.append(n)
    return merged


def _flush(cur, notes, min_dur):
    if not cur:
        return
    start, end = cur[0][1], cur[-1][1] + 0.023  # 末幀補一格 hop
    if end - start < min_dur:
        return
    pitch = float(np.median([c[0] for c in cur]))
    conf = float(np.mean([c[2] for c in cur]))
    # 去掉顫音造成的 ±0.3 之內微抖（取中位數已大半抵銷）
    notes.append((pitch, start, end, conf))


MAJOR = {0: 0, 2: 2, 4: 4, 5: 5, 7: 7, 9: 9, 11: 11}


def snap(pitch, mode, key_offset=0):
    """音高對齊：chromatic=就地取整半音；scale=吸附到大調五聲（更不容易聽出錯音）"""
    if mode == "chromatic":
        return int(round(pitch))
    # 大調音階吸附：找最近的音階音
    rel = (pitch - key_offset) % 12
    scale_pcs = [0, 2, 4, 5, 7, 9, 11]
    best = min(scale_pcs, key=lambda s: min(abs(rel - s), 12 - abs(rel - s)))
    return int(round(pitch - rel + best))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True, help="錄音檔 wav/mp3/m4a")
    ap.add_argument("--out", default="hum.mid")
    ap.add_argument("--snap", choices=["scale", "chromatic"], default="chromatic",
                    help="chromatic=保留原調半音取整(預設)；scale=吸附大調音階")
    ap.add_argument("--key", type=int, default=0, help="scale 模式：主音偏移半音 0-11")
    ap.add_argument("--min-dur", type=float, default=0.12, help="最短音符秒數")
    ap.add_argument("--bpm", type=float, default=0,
                    help=">0 時把音符起點量化到此 BPM 的節拍格線")
    a = ap.parse_args()

    raw = track_notes(a.src, min_dur=a.min_dur)
    if not raw:
        raise SystemExit("沒有追到旋律：確認檔案有人聲、音量不要太小")

    beat = 60.0 / a.bpm if a.bpm > 0 else 0
    pm = pretty_midi.PrettyMIDI(initial_tempo=a.bpm if a.bpm > 0 else 120)
    inst = pretty_midi.Instrument(program=0, name="hummed")
    snapped = []
    for pitch, st, en, conf in raw:
        p = snap(pitch, a.snap, a.key)
        if a.bpm > 0:  # 節拍量化：哼唱節奏對齊格線
            st = round(st / (beat / 2)) * (beat / 2)
            en = round(en / (beat / 2)) * (beat / 2)
        # 對齊後同音高、間隔<60ms 的碎片合併（顫音殘餘造成的斷裂）
        if snapped and snapped[-1][0] == p and st - snapped[-1][2] < 0.06:
            snapped[-1] = (p, snapped[-1][1], en, max(snapped[-1][3], conf))
        elif en - st >= 0.05:
            snapped.append((p, st, en, conf))
    for p, st, en, conf in snapped:
        if en - st >= 0.05 and 0 <= p <= 127:
            inst.notes.append(pretty_midi.Note(
                velocity=int(60 + 30 * conf), pitch=p, start=st, end=en))
    pm.instruments.append(inst)
    pm.write(a.out)

    pits = [n.pitch for n in inst.notes]
    print(f"written: {a.out} | {len(inst.notes)} 音符 | "
          f"{inst.notes[-1].end:.1f}s | 音域 {min(pits)}-{max(pits)} "
          f"| snap={a.snap}")
    print("旋律(唱名):", " ".join(str(n.pitch % 12) for n in inst.notes[:40]))
