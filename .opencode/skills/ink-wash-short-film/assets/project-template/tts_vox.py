#!/usr/bin/env python3
"""逐句生成旁白（VoxCPM2），輸出 build.py 認得的檔名。

約定：`tts/<scene>_<index>.wav`，例如 s1_0.wav、s3_2.wav。
多候選時另外寫 `tts/cand/<key>_s<seed>.wav` 與每句 montage；
`tts/<key>.wav` 固定放第一個 seed，build.py 不必改。

用法：
  python tts_vox.py --dry-run          # 只印出將要生成的句子
  python tts_vox.py                    # 生成全部（預設 2 個候選）
  python tts_vox.py --only s2_1        # 只重做某一句
  python tts_vox.py --candidates 1     # 只生一個版本
"""
import argparse
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
DEFAULT_VOX = os.path.join(
    os.path.expanduser("~"), "Documents", "OpenCode", "Voice", "voxcpm2-voice-cloner"
)


def parse_args():
    ap = argparse.ArgumentParser(description="VoxCPM2 逐句旁白（ink_history_video 格式）")
    ap.add_argument("--script", default=os.path.join(HERE, "script.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "tts"))
    ap.add_argument("--voice", default="許耀文")
    ap.add_argument("--vox-dir", default=DEFAULT_VOX)
    ap.add_argument("--candidates", type=int, default=2, help="每句生幾個 seed（預設 2）")
    ap.add_argument("--seed", type=int, default=1, help="第一個 seed，之後遞增")
    ap.add_argument("--cfg", type=float, default=2.0)
    ap.add_argument("--timesteps", type=int, default=10)
    ap.add_argument("--no-speech", action="store_true", help="不過 pronounce.py")
    ap.add_argument("--force", action="store_true", help="已有檔案也重做")
    ap.add_argument("--no-default", action="store_true", help="只生候選，不覆蓋 tts/<key>.wav")
    ap.add_argument("--only", nargs="*", default=None, help="只做指定 key，例如 s2_1")
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args()


def speech_text(text, vox_dir, enabled):
    if not enabled:
        return text
    sys.path.insert(0, vox_dir)
    import pronounce

    return pronounce.speech_text(text)


def main():
    args = parse_args()
    script = json.load(open(args.script, encoding="utf-8"))
    speech_map = script.get("speech", {})
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(os.path.join(args.out, "cand"), exist_ok=True)

    jobs = []
    for sc in script["scenes"]:
        for i, line in enumerate(sc["lines"]):
            jobs.append((f"{sc['id']}_{i}", line))

    if args.only:
        jobs = [j for j in jobs if j[0] in args.only]

    print(f"句子 {len(jobs)} 句 · 候選 {args.candidates} · seed {args.seed}..{args.seed + args.candidates - 1}")
    for key, line in jobs:
        print(f"  {key:6s} {line}")

    if args.dry_run:
        return

    vox = args.vox_dir
    sys.path.insert(0, vox)
    import numpy as np
    import soundfile as sf
    import torch
    from voxcpm import VoxCPM

    voice_dir = os.path.join(vox, "voices", args.voice)
    ref = os.path.join(voice_dir, "ref_voice.wav")
    prompt_path = os.path.join(voice_dir, "prompt.txt")
    for p in (ref, prompt_path):
        if not os.path.exists(p):
            raise SystemExit(f"缺少聲音檔：{p}")
    prompt_text = open(prompt_path, encoding="utf-8").read().strip()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    marker = os.path.join(vox, ".device_type")
    if os.path.exists(marker):
        device = open(marker, encoding="utf-8").read().strip()
    print(f"裝置 {device} · 聲音 {args.voice}")
    t0 = time.time()
    model = VoxCPM.from_pretrained(
        "openbmb/VoxCPM2", load_denoiser=False, device=device, optimize=False
    )
    sr = model.tts_model.sample_rate
    print(f"模型載入 {time.time() - t0:.1f}s · 取樣率 {sr} Hz")

    manifest_path = os.path.join(args.out, "_manifest.json")
    previous = {}
    if os.path.exists(manifest_path):
        try:
            prev = json.load(open(manifest_path, encoding="utf-8"))
            previous = {l["key"]: l for l in prev.get("lines", [])}
        except Exception:
            previous = {}

    manifest = {"voice": args.voice, "cfg": args.cfg, "timesteps": args.timesteps,
                "seeds": list(range(args.seed, args.seed + max(1, args.candidates))),
                "sample_rate": sr, "lines": list(previous.values())}
    order = [f"{sc['id']}_{i}" for sc in script["scenes"] for i, _ in enumerate(sc["lines"])]
    defaults = []
    total_t = time.time()

    for key, line in jobs:
        default_path = os.path.join(args.out, key + ".wav")
        if os.path.exists(default_path) and not args.force and not args.only:
            print(f"{key} 已存在，跳過")
            wav, _ = sf.read(default_path)
            defaults.append((key, wav.astype(np.float32)))
            continue

        spoken = speech_text(speech_map.get(key, line), vox, not args.no_speech)
        if spoken != line:
            print(f"{key} 發音稿：{spoken}")

        wavs, seeds = [], []
        for n in range(max(1, args.candidates)):
            seed = args.seed + n
            torch.manual_seed(seed)
            t1 = time.time()
            wav = model.generate(
                text=spoken,
                prompt_wav_path=ref,
                prompt_text=prompt_text,
                reference_wav_path=ref,
                cfg_value=args.cfg,
                inference_timesteps=args.timesteps,
            )
            dur = len(wav) / sr
            path = (os.path.join(args.out, "cand", f"{key}_s{seed}.wav")
                    if args.candidates > 1 else default_path)
            sf.write(path, wav, sr)
            wavs.append(wav)
            seeds.append(seed)
            print(f"  {key} seed={seed} {dur:.2f}s 生成 {time.time() - t1:.1f}s "
                  f"(RTF={(time.time() - t1) / max(dur, 0.01):.1f}) -> {path}")

        if not args.no_default:
            sf.write(default_path, wavs[0], sr)
        if args.candidates > 1:
            files = glob.glob(os.path.join(args.out, "cand", f"{key}_s*.wav"))
            files.sort(key=lambda p: int(os.path.basename(p).rsplit("_s", 1)[1].split(".")[0]))
            gap = np.zeros(int(sr * 0.7), dtype=wavs[0].dtype)
            montage = []
            for f in files:
                w, _ = sf.read(f)
                montage += [w.astype(np.float32), gap]
            sf.write(os.path.join(args.out, "cand", f"{key}_montage.wav"),
                     np.concatenate(montage), sr)
        defaults.append((key, wavs[0]))
        previous[key] = {
            "key": key, "text": line, "speech_text": spoken,
            "duration_s": round(len(wavs[0]) / sr, 2),
            "candidates": [{"seed": s, "duration_s": round(len(w) / sr, 2)}
                           for s, w in zip(seeds, wavs)],
        }

    manifest["lines"] = [previous[k] for k in order if k in previous]
    json.dump(manifest, open(manifest_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # 整段試聽：照順序、句間 0.8 秒、幕間 1.4 秒
    if defaults:
        gap_sentence = np.zeros(int(sr * 0.8), dtype=np.float32)
        gap_scene = np.zeros(int(sr * 1.4), dtype=np.float32)
        parts, current = [], None
        for key, wav in defaults:
            scene = key.split("_")[0]
            if current is not None and scene != current:
                parts.append(gap_scene)
            elif parts:
                parts.append(gap_sentence)
            parts.append(wav.astype(np.float32))
            current = scene
        review = os.path.join(args.out, "_review_only.wav" if args.only else "_review.wav")
        sf.write(review, np.concatenate(parts), sr)
        print(f"試聽檔：{review}")

    print(f"完成，共 {time.time() - total_t:.1f}s")


if __name__ == "__main__":
    main()
