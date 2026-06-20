# Component Mapping Reference

Markdown → HTML 完整對照表。`build.mjs` 依此規則解析內容。

## 1. Section（主章節）

**Markdown：**
```markdown
# LABEL：章節標題
> 章節引言文字...
```

**HTML：**
```html
<section class="handout-section" id="section-n">
  <div class="reveal">
    <span class="section-label">LABEL</span>
    <h2 class="section-title">章節標題</h2>
    <p class="lead">章節引言文字...</p>
  </div>
```

規則：
- `#` 以冒號分為 label 和 title（`# LABEL：TITLE`）
- 緊接的 `>` blockquote 作為 `.lead`
- 自動編號，`id` 由標題轉為 kebab-case

## 2. Sub-section（子章節）

**Markdown：**
```markdown
## 子章節名稱
```

**HTML：**
```html
<h3 class="sub-title"><span class="bar"></span>子章節名稱</h3>
```

## 3. Card（卡片）

**Markdown：**
```markdown
### 🔧 卡片標題
- 項目一
- 項目二
```

**HTML：**
```html
<div class="card">
  <h3 class="card-title"><span class="icon">🔧</span> 卡片標題</h3>
  <ul><li>項目一</li><li>項目二</li></ul>
</div>
```

規則：`###` 開頭，emoji 拆入 `.icon`，內容自動包入 card。

## 4. Table（表格）

**Markdown：**
```markdown
| Header | Header |
|---|---|
| Data | Data |
```

**HTML：** 標準 `<table>`，`build.mjs` 不處理，保留原生 Markdown 解析。

## 5. Step（步驟）

**Markdown：**
````
`step` Step name: Description text here
````

**In the middle of the action text, 偵測 `` `step` `` 開頭的行：**

**HTML：**
```html
<div class="step">
  <div class="step-num">1</div>
  <div class="step-content">
    <h4>Step name</h4>
    <p>Description text here</p>
  </div>
</div>
```

## 6. Tip Box（提示框）

**Markdown：**
```markdown
> **💡 Tip** 提示文字
```

**HTML：**
```html
<div class="tip-box">
  <span class="label">💡 Tip</span> 提示文字
</div>
```

## 7. Warning Box（警告框）

**Markdown：**
```markdown
> **⚠️ Warning** 警告文字
```

**HTML：**
```html
<div class="warning-box">
  <span class="label">⚠️ Warning</span> 警告文字
</div>
```

## 8. Flow（流程圖）

**Markdown：**
```markdown
[flow]
Step 1
Step 2
Step 3
[/flow]
```

**HTML：**
```html
<div class="flow-row">
  <span class="flow-step">Step 1</span>
  <span class="flow-arrow">→</span>
  <span class="flow-step">Step 2</span>
  <span class="flow-arrow">→</span>
  <span class="flow-step">Step 3</span>
</div>
```

## 9. Tags（標籤）

**Markdown：**
```markdown
[tags]
green: 初階
orange: 中階
purple: 進階
[/tags]
```

**HTML：**
```html
<p>
  <span class="tag green">初階</span>
  <span class="tag orange">中階</span>
  <span class="tag purple">進階</span>
</p>
```

## 10. Summary Grid（總結網格）

**Markdown：**
```markdown
[summary]
8: 章節
24: 單元
10+: 小時
[/summary]
```

**HTML：**
```html
<div class="summary-grid">
  <div class="summary-item"><div class="num">8</div><div class="desc">章節</div></div>
  ...
</div>
```

## 11. Glossary（術語表）

**Markdown：**
````
```glossary
Term: Definition
Another term: Definition
```
````

**HTML：**
```html
<p class="glossary-term">Term</p>
<p class="glossary-def">Definition</p>
```

## 12. Checklist（勾選清單）

**Markdown：**
```markdown
- [x] 已完成項目
- [ ] 未完成項目
```

**HTML：**
```html
<ul class="checklist">
  <li>已完成項目</li>
  <li>未完成項目</li>
</ul>
```

## 13. Code Block（程式碼）

**Markdown：**
````
```bash
npm install
```
````

**HTML：**
```html
<pre><code>npm install</code></pre>
```
