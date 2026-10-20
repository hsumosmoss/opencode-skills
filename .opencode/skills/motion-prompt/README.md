# motion-prompt（中文增強版）

[`motion-prompt`](https://showheyohtaki.github.io/motion-prompt/) 是一個編號化的動作圖鑑：144 個動作、運鏡、轉場、UI、網頁效果與光線風格，每個都有名稱、一句話意義、秒數／緩動規格，以及可直接讀的 Canvas 2D 參考碼。上游由 Shohei Ohtaki 製作，MIT 授權。

這個目錄是**中文增強版**：官方檔案原封不動，另外加上繁體中文覆蓋層與同步工具。

## 多了什麼

| 項目 | 說明 |
|---|---|
| `zh/zh.json` | 144 筆的中文名稱、別名、一句話意義、摘要與中文標籤 |
| `zh/index.zh.tsv` | 合併後的中文索引（10 欄，含中英文標籤），用 `Select-String`／`grep` 查 |
| `references/motion-prompt-zh.md` | 給人看的 144 筆速查表（依 pack → 分類排列） |
| `zh/update.mjs` | 同步上游三個檔案、補回中文導引、重建索引 |
| `update.ps1` | Windows 一鍵包裝（`-Check`、`-Offline`） |

中文只翻 `name`／`meaning`／`summary`／`tags`；`spec` 與程式碼保持原文，避免秒數、曲線與係數失真。

## 安裝

把整個 `motion-prompt` 資料夾放進 OpenCode 的 skills 目錄：

```powershell
# Windows
Copy-Item -Recurse .\motion-prompt "$env:USERPROFILE\.config\opencode\skills\"
```

```bash
# macOS / Linux
cp -R ./motion-prompt ~/.config/opencode/skills/
```

重啟 OpenCode 後，用 `opencode debug skill` 確認載入。

## 用法

```powershell
$mp = "$env:USERPROFILE\.config\opencode\skills\motion-prompt"

# 中文找（官方 search 只吃英日文）
Select-String -Path "$mp\zh\index.zh.tsv" -Pattern '轉場'

# 用編號取規格與程式碼
node "$mp\scripts\motion-prompt.mjs" get 138

# 開畫廊讓使用者自己挑
node "$mp\scripts\motion-prompt.mjs" pick --pack motion2
```

其他指令：`search`、`list`、`kit`、`prompt`、`info`，細節見 `SKILL.md`。

## 更新上游

```powershell
.\update.ps1            # 重抓上游 + 補回中文導引 + 重建索引
.\update.ps1 -Check     # 只比對
.\update.ps1 -Offline   # 不下載，只重建索引
```

macOS / Linux：

```bash
node zh/update.mjs
node zh/update.mjs --check
node zh/update.mjs --offline
```

同步後看 `zh/missing.txt`：新出現的 id 補進 `zh/zh.json` 再重建即可，舊翻譯不會被覆蓋。`zh/README.md` 有完整的檔案說明與翻譯原則。

## 目錄

```
motion-prompt/
├── SKILL.md                      # 官方 + 本地中文導引
├── LICENSE                       # 上游 MIT
├── scripts/motion-prompt.mjs     # 官方 CLI（未修改）
├── references/
│   ├── porting.md                # 官方移植指南
│   └── motion-prompt-zh.md       # 中文速查表（產生檔）
├── zh/
│   ├── zh.json                   # 翻譯覆蓋層
│   ├── index.zh.tsv              # 中文索引（產生檔）
│   ├── missing.txt               # 未翻譯 id（產生檔）
│   ├── build-zh-index.mjs
│   ├── update.mjs
│   ├── patch-body.md             # 同步後要補回的 SKILL.md 區塊
│   ├── patch-description.txt     # 同步後要補回的 description 觸發詞
│   └── README.md
└── update.ps1
```

## 授權

上游程式碼與規格：MIT © 2026 Shohei Ohtaki，見 `LICENSE`。
本地新增的中文覆蓋層與同步工具同樣以 MIT 釋出。
