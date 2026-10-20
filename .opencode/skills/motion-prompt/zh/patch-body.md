<!-- zh-patch:start (local addition; re-apply after syncing from upstream) -->

## 中文索引（本地增補）

官方資料只有英文與日文。中文名稱、一句話意義、摘要與中文標籤放在
`zh/zh.json`，合併後的索引是 `zh/index.zh.tsv`（欄位：id、pack、分類、
中文名、英文名、日文名、中文意義、中文標籤、中文摘要）。人看的版本是
`references/motion-prompt-zh.md`。

- **使用者用中文描述時**：先讀 `zh/index.zh.tsv` 找候選（可直接 `Select-String`
  或讀檔比對「中文名／標籤／摘要」），再用官方 `get <id>` 取規格與程式碼。
  官方 `search` 只吃英日文，不要拿中文去餵它。
- **使用者用英文或日文時**：照原本流程走官方 `search`，不需要碰中文索引。
- **回報時**：同時給中文名與英文名，例如「#005 遮罩揭露（Mask reveal）」，
  方便使用者對照畫廊。
- **更新上游後**：跑 `.\update.ps1`（或 `node zh/update.mjs`）。它會重抓
  上游的 `SKILL.md`、`scripts/motion-prompt.mjs`、`references/porting.md`，
  把這段中文導引與 description 的中文觸發詞補回去，再重建索引；上游新增的
  動作不會消失，只會顯示為未翻譯（此時索引的中文欄位為空，請用英文名繼續工作）。
- `spec` 與程式碼刻意不翻譯：裡面的秒數、緩動曲線與係數是原文，翻了容易失真。

<!-- zh-patch:end -->
