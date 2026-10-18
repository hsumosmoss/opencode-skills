# React + Babel 项目规范

用HTML+React+Babel做原型时必须遵守的技术规范。不遵守会炸。

## Pinned Script Tags（必须用这些版本）

在HTML的`<head>`里放这三个script tag，用**固定版本+integrity hash**：

```html
<script src="https://unpkg.com/react@18.3.1/umd/react.development.js" integrity="sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L" crossorigin="anonymous"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" integrity="sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm" crossorigin="anonymous"></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" integrity="sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y" crossorigin="anonymous"></script>
```

**不要**用`react@18`或`react@latest`这种unpinned版本——会出现版本漂移/缓存问题。

**不要**省略`integrity`——CDN一旦被劫持或篡改，这是防线。

## integrity 校验失败时 —— 降级为本地 vendor，不是删掉 integrity

**踩的坑（2026-10-18）**：unpkg 拉下来的文件 SRI hash 对不上（疑似中间层缓存篡改或 CDN 重建产物），浏览器 console 报 `Failed to find a valid digest`，React 拒绝执行，整页黑屏。第一反应如果是「删掉 integrity 就能跑」——**错，这等于拆掉防线**。

**正确降级顺序**：
1. 先换 CDN 试（unpkg → jsdelivr → esm.sh），有时只是单 CDN 缓存坏
2. 仍然失败 → **下载固定版本到项目本地 `assets/vendor/`**，用相对路径引用：
   ```html
   <script src="assets/vendor/react.development.js"></script>
   <script src="assets/vendor/react-dom.development.js"></script>
   <script src="assets/vendor/babel.min.js"></script>
   ```
3. 本地 vendor 对单文件交付也更优：**双击 file:// 打开零网络依赖**，离线/内网演示不炸
4. 在项目 README 里记录 vendor 版本号（`react@18.3.1` 等），升级时有据可查

**副作用检查**：Babel in-browser 编译时 console 会报「You are using the in-browser Babel transformer」warning——这是**正常的**，不是错误。验证脚本的错误过滤要区分 warning 与 error。

## 字体也要本地化 —— fonts.css 的相对路径陷阱

下载的 webfont 包里 `fonts.css` 的 `url()` 是**相对于 CSS 文件位置**解析的。如果 CSS 在 `assets/fonts/fonts.css` 里写 `url(assets/fonts/xxx.woff2)`，浏览器会去找 `assets/fonts/assets/fonts/xxx.woff2` → 404 → 字体静默 fallback（不报 error，只是字形不对）。

**规则**：把 fonts.css 挪到项目根、或改写其中 url 为**裸文件名**（与 css 同目录）；另外下载时注意长文件名 + 非 ASCII 文件名会被某些下载工具**截断或转码**——下载后必须 `Get-ChildItem` 核对磁盘上真实文件名，与 CSS 引用逐一对上。

## 文件结构

```
项目名/
├── index.html               # 主HTML
├── components.jsx           # 组件文件（type="text/babel"加载）
├── data.js                  # 数据文件
└── styles.css               # 额外CSS（可选）
```

HTML里加载方式：

```html
<!-- 先React+Babel -->
<script src="https://unpkg.com/react@18.3.1/..."></script>
<script src="https://unpkg.com/react-dom@18.3.1/..."></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/..."></script>

<!-- 然后你的组件文件 -->
<script type="text/babel" src="components.jsx"></script>
<script type="text/babel" src="pages.jsx"></script>

<!-- 最后主入口 -->
<script type="text/babel">
  const root = ReactDOM.createRoot(document.getElementById('root'));
  root.render(<App />);
</script>
```

**不要**用`type="module"`——会和Babel冲突。

## 三条不可违反的规矩

### 规矩1：styles 对象必须用唯一命名

**错误**（多组件时必炸）：
```jsx
// components.jsx
const styles = { button: {...}, card: {...} };

// pages.jsx  ← 同名覆盖！
const styles = { container: {...}, header: {...} };
```

**正确**：每个组件文件的styles用唯一前缀。

```jsx
// terminal.jsx
const terminalStyles = { 
  screen: {...}, 
  line: {...} 
};

// sidebar.jsx
const sidebarStyles = { 
  container: {...}, 
  item: {...} 
};
```

**或者用inline styles**（小组件推荐）：
```jsx
<div style={{ padding: 16, background: '#111' }}>...</div>
```

这条是**非协商**的。每次写`const styles = {...}`都必须replace成specific命名，否则多组件加载时全栈报错。

### 规矩2：Scope 不共享，需手动export

**关键认知**：每个`<script type="text/babel">`被Babel独立编译，它们之间**scope不通**。`components.jsx`里定义的`Terminal`组件，在`pages.jsx`里**默认是undefined**。

**解决方式**：在每个组件文件末尾，把要共享的组件/工具export到`window`：

```jsx
// components.jsx 末尾
function Terminal(props) { ... }
function Line(props) { ... }
const colors = { green: '#...', red: '#...' };

Object.assign(window, {
  Terminal, Line, colors,
  // 所有你要在别处用的都列在这里
});
```

然后`pages.jsx`就能直接用`<Terminal />`，因为JSX会去`window.Terminal`找。

### 规矩3：不要用 scrollIntoView

`scrollIntoView`会把整个HTML容器往上推，搞坏web harness的布局。**永远不要用**。

替代方案：
```js
// 滚到容器内某个位置
container.scrollTop = targetElement.offsetTop;

// 或者用element.scrollTo
container.scrollTo({
  top: targetElement.offsetTop - 100,
  behavior: 'smooth'
});
```

## 调 Claude API（HTML内）

部分原生 design-agent 环境（如 Claude.ai Artifacts）有免配置的 `window.claude.complete`，但大部分 agent 环境（Claude Code / Codex / Cursor / Trae / etc.）本地里**没有**。

如果你的 HTML 原型需要调用 LLM 做 demo（比如做个聊天 interface），两个选项：

### 选项A：不真调，用mock

Demo场景推荐。写一个假helper，返回预设的response：
```jsx
window.claude = {
  async complete(prompt) {
    await new Promise(r => setTimeout(r, 800)); // 模拟延迟
    return "这是一个mock响应。真部署时请替换为真API。";
  }
};
```

### 选项B：真调Anthropic API

需要API key，用户必须在HTML里填入自己的key才能跑。**永远不要把key硬编码在HTML里**。

```html
<input id="api-key" placeholder="粘贴你的Anthropic API key" />
<script>
window.claude = {
  async complete(prompt) {
    const key = document.getElementById('api-key').value;
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': key,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5',
        max_tokens: 1024,
        messages: [{ role: 'user', content: prompt }]
      })
    });
    const data = await res.json();
    return data.content[0].text;
  }
};
</script>
```

**注意**：浏览器直接调Anthropic API会遇到CORS问题。如果用户给你的预览环境不支持CORS bypass，这条路不通。这时候用选项A mock，或者告诉用户需要一个proxy后端。

### 选项 C：用 agent 侧的 LLM 能力生成 mock 数据

如果只是本地演示用，可以在当前 agent 会话里临时调用该 agent 的 LLM 能力（或用户装的 multi-model 类 skill）先生成 mock 响应数据，再硬编码写进 HTML。这样 HTML 运行时完全不依赖任何 API。

## 典型 HTML 起手模板

拷贝这个模板作为React原型的骨架：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Prototype Name</title>

  <!-- React + Babel pinned -->
  <script src="https://unpkg.com/react@18.3.1/umd/react.development.js" integrity="sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L" crossorigin="anonymous"></script>
  <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" integrity="sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm" crossorigin="anonymous"></script>
  <script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" integrity="sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y" crossorigin="anonymous"></script>

  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { height: 100%; width: 100%; }
    body { 
      font-family: -apple-system, 'SF Pro Text', sans-serif;
      background: #FAFAFA;
      color: #1A1A1A;
    }
    #root { min-height: 100vh; }
  </style>
</head>
<body>
  <div id="root"></div>

  <!-- 你的组件文件 -->
  <script type="text/babel" src="components.jsx"></script>

  <!-- 主入口 -->
  <script type="text/babel">
    const { useState, useEffect } = React;

    function App() {
      return (
        <div style={{padding: 40}}>
          <h1>Hello</h1>
        </div>
      );
    }

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
```

## 常见报错及解决

**`styles is not defined` 或 `Cannot read property 'button' of undefined`**
→ 你在一个文件里定义了`const styles`，另一个文件覆盖了。给每个改成specific命名。

**`Terminal is not defined`**
→ 跨文件引用时scope不通。在定义Terminal的文件末尾加`Object.assign(window, {Terminal})`。

**整个页面白屏，控制台没错误**
→ 多半是JSX语法错误但Babel没报在控制台。把`babel.min.js`临时换成`babel.js`非压缩版，错误信息更清晰。

**ReactDOM.createRoot is not a function**
→ 版本不对。确认用了react-dom@18.3.1（而不是17或其他）。

**`Objects are not valid as a React child`**
→ 你渲染了一个对象而不是JSX/字符串。通常是`{someObj}`写成了`{someObj.name}`。

## 大项目怎么拆文件

**>1000行的单文件**难维护。分拆思路：

```
项目/
├── index.html
├── src/
│   ├── primitives.jsx      # 基础元素：Button、Card、Badge...
│   ├── components.jsx      # 业务组件：UserCard、PostList...
│   ├── pages/
│   │   ├── home.jsx        # 首页
│   │   ├── detail.jsx      # 详情页
│   │   └── settings.jsx    # 设置页
│   ├── router.jsx          # 简单路由（React state切换）
│   └── app.jsx             # 入口组件
└── data.js                 # mock data
```

HTML里按顺序加载：
```html
<script type="text/babel" src="src/primitives.jsx"></script>
<script type="text/babel" src="src/components.jsx"></script>
<script type="text/babel" src="src/pages/home.jsx"></script>
<script type="text/babel" src="src/pages/detail.jsx"></script>
<script type="text/babel" src="src/pages/settings.jsx"></script>
<script type="text/babel" src="src/router.jsx"></script>
<script type="text/babel" src="src/app.jsx"></script>
```

**每个文件末尾**都要`Object.assign(window, {...})`导出要共享的东西。
