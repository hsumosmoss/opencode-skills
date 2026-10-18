#!/usr/bin/env python3
"""
掃描 icons/ 與 patterns/，重建 index.json。
擴充機制：放入新的 .svg 後執行
    python tools/build_index.py
即可納入索引。新增整套圖示庫時，在 ICON_SETS 補一條即可。

index.json 結構：
{
  "generated": "YYYY-MM-DD",
  "sets": { "lucide": {"count": N, "license": "ISC"}, ... },
  "icons": [ {"name": "...", "set": "lucide", "path": "icons/lucide/....svg"}, ... ],
  "patterns": [ {"name": "...", "path": "patterns/....svg"}, ... ]
}
"""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 新增整套圖示庫時在此登記（授權以庫的 LICENSE 為準）
ICON_SETS = {
    "lucide": {"license": "ISC"},
    "tabler": {"license": "MIT"},
    "heroicons": {"license": "MIT"},
}


def normalize(stem: str) -> str:
    """檔名正規化：kebab/underscore → 統一小寫空白，便於模糊搜尋。"""
    return re.sub(r"[_\s]+", "-", stem.lower()).strip("-")


def main() -> None:
    icons = []
    sets = {}
    for set_name, meta in ICON_SETS.items():
        svg_dir = ROOT / "icons" / set_name
        if not svg_dir.is_dir():
            continue
        files = sorted(svg_dir.glob("*.svg"))
        for f in files:
            icons.append({
                "name": normalize(f.stem),
                "set": set_name,
                "path": str(f.relative_to(ROOT)).replace("\\", "/"),
            })
        sets[set_name] = {"count": len(files), "license": meta["license"]}

    patterns = []
    pat_dir = ROOT / "patterns"
    if pat_dir.is_dir():
        for f in sorted(pat_dir.glob("*.svg")):
            patterns.append({
                "name": normalize(f.stem),
                "path": str(f.relative_to(ROOT)).replace("\\", "/"),
            })

    index = {
        "generated": date.today().isoformat(),
        "sets": sets,
        "icons": icons,
        "patterns": patterns,
    }
    out = ROOT / "index.json"
    out.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"icons: {len(icons)}, patterns: {len(patterns)} -> index.json")


if __name__ == "__main__":
    main()
