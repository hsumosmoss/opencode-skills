#!/usr/bin/env python3
"""簡譜 → MIDI 轉換器（作曲層的文字介面）
用法: python jianpu2midi.py --text "1 1 5 5 6 6 5 -" [--bpm 66] [--key 1=C]
      python jianpu2midi.py --file song.txt --out song.mid

簡譜記法（純文字版）:
  1 2 3 4 5 6 7   音階音（首調唱名 do re mi...），0 = 休止
  '               升一個八度（上加點），可疊加 1'' = 升兩個八度
  ,               降一個八度（下加點），可疊加
  _               減時線：時值減半（底線），可疊加 __ = 1/4
  -               增時線：+1 拍
  |               小節線（忽略，僅供閱讀）
  空格            分隔音符

預設: 一拍 = 四分音符, 1 = C4(do), 大調
"""
import argparse
import re
import sys

import pretty_midi

# 首調唱名 -> 大調音程（半音數）
MAJOR = [0, 2, 4, 5, 7, 9, 11]
# --key 1=G 之類：G 相對 C 的偏移
KEY_OFFSET = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

TOKEN = re.compile(r"^([0-7])([,']*)(\.?)(_*)(-*)$")


def parse(text):
    """簡譜文字 -> [(degree, octave_shift, dur_beats), ...]（含休止 dur>0）"""
    notes = []
    # 先按行/空格切；| 視為分隔
    text = text.replace("|", " ")
    for raw in text.split():
        if raw == "-" and notes:
            # "5 -"（有空格）的寫法：獨立增時線延續前一個音
            deg, oct_shift, dur = notes[-1]
            notes[-1] = (deg, oct_shift, dur + 1.0)
            continue
        m = TOKEN.match(raw)
        if not m:
            raise ValueError(f"無法解析的記號: {raw!r}")
        deg = int(m.group(1))
        oct_mark, dot, under, dash = m.group(2), m.group(3), m.group(4), m.group(5)
        oct_shift = oct_mark.count("'") - oct_mark.count(",")
        base = 1.5 if dot else 1.0            # 附點 5. = 1.5 拍
        dur = base * (0.5 ** len(under)) + len(dash) * 1.0  # 底線減半、橫線加一拍
        if deg == 0:
            notes.append((0, 0, dur))     # 休止
        else:
            notes.append((deg, oct_shift, dur))
    return notes


def to_midi(parsed, bpm=66, key="C", base_octave=4, velocity=(58, 84)):
    """解析結果 -> PrettyMIDI（單軌鋼琴）"""
    import random
    rng = random.Random(42)
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(program=0, name="piano")
    beat = 60.0 / bpm
    t = 0.0
    off = KEY_OFFSET[key.upper()]
    for deg, oct_shift, dur in parsed:
        if deg:  # 非休止
            pitch = (base_octave * 12 + 12) + MAJOR[deg - 1] + off + 12 * oct_shift
            if not 0 <= pitch <= 127:
                raise ValueError(f"音高超出 MIDI 範圍: {pitch}")
            # 尾音微收（0.92）讓音符間有呼吸，接近真人彈奏
            inst.notes.append(pretty_midi.Note(
                velocity=rng.randint(*velocity), pitch=pitch,
                start=t, end=t + dur * beat * 0.92))
        t += dur * beat
    pm.instruments.append(inst)
    pm._tick_scales  # 觸發內部建構
    return pm, t


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", help="簡譜字串，例: '1 1 5 5 6 6 5 -'")
    g.add_argument("--file", help="簡譜文字檔路徑")
    ap.add_argument("--bpm", type=float, default=None,
                    help="BPM；未指定時自動讀檔內 '# ... bpm=NN' header，都沒有才用 66")
    ap.add_argument("--key", default=None,
                    help="調號 1=?，例 C G D；未指定時自動讀 header '# 1=X'，都沒有才用 C")
    ap.add_argument("--out", default="song.mid")
    a = ap.parse_args()

    raw = a.text if a.text else open(a.file, encoding="utf-8").read()
    # header 解析：編輯器/mid2jianpu 輸出的 '# 1=D  bpm=170  拍號=4/4 ...'
    hdr_key = hdr_bpm = None
    for ln in raw.splitlines():
        s = ln.lstrip()
        if not s.startswith("#"):
            continue
        m = re.search(r"1\s*=\s*([A-Ga-g])[#b]?", s)
        if m and hdr_key is None:
            hdr_key = m.group(1).upper()
        m = re.search(r"bpm\s*=\s*([\d.]+)", s, re.I)
        if m and hdr_bpm is None:
            hdr_bpm = float(m.group(1))
    key = a.key or hdr_key or "C"
    bpm = a.bpm or hdr_bpm or 66.0
    if key not in KEY_OFFSET:
        raise SystemExit(f"不支援的調號 1={key}（支援 {'/'.join(KEY_OFFSET)}；"
                         f"升記號調請先轉成等價自然調）")
    # 跳過 # 註解行（header/報告）
    src = "\n".join(ln for ln in raw.splitlines() if not ln.lstrip().startswith("#"))
    parsed = parse(src)
    pm, total_sec = to_midi(parsed, bpm=bpm, key=key)
    pm.write(a.out)
    n = sum(len(i.notes) for i in pm.instruments)
    via = "參數" if (a.key or a.bpm) else ("header" if (hdr_key or hdr_bpm) else "預設")
    print(f"written: {a.out} | {n} 音符 | 總長 {total_sec:.1f} 秒 "
          f"| bpm={bpm:g} key=1={key}（{via}）")
