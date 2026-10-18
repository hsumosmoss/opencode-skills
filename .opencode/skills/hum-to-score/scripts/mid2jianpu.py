#!/usr/bin/env python3
"""MIDI → 簡譜（反向轉換）：讓哼唱抽取的結果可以「看成簡譜、手改、傳回重生成」
用法: python mid2jianpu.py --in song.mid [--bpm 100] [--meter 4] [--key auto]
輸出: 簡譜文字（可直接餵回 jianpu2midi.py）

流程: MIDI 音符 → 調性自動偵測 → 首調唱名化 → 時值量化 → 記譜字串
無法精確記譜的音（非調內半音）→ 就近吸附到音階，並在報告中列出
"""
import argparse
from collections import Counter

import pretty_midi

# 大調調內半音（相對主音）
MAJOR_PCS = [0, 2, 4, 5, 7, 9, 11]
PC_TO_DEGREE = {0: 1, 2: 2, 4: 3, 5: 4, 7: 5, 9: 6, 11: 7}
PC_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def detect_key(pitches):
    """自動偵測最適合的大調（調內音最多、主音有強調）"""
    pc_count = Counter(p % 12 for p in pitches)
    best, best_score = 0, -1
    for tonic in range(12):
        on = sum(pc_count.get((tonic + d) % 12, 0) for d in MAJOR_PCS)
        # 調內音比例為主，主音出現次數做次要加分
        score = on + 0.5 * pc_count.get(tonic, 0)
        if score > best_score:
            best, best_score = tonic, score
    return best


def dur_to_jianpu(beats):
    """拍數 → 記譜字串（附點 .、增時線 -、減時線 _）"""
    if beats <= 0:
        return ""
    if beats < 1:                      # 0.5 -> _  0.25 -> __
        import math
        return "_" * max(1, round(-math.log2(beats)))
    whole = int(round(beats))
    frac = beats - whole
    if abs(frac - 0.5) < 0.01:         # 1.5 -> .   2.5 -> .-  3.5 -> .--
        return "." + "-" * (whole - 1) if whole >= 1 else "."
    return "-" * max(0, whole - 1)     # 2 -> -  3 -> --


def midi_to_jianpu(midi_path, bpm=None, meter=4, key="auto", grid=0.5):
    pm = pretty_midi.PrettyMIDI(midi_path)
    if not pm.instruments or not pm.instruments[0].notes:
        raise SystemExit("MIDI 內沒有音符")
    notes = sorted(pm.instruments[0].notes, key=lambda n: n.start)

    if bpm is None:
        tempos, _ = pm.get_tempo_changes()
        cand = float(tempos[0]) if len(tempos) else 0.0
        if not (20 <= cand <= 300):
            # pretty_midi 寫出的檔案 get_tempo_changes 可能回 [0.] → 改用估測
            cand = float(pm.estimate_tempo())
        bpm = cand if (20 <= cand <= 300) else 100.0
    beat = 60.0 / bpm

    pitches = [n.pitch for n in notes]
    tonic = detect_key(pitches) if key == "auto" else PC_NAMES.index(key)

    # 基準八度：把主音放在最接近 C4(60) 的八度，唱名 1 對齊它
    tonic_base = tonic + 12 * round((60 - tonic) / 12)

    tokens, report = [], {"snapped": [], "rests": 0}
    cursor = 0.0                        # 進度（拍）
    for n in notes:
        start_beat, end_beat = n.start / beat, n.end / beat
        # --- 空隙 → 休止（>0.3 拍才記）---
        gap = start_beat - cursor
        if gap > 0.3:
            g = round(gap / grid) * grid
            report["rests"] += 1
            tokens.append(_rest(g))
            cursor += g
        # --- 時值量化 ---
        dur = max(grid, round((end_beat - start_beat) / grid) * grid)
        # --- 音高 → 首調唱名 ---
        rel = n.pitch - tonic_base
        pc = rel % 12
        if pc not in PC_TO_DEGREE:
            # 非調內音：吸附到最近調內音
            best = min(MAJOR_PCS, key=lambda d: min(abs(pc - d), 12 - abs(pc - d)))
            report["snapped"].append(
                f"{n.start:.1f}s {PC_NAMES[n.pitch % 12]}->{PC_NAMES[(tonic + best) % 12]}")
            rel += best - pc
            pc = best
        deg = PC_TO_DEGREE[pc]
        octave = rel // 12
        mark = "'" * octave if octave > 0 else "," * (-octave)
        tokens.append(f"{deg}{mark}{dur_to_jianpu(dur)}")
        cursor = start_beat + dur

    # --- 排版：每 meter 拍加小節線 ---
    lines, line, beats_in_line = [], [], 0
    beat_cost = {"_": 0.5, ".": 1.5, "": 1.0}
    for tk in tokens:
        cost = 1.0 + tk.count("-") + 0.5 * tk.count("_") + (0.5 if "." in tk else 0)
        if beats_in_line + cost > meter + 0.01:
            lines.append(" ".join(line) + " |")
            line, beats_in_line = [], 0
        line.append(tk)
        beats_in_line += cost
    if line:
        lines.append(" ".join(line) + " |")

    header = (f"# 1={PC_NAMES[tonic]}  bpm={bpm:.0f}  拍號={meter}/4  "
              f"(自動偵測; {len(notes)} 音符)")
    if report["snapped"]:
        header += f"\n# 非調內音已吸附 {len(report['snapped'])} 處: " + \
                  "; ".join(report["snapped"][:8])
    return header + "\n" + "\n".join(lines) + "\n"


def _rest(beats):
    import math
    if beats < 1:
        return "0" + "_" * max(1, round(-math.log2(beats)))
    return "0" + "-" * max(0, int(round(beats)) - 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", default=None, help="預設: 同名 .txt")
    ap.add_argument("--bpm", type=float, default=None)
    ap.add_argument("--meter", type=int, default=4, help="每小節拍數（4=4/4）")
    ap.add_argument("--key", default="auto", help="auto 或主音如 C/G/Am 的 A")
    a = ap.parse_args()
    out = a.out or a.src.rsplit(".", 1)[0] + ".jianpu.txt"
    txt = midi_to_jianpu(a.src, bpm=a.bpm, meter=a.meter, key=a.key)
    with open(out, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"written: {out}")
    print(txt)
