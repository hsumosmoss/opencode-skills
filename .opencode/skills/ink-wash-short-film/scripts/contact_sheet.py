#!/usr/bin/env python3
"""把 stills 拼成 contact sheet。

用法：
  python contact_sheet.py --dir scripts\\work\\stills --out scripts\\work\\stills\\contact.jpg
"""
import argparse
import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFont


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--glob", default="*.jpg")
    ap.add_argument("--out", help="預設 <dir>\\contact.jpg")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--thumb-w", type=int, default=480)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, args.glob)))
    if not files:
        sys.exit(f"沒有檔案: {args.dir}\\{args.glob}")

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

    for i, path in enumerate(files):
        im = Image.open(path).convert("RGB").resize((args.thumb_w, thumb_h), Image.LANCZOS)
        x = (i % args.cols) * args.thumb_w
        y = (i // args.cols) * (thumb_h + label_h)
        sheet.paste(im, (x, y))
        draw.text((x + 6, y + thumb_h + 4), os.path.basename(path),
                  fill=(30, 27, 28), font=font)

    out = args.out or os.path.join(args.dir, "contact.jpg")
    sheet.save(out, quality=90)
    print(f"{out}  {sheet.size}  {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
