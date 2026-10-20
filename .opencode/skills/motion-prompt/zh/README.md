# 中文索引（本地增補）

這一層不是官方的一部分。官方檔案保持原樣，中文只放在 `zh.json`，由
`build-zh-index.mjs` 在執行時合併；`update.mjs` 負責同步上游並把中文導引
補回 `SKILL.md`。

## 檔案

| 檔案 | 用途 |
|---|---|
| `zh.json` | 翻譯覆蓋層：`id → 中文名稱／別名／意義／摘要／標籤`，另含 pack 與分類的中文名 |
| `build-zh-index.mjs` | 抓上游 catalog、合併 `zh.json`、產出索引與速查表 |
| `index.zh.tsv` | 產出物。欄位：id、pack、分類、中文名、英文名、日文名、中文意義、中文標籤、中文摘要、英文標籤 |
| `missing.txt` | 上游有、但 `zh.json` 還沒翻的 id（已翻完時是空檔） |
| `update.mjs` | 同步上游三個檔案、補回中文導引與 description 觸發詞、重建索引 |
| `patch-body.md` | 要補回 `SKILL.md` 的中文導引區塊（含 `zh-patch` 標記） |
| `patch-description.txt` | 要接在 frontmatter `description` 後面的中文觸發詞 |
| `backup/` | 每次覆寫 `SKILL.md` 前的備份，只留最新 5 份 |

另外，`../references/motion-prompt-zh.md` 是給人看的 144 筆速查表，由
`build-zh-index.mjs` 一起產生，不要手改。

## 用法

```powershell
# 同步上游 + 重建索引（建議）
.\update.ps1

# 只比對，不寫入
.\update.ps1 -Check

# 不下載，只重建索引（例如只改了 zh.json）
.\update.ps1 -Offline
# 或
node zh\build-zh-index.mjs

# 離線：先自備一份 catalog.json
node zh\build-zh-index.mjs --local path\to\catalog.json
```

查中文：

```powershell
Select-String -Path zh\index.zh.tsv -Pattern '轉場'
```

拿到 id 之後再走官方 `get`：

```powershell
node scripts\motion-prompt.mjs get 129
```

官方 `search` 只吃英文與日文；中文查詢一律先查 `index.zh.tsv`。

## 更新上游時

`update.mjs` 會做這幾件事，正常情況下不需要手動補洞：

1. 下載上游的 `SKILL.md`、`scripts/motion-prompt.mjs`、`references/porting.md`
   （全部先下載到記憶體，任何一個失敗就整批不寫，避免半套）。
2. 把 `patch-description.txt` 接回 frontmatter 的 `description`，把
   `patch-body.md` 插回 `SKILL.md`。已有的舊版中文尾巴會先移除，反覆執行
   不會累積標點。
3. 備份舊 `SKILL.md` 到 `backup/`，再寫入新檔。
4. 跑 `build-zh-index.mjs`，印出 `missing.txt` 裡新出現的 id。

上游若改了 `SKILL.md` 的結構（例如找不到 description 或插入點），
`update.mjs` 會印出警告並把區塊附加在檔尾，此時請手動確認一次。

新出現的 id 補進 `zh.json` 的 `entries` 後，再跑一次 `.\update.ps1 -Offline`
即可；舊翻譯不會被覆蓋。

## 翻譯原則

- 保留英文原名，中文只做「好懂」的補充，不取代原文。
- 只翻 `name`、`meaning`、`summary`、`tags`；`spec` 與程式碼不翻。
  秒數、緩動曲線、係數翻錯比不翻更糟。
- 顯示名稱是「主名（別名1／別名2）」：`zh.json` 裡用 `name` + `aka` 分開存，
  建索引時才合併，主名不會越長越誇張。
- 術語盡量用台灣常見說法（緩動、過衝、殘影、視差、掃光、換場）。
- `photo` pack 保留攝影術語（林布蘭光、蝴蝶光、高調、低調），不硬翻成中國譯名。
- 一個 id 的 `tags` 以 4～8 個詞為限，包含「動作本身」和「常見用途」。
