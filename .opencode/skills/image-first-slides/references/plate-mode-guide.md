# Plate 模式排版指南

Plate 模式生成無文字的底圖，再由 `pack_pptx.py` 疊加可編輯的 PowerPoint 文字框。
本文件定義 plate 模式的排版規範。

---

## 1. 文字框配置

### 標題文字框
- **位置**：頁面上方 1/3 區域
- **字體**：`Microsoft JhengHei`（粗體）
- **字級**：44-56pt（依內容長度調整）
- **對齊**：置中或靠左
- **顏色**：白色（深色底圖）或深色（淺色底圖）

### 副標題/內文文字框
- **位置**：標題下方，留出 20-30% 的呼吸空間
- **字體**：`Microsoft JhengHei`（一般）
- **字級**：18-24pt
- **行距**：1.4-1.6 倍
- **顏色**：與標題同系但降低對比

### 頁碼文字框
- **位置**：右下角
- **字級**：12-14pt
- **顏色**：半透明白色或灰色

---

## 2. 文字可讀性保障

### 底框策略（推薦）
在文字區域下方放置半透明矩形，確保文字在任何底圖上都可讀：

```python
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor

# 加入半透明深色底框
backdrop = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE,
    left=Inches(0.5),
    top=Inches(0.3),
    width=Inches(9),
    height=Inches(1.2)
)
fill = backdrop.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0x10, 0x15, 0x25)
fill.fore_color.brightness = 0
backdrop.fill.background()  # 設定透明度需用 XML
```

### 透明度設定（需直接操作 XML）
```python
from pptx.oxml.ns import qn

# 設定 70% 透明度（alpha = 30000 = 30%）
solidFill = backdrop.fill._fill
srgbClr = solidFill.find(qn('a:srgbClr'))
alpha = srgbClr.makeelement(qn('a:alpha'), {'val': '30000'})
srgbClr.append(alpha)
```

---

## 3. spec.yaml 格式

Plate 模式使用 `spec.yaml` 定義每頁的文字疊加內容：

```yaml
slides:
  - page: 1
    role: cover
    title: "簡報標題"
    subtitle: "副標題文字"
    title_style:
      font_size: 56
      bold: true
      color: "#FFFFFF"
      position: [1.0, 2.5]  # [left_inches, top_inches]
    subtitle_style:
      font_size: 24
      color: "#CCCCCC"
      position: [1.0, 4.0]

  - page: 2
    role: content
    title: "核心觀點"
    body:
      - "第一個要點"
      - "第二個要點"
      - "第三個要點"
    title_style:
      font_size: 44
      bold: true
      color: "#FFFFFF"
      position: [0.8, 0.5]
    body_style:
      font_size: 20
      color: "#E0E0E0"
      position: [0.8, 2.0]
      line_spacing: 1.5
      bullet: true

  - page: 10
    role: cta
    title: "行動呼籲"
    subtitle: "立即開始！"
    title_style:
      font_size: 48
      bold: true
      color: "#FFD700"
      position: [1.0, 3.0]
      alignment: center
```

### spec.yaml 欄位說明

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `page` | int | ✅ | 頁碼（1-based） |
| `role` | str | ✅ | cover / content / chart / compare / cta |
| `title` | str | ✅ | 標題文字 |
| `subtitle` | str | ❌ | 副標題 |
| `body` | list | ❌ | 內文條列 |
| `*_style.font_size` | int | ❌ | 字級（pt），預設：title=44, body=20 |
| `*_style.bold` | bool | ❌ | 是否粗體 |
| `*_style.color` | str | ❌ | 色彩 HEX，預設白色 |
| `*_style.position` | [float, float] | ❌ | [左邊距, 上邊距]（英吋）|
| `*_style.alignment` | str | ❌ | left / center / right |
| `*_style.line_spacing` | float | ❌ | 行距倍數 |
| `*_style.bullet` | bool | ❌ | 是否加入條列符號 |

---

## 4. 底圖生成注意事項

為 plate 模式生成底圖時，prompt 中必須明確指定：
- **「no text, no words, no letters, no characters」** — 確保圖片上沒有任何文字
- **在文字預留區域保持低對比/暗色/模糊** — 讓後續疊加的文字可讀
- **避免在圖片中心放置密集細節** — 中心區域通常是標題位置

### 底圖 prompt 範例
```
16:9 aspect ratio. [場景描述], with a large dark gradient area
on the upper portion for text overlay. No text, no words, no letters,
no characters anywhere in the image. [風格描述], cinematic lighting.
```
