#!/usr/bin/env python3
"""檢查 timeline.json 與 mix.wav 是否對得上，並看片尾留白。

用法：
  python check_timeline.py --project C:\\...\\my-film
  python check_timeline.py --timeline ...\\work\\timeline.json --mix ...\\work\\mix.wav
"""
import argparse
import json
import os
import sys
import wave


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def wav_duration(path):
    with wave.open(path) as w:
        return w.getnframes() / float(w.getframerate())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", help="專案根目錄（含 scripts/work）")
    ap.add_argument("--timeline")
    ap.add_argument("--mix")
    ap.add_argument("--min-tail", type=float, default=2.0,
                    help="最後字幕後至少留幾秒（預設 2.0）")
    args = ap.parse_args()

    if args.project:
        base = os.path.join(args.project, "scripts", "work")
        timeline = args.timeline or os.path.join(base, "timeline.json")
        mix = args.mix or os.path.join(base, "mix.wav")
    else:
        timeline = args.timeline
        mix = args.mix

    if not timeline or not os.path.exists(timeline):
        sys.exit(f"找不到 timeline: {timeline}")
    if not mix or not os.path.exists(mix):
        sys.exit(f"找不到 mix: {mix}")

    tl = load_json(timeline)
    segs = tl.get("segments", [])
    subs = tl.get("subs", [])
    total = float(tl.get("total", 0))
    wd = wav_duration(mix)

    print(f"timeline: {timeline}")
    print(f"mix     : {mix}")
    print(f"total   : {total:.3f}s")
    print(f"wav     : {wd:.3f}s")

    errors = []
    warnings = []

    if abs(total - wd) > 0.05:
        errors.append(f"total 與 mix.wav 長度差 {abs(total - wd):.3f}s（>0.05）")

    if segs:
        s = sum(float(x.get("dur", 0)) for x in segs)
        if abs(s - total) > 0.05:
            errors.append(f"segments 總和 {s:.3f}s 與 total {total:.3f}s 不符")
        last = segs[-1]
        print(f"last seg: {last.get('id')}  start={last.get('start'):.3f}  dur={last.get('dur'):.3f}")

    if subs:
        last_sub = max(subs, key=lambda x: float(x.get("end", 0)))
        tail = total - float(last_sub["end"])
        print(f"last sub: {last_sub['end']:.3f}s  tail={tail:.3f}s")
        print(f"           {last_sub.get('text','')}")
        if tail < args.min_tail:
            warnings.append(f"片尾只有 {tail:.3f}s（建議 >= {args.min_tail:.1f}s）")
        for i, sub in enumerate(subs):
            if float(sub.get("end", 0)) > total + 0.01:
                errors.append(f"字幕 #{i+1} 超過 total: end={sub['end']}")

    if segs:
        for i, seg in enumerate(segs):
            start = float(seg.get("start", 0))
            dur = float(seg.get("dur", 0))
            if i == 0 and abs(start) > 0.001:
                warnings.append(f"第一段不是從 0 開始: {seg.get('id')} start={start}")
            if dur <= 0:
                errors.append(f"segment {seg.get('id')} dur <= 0")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")

    if errors:
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
