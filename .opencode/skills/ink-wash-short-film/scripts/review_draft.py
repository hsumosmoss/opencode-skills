#!/usr/bin/env python3
"""從 draft 抽換幕邊界與關鍵時間，產生 contact sheet。

用法：
  python review_draft.py --video renders\\片.mp4 --timeline scripts\\work\\timeline.json --out scripts\\work\\review
  python review_draft.py --video ... --times 1.0,5.2,11.2,12.0 --out ...
"""
import argparse
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def probe_duration(video):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video,
    ], text=True)
    return float(out.strip())


def make_times(tl, key_times):
    times = set()
    for t in key_times:
        times.add(round(float(t), 3))
    for seg in tl.get("segments", []):
        s = float(seg.get("start", 0))
        d = float(seg.get("dur", 0))
        e = s + d
        for t in (s - 0.35, s, s + 0.35, e - 0.35, e, e + 0.35):
            if t > 0:
                times.add(round(t, 3))
    return sorted(times)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--timeline")
    ap.add_argument("--out", required=True)
    ap.add_argument("--times", help="逗號分隔的秒數；有給就只用這些")
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--thumb-w", type=int, default=384)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    frames_dir = os.path.join(args.out, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    dur = probe_duration(args.video)
    if args.times:
        times = sorted({round(float(x.strip()), 3) for x in args.times.split(",") if x.strip()})
    else:
        if not args.timeline:
            sys.exit("沒有 --times 時必須給 --timeline")
        tl = load_json(args.timeline)
        times = make_times(tl, [1.0, 5.2])
    times = [t for t in times if 0 <= t < dur]

    print(f"video {dur:.2f}s，抽 {len(times)} 幀")
    files = []
    for i, t in enumerate(times):
        name = f"f{i:02d}_{t:06.2f}.jpg"
        path = os.path.join(frames_dir, name)
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}",
               "-i", args.video, "-frames:v", "1", "-q:v", "2", path]
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if r.returncode != 0 or not os.path.exists(path):
            print(f"  skip {t:.2f}s: {r.stderr.strip()[:120]}")
            continue
        files.append((t, path))
        print(f"  {t:6.2f}s -> {name}")

    if not files:
        sys.exit("沒有成功抽到任何幀")

    thumb_h = int(args.thumb_w * 9 / 16)
    label_h = 28
    rows = (len(files) + args.cols - 1) // args.cols
    sheet = Image.new("RGB", (args.cols * args.thumb_w, rows * (thumb_h + label_h)),
                      (245, 242, 235))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/kaiu.ttf", 18)
    except Exception:
        font = ImageFont.load_default()

    for i, (t, path) in enumerate(files):
        im = Image.open(path).convert("RGB").resize((args.thumb_w, thumb_h), Image.LANCZOS)
        x = (i % args.cols) * args.thumb_w
        y = (i // args.cols) * (thumb_h + label_h)
        sheet.paste(im, (x, y))
        draw.text((x + 6, y + thumb_h + 4), f"{t:.2f}s  {os.path.basename(path)}",
                  fill=(30, 27, 28), font=font)

    out_path = os.path.join(args.out, "draft_contact.jpg")
    sheet.save(out_path, quality=92)
    print(out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
