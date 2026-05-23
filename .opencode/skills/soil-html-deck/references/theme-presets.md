# HTML 簡報主題預設

本文件提供 `soil-html-deck` 的多種視覺主題預設。
根據簡報主題的語境，選擇最適合的預設作為起點。

---

## 使用方式

在建立 HTML 簡報時，根據主題內容選擇預設，將對應的 CSS 變數注入 `:root`。
所有主題共用相同的 HTML 結構，只改變色彩、字體與裝飾元素。

---

## Theme 1：科技深色（Tech Dark）—— 預設主題

> 適用：AI / SaaS / 開發者工具 / 數據分析 / 技術演講

```css
:root {
  --bg-primary: #0A0E1A;
  --bg-secondary: #111827;
  --bg-card: rgba(255, 255, 255, 0.04);
  --text-primary: #F1F5F9;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;
  --accent-1: #3B82F6;       /* 科技藍 */
  --accent-2: #8B5CF6;       /* 紫色強調 */
  --border: rgba(255, 255, 255, 0.08);
  --font-display: 'Inter', 'Noto Sans TC', sans-serif;
  --font-body: 'Inter', 'Noto Sans TC', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --kicker-style: uppercase;  /* 使用大寫英文 kicker */
  --radius: 12px;
}
```

**視覺特色**：
- 深色背景 + 微弱邊框
- JetBrains Mono 等寬字體 kicker
- 玻璃態卡片（glassmorphism）
- 漸層強調色

---

## Theme 2：東方文化（Eastern Heritage）

> 適用：傳統文化 / 歷史故事 / 節慶 / 人文藝術

```css
:root {
  --bg-primary: #1A1410;
  --bg-secondary: #2A2018;
  --bg-card: rgba(210, 180, 140, 0.06);
  --text-primary: #F5E6D0;
  --text-secondary: #C4A882;
  --text-muted: #8B7355;
  --accent-1: #C04A1A;       /* 硃砂紅 */
  --accent-2: #D4A853;       /* 端陽金 */
  --border: rgba(210, 180, 140, 0.12);
  --font-display: 'Noto Serif TC', 'PMingLiU', serif;
  --font-body: 'Noto Sans TC', 'Microsoft JhengHei', sans-serif;
  --font-mono: 'Noto Sans TC', sans-serif;
  --kicker-style: none;       /* 不使用英文 kicker */
  --radius: 4px;              /* 較小的圓角，保持方正感 */
}
```

**視覺特色**：
- 暖色調深底（墨色 + 古銅）
- 襯線字體大標題（書卷氣）
- 不使用英文 kicker/tag
- 方正圓角，隱含印章感
- 強調色取自傳統色譜（硃砂、端陽金）

**裝飾元素建議**：
- 用 `border-left: 3px solid var(--accent-1)` 取代 kicker
- 引言用「」括號而非 ""
- 分隔線可用古典花紋或簡潔細線

---

## Theme 3：清新自然（Nature Light）

> 適用：教育 / 環保 / 健康 / 生活風格 / 親子

```css
:root {
  --bg-primary: #FAFDF7;
  --bg-secondary: #F0F5EB;
  --bg-card: rgba(76, 120, 68, 0.05);
  --text-primary: #1A2E1A;
  --text-secondary: #4A6741;
  --text-muted: #7A9970;
  --accent-1: #2D7A3A;       /* 森林綠 */
  --accent-2: #E8963A;       /* 暖橘 */
  --border: rgba(76, 120, 68, 0.12);
  --font-display: 'Noto Sans TC', sans-serif;
  --font-body: 'Noto Sans TC', sans-serif;
  --font-mono: 'Noto Sans Mono', monospace;
  --kicker-style: none;       /* 不使用英文 kicker */
  --radius: 16px;
}
```

**視覺特色**：
- 米白/淺綠背景（明亮舒適）
- 深綠色文字（高對比、護眼）
- 大圓角卡片（友善感）
- 不使用英文 kicker

---

## Theme 4：專業商務（Corporate Minimal）

> 適用：商業報告 / 策略提案 / 投資簡報 / 數據報告

```css
:root {
  --bg-primary: #FFFFFF;
  --bg-secondary: #F8F9FA;
  --bg-card: rgba(0, 0, 0, 0.02);
  --text-primary: #1A1A2E;
  --text-secondary: #4A4A5A;
  --text-muted: #9A9AAA;
  --accent-1: #1A3A5C;       /* 深海藍 */
  --accent-2: #C0392B;       /* 警示紅（用於數據強調）*/
  --border: rgba(0, 0, 0, 0.08);
  --font-display: 'Noto Sans TC', sans-serif;
  --font-body: 'Noto Sans TC', sans-serif;
  --font-mono: 'Roboto Mono', monospace;
  --kicker-style: uppercase;  /* 小型大寫 kicker */
  --radius: 8px;
}
```

**視覺特色**：
- 純白背景、乾淨克制
- 深藍色主調（專業信任感）
- 紅色僅用於數據重點標記
- 大量留白，資訊密度適中

---

## Theme 5：創意暖色（Creative Warm）

> 適用：設計提案 / 品牌介紹 / 行銷企劃 / 社群內容

```css
:root {
  --bg-primary: #FDF6EC;
  --bg-secondary: #FAF0E0;
  --bg-card: rgba(192, 74, 26, 0.04);
  --text-primary: #2C1810;
  --text-secondary: #6B4C3B;
  --text-muted: #A08070;
  --accent-1: #E07A5F;       /* 赤陶橘 */
  --accent-2: #3D405B;       /* 靛藍灰 */
  --border: rgba(192, 74, 26, 0.10);
  --font-display: 'Noto Serif TC', serif;
  --font-body: 'Noto Sans TC', sans-serif;
  --font-mono: 'Noto Sans Mono', monospace;
  --kicker-style: none;
  --radius: 20px;
}
```

**視覺特色**：
- 奶油底色 + 赤陶色強調（溫暖有活力）
- 襯線標題 + 無襯線內文的混搭
- 大圓角設計
- 適合帶有品牌個性的簡報

---

## 主題選擇速查表

| 簡報主題 | 建議主題 | 理由 |
|---------|---------|------|
| AI 技術演講 | Theme 1 科技深色 | 科技感、專業感 |
| 端午節由來 | Theme 2 東方文化 | 文化沉浸感 |
| 環保教育課程 | Theme 3 清新自然 | 友善、明亮 |
| 年度業績報告 | Theme 4 專業商務 | 乾淨、數據導向 |
| 品牌設計提案 | Theme 5 創意暖色 | 溫暖、有品味 |
| 程式開發教學 | Theme 1 科技深色 | 開發者熟悉 |
| 歷史人物傳記 | Theme 2 東方文化 | 書卷氣 |
| 親子活動介紹 | Theme 3 清新自然 | 輕鬆、友善 |
| 投資人簡報 | Theme 4 專業商務 | 專業信任 |
| 社群行銷提案 | Theme 5 創意暖色 | 有溫度 |

---

## 自訂主題

如果預設主題都不適合，可基於以下框架自訂：

```css
:root {
  /* 背景層級 */
  --bg-primary: ;      /* 主背景 */
  --bg-secondary: ;    /* 次要背景（卡片外層）*/
  --bg-card: ;         /* 卡片/容器背景 */

  /* 文字層級 */
  --text-primary: ;    /* 標題、主要文字 */
  --text-secondary: ;  /* 內文 */
  --text-muted: ;      /* 輔助說明、meta */

  /* 強調色 */
  --accent-1: ;        /* 主強調色（CTA、重點）*/
  --accent-2: ;        /* 次強調色（圖表、裝飾）*/

  /* 邊框 */
  --border: ;          /* 卡片邊框、分隔線 */

  /* 字體 */
  --font-display: ;    /* 大標題 */
  --font-body: ;       /* 內文 */
  --font-mono: ;       /* 程式碼 / 數據 */

  /* 裝飾 */
  --kicker-style: ;    /* uppercase | none */
  --radius: ;          /* 圓角大小 */
}
```
