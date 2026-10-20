#!/usr/bin/env python3
"""產生可疊在現有解說影片上的透明水墨覆蓋層。

輸出：
  ink_edge.png    深墨邊框＋角落墨漬；中心透明；適合 multiply
  paper_grain.png 暖紙色＋紙紋；中心很淡、邊緣較明顯；適合 soft-light / screen
  overlay.json    尺寸、seed、檔案名稱

用法：
  python make_ink_overlay.py --width 1920 --height 1080 --seed 7 --out-dir assets/ink-overlay
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def multiscale_noise(rng, h, w, scales=(5, 16, 48)):
    out = np.zeros((h, w), dtype=np.float32)
    for i, s in enumerate(scales):
        n = rng.normal(0.0, 1.0, (h, w)).astype(np.float32)
        n = gaussian_filter(n, s)
        n /= max(1e-6, float(np.std(n)))
        out += n / (i + 1)
    out /= max(1e-6, float(np.std(out)))
    return out


def edge_mask(h, w):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    x = (xx / max(1, w - 1)) * 2.0 - 1.0
    y = (yy / max(1, h - 1)) * 2.0 - 1.0
    d = np.maximum(np.abs(x), np.abs(y))
    edge = smoothstep(0.70, 1.0, d)
    # 四角再加一點重量
    corner = np.exp(-((np.abs(x) - 1.0) ** 2 + (np.abs(y) - 1.0) ** 2) / 0.035)
    edge = np.clip(edge + 0.22 * corner * (1.0 - edge), 0.0, 1.0)
    return x, y, edge


def wash_mask(rng, h, w, edge, count=10):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for _ in range(count):
        # 貼著畫面邊緣選點
        side = int(rng.integers(0, 4))
        t = float(rng.uniform(0.05, 0.95))
        if side == 0:
            cx, cy = t * w, float(rng.uniform(-0.03, 0.12)) * h
        elif side == 1:
            cx, cy = t * w, float(rng.uniform(0.88, 1.03)) * h
        elif side == 2:
            cx, cy = float(rng.uniform(-0.03, 0.12)) * w, t * h
        else:
            cx, cy = float(rng.uniform(0.88, 1.03)) * w, t * h
        rx = float(rng.uniform(0.025, 0.075)) * w
        ry = float(rng.uniform(0.022, 0.070)) * h
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=int(rng.uniform(45, 105)))
    m = np.asarray(m, dtype=np.float32) / 255.0
    m = gaussian_filter(m, max(2.5, min(h, w) * 0.008))
    return np.clip(m * edge, 0.0, 1.0)


def save_rgba(path, rgb, alpha):
    h, w = alpha.shape
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 0] = rgb[0]
    arr[..., 1] = rgb[1]
    arr[..., 2] = rgb[2]
    arr[..., 3] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    Image.fromarray(arr, "RGBA").save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out-dir", default="assets/ink-overlay")
    ap.add_argument("--no-paper", action="store_true")
    ap.add_argument("--safe-bottom", type=float, default=0.10,
                    help="底部保留給字幕的比例（0-0.4，預設 0.10）")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    h, w = args.height, args.width
    x, y, edge = edge_mask(h, w)
    noise = multiscale_noise(rng, h, w)
    wash = wash_mask(rng, h, w, edge)

    # 底部字幕安全區：越靠近畫面底部，覆蓋層越淡
    yy = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
    if args.safe_bottom > 0:
        fade = smoothstep(0.0, 1.0, (1.0 - yy) / args.safe_bottom)
    else:
        fade = np.ones((h, 1), dtype=np.float32)

    # 墨邊：中心完全透明；邊緣 0.30–0.58；角落最重
    ink_alpha = np.clip(
        edge * (0.30 + 0.08 * noise) + 0.14 * wash, 0.0, 0.58
    ) * fade
    os.makedirs(args.out_dir, exist_ok=True)
    ink_path = os.path.join(args.out_dir, "ink_edge.png")
    save_rgba(ink_path, (27, 24, 23), ink_alpha)

    files = {"ink_edge": os.path.basename(ink_path)}
    if not args.no_paper:
        # 紙紋：中心 alpha 約 0.02–0.035，邊緣約 0.08–0.10
        fiber = gaussian_filter(noise, 1.2)
        paper_alpha = np.clip(
            0.012 + 0.045 * edge + 0.006 * fiber, 0.0, 0.075
        ) * fade
        paper_path = os.path.join(args.out_dir, "paper_grain.png")
        save_rgba(paper_path, (247, 243, 233), paper_alpha)
        files["paper_grain"] = os.path.basename(paper_path)

    meta = {
        "width": w,
        "height": h,
        "seed": args.seed,
        "files": files,
        "safe_bottom": args.safe_bottom,
        "usage": {
            "ink_edge": "multiply 或 alpha overlay； opacity 0.35-0.6；中心透明，不會壓住字幕",
            "paper_grain": "soft-light 或 screen； opacity 0.3-0.5；放在文字圖層下方",
        },
    }
    meta_path = os.path.join(args.out_dir, "overlay.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(ink_path)
    if "paper_grain" in files:
        print(os.path.join(args.out_dir, files["paper_grain"]))
    print(meta_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())


