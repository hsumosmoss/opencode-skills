# 此為【圖文錨定簡報輸出】格式框架 V5

# 勾選此資料則決定輸出樣式與排版。

---

## 【使用說明】

使用前請修改以下兩個參數：

- `total_slides_planned`：填入你要的總頁數  
- `slide_execution`：依來源文件的章節數量新增或刪減 page 區塊

圖片與 IP 人物部分**不需要手動填寫**，Soul 框架會自動判斷來源狀況執行。

---

## 【格式定義】

presentation\_anchored\_v5\_section\_split:

  metadata:

    version: "V5"

    processing\_target: "1:1 章節映射（每個大項獨立一頁）"

    total\_slides\_planned: "7"          \# ← 請修改為你要的總頁數

    style:
      theme_name: "Modern AI"
      color_primary: "#4285F4"  # 主題強調色
      color_background: "#FFFFFF" # 根據來源氛圍決定的投影片背景色 (如科技深藍、溫暖米色)
      color_text: "#333333"     # 根據背景色搭配的內文顏色 (深底用淺字，淺底用深字)
      font_heading: "sans-serif"

    watermark:

      position: "左下角"

      content: "品牌文字 \+ IP人物Q版娃娃"   \# ← 請修改為你的品牌文字

  slide\_execution:

    \# ─────────────────────────────────────────

    \# 範例頁 1（請依來源文件修改 section\_reference 與 content）

    \# ─────────────────────────────────────────

    \- page: 1

      section\_reference: "一、\[章節名稱\]"    \# ← 對應來源文件的第一個大項標題

      elements\_manifest:

        \- type: "title"

          content: "一、\[章節名稱\]"           \# ← 與 section\_reference 一致

        \- type: "text\_block"

          content: "【必須完整保留】\[此處貼上來源文字\]"

          \# 若需要特殊樣式，取消下方註解並填入：

          \# style:

          \#   color: "\#EA4335"

          \#   bold: true

        \- type: "image\_anchor"

          \# ↓ 以下由 Soul 框架自動執行，不需手動填寫

          instruction: |

            依優先順序執行：

            1\. 來源檔案有圖 → 請註記「使用來源文件圖片」即可，排版引擎會自動抓取對應頁數的圖片

            2\. 來源檔案無圖 → AI生成符合本頁情境的圖片

            placement: "文字下方，全寬顯示"

        \- type: "ip\_character"

          \# ↓ 以下由 Soul 框架自動執行，不需手動填寫

          instruction: |

            從上傳的IP JPEG檔中挑選一個人物

            動作須配合本頁文字情境

            placement: "右下角"

          fallback: "無IP檔案時略過此元素"

    \# ─────────────────────────────────────────

    \# 範例頁 2

    \# ─────────────────────────────────────────

    \- page: 2

      section\_reference: "二、\[章節名稱\]"

      elements\_manifest:

        \- type: "title"

          content: "二、\[章節名稱\]"

        \- type: "text\_block"

          content: "【必須完整保留】\[此處貼上來源文字\]"

        \- type: "image\_anchor"

          instruction: |

            依優先順序執行：

            1\. 來源檔案有圖 → 選與本頁主題最相關的一張真實照片

            2\. 來源檔案無圖 → AI生成符合本頁情境的圖片

            placement: "文字右側或下方"

        \- type: "ip\_character"

          instruction: |

            從上傳的IP JPEG檔中挑選一個人物

            動作須配合本頁文字情境

            placement: "右下角"

          fallback: "無IP檔案時略過此元素"

    \# ─────────────────────────────────────────

    \# 範例頁 3（含表格範例）

    \# ─────────────────────────────────────────

    \- page: 3

      section\_reference: "三、\[章節名稱\]"

      elements\_manifest:

        \- type: "title"

          content: "三、\[章節名稱\]"

        \- type: "text\_block"

          content: "【必須完整保留】\[此處貼上來源文字\]"

        \- type: "table"

          \# 若來源有【轉為表格】標記則自動執行

          instruction: "偵測到【轉為表格】標記時，將對應內容轉換為視覺化表格"

        \- type: "image\_anchor"

          instruction: |

            依優先順序執行：

            1\. 來源檔案有圖 → 選與本頁主題最相關的一張真實照片

            2\. 來源檔案無圖 → AI生成符合本頁情境的圖片

            placement: "文字下方"

        \- type: "ip\_character"

          instruction: |

            從上傳的IP JPEG檔中挑選一個人物

            動作須配合本頁文字情境

            placement: "右下角"

          fallback: "無IP檔案時略過此元素"

    \# ─────────────────────────────────────────

    \# 繼續新增頁面（複製上方區塊，修改 page 編號與內容）

    \# \- page: 4 ...

    \# \- page: 5 ...

    \# \- page: 6 ...

    \# ─────────────────────────────────────────

    \# ─────────────────────────────────────────

    \# 最後一頁：總結頁範例

    \# ─────────────────────────────────────────

    \- page: 7                            \# ← 改為你的最後一頁頁碼

      section\_reference: "七、總結"       \# ← 改為你的最後章節名稱

      elements\_manifest:

        \- type: "title"

          content: "七、總結"

        \- type: "text\_block"

          content: "【必須完整保留】\[此處貼上總結文字全文\]"

          style:

            color: "\#EA4335"

            bold: true

        \- type: "image\_anchor"

          instruction: |

            依優先順序執行：

            1\. 來源檔案有圖 → 選與本頁主題最相關的一張真實照片

            2\. 來源檔案無圖 → AI生成符合本頁情境的圖片

            placement: "文字下方"

        \- type: "ip\_character"

          instruction: |

            從上傳的IP JPEG檔中挑選一個人物

            動作建議：坐著總結 / 拿麥克風 / 雙手展開

            placement: "右下角"

          fallback: "無IP檔案時略過此元素"

---

## 【快速使用流程】

步驟 1：上傳來源文件（含文字，有圖更好）到 NotebookLM

步驟 2：上傳 IP 人物 JPEG 檔（可選，沒有也能執行）

步驟 3：上傳本 Body 框架 \+ Soul 框架到 NotebookLM 來源

步驟 4：在聊天框輸入以下提示詞：

「請根據來源文件，套用 Body V5 格式框架與 Soul V5 角色設定，

 生成 \[X\] 頁簡報，每頁對應一個大項章節，

 圖片優先使用來源文件的真實照片，無圖則 AI 生成，

 每頁加入一個 IP 人物，風格 Google 四原色簡潔清爽。」

---

## 【版本說明】

| 版本 | 主要改動 |
| :---- | :---- |
| V4 | 座標語法圖片定位（NotebookLM 不支援） |
| V5 | 語意指令圖片定位 \+ 智慧降級機制（來源有圖用真圖，無圖 AI 生成） |

