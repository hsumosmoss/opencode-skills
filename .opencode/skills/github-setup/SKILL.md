---
name: github-setup
description: Guide for connecting a local git repository to GitHub, including SSH key generation, git config, remote setup, and troubleshooting. Use when the user wants to push code to GitHub, initialize a repo, or fix git authentication issues.
compatibility: opencode
---

# GitHub 連線設定流程

## 重要觀念

- **Git 本身無法在 GitHub 上開 repository**，必須先到 GitHub 網站手動建立，或使用 GitHub CLI（`gh`）
- 每個專案對應一個 GitHub repo，一個電腦可以同時管理多個專案，各自獨立設定 remote 即可

## 前置條件

- 在 https://github.com 註冊帳號
- 已在 GitHub 上按下 **+ → New repository** 建立好空白 repo

## Step 1：檢查 git 是否已安裝

```bash
git --version
```

## Step 2：設定 git 使用者資訊

```bash
git config user.name "你的GitHub使用者名稱"
git config user.email "你的Email"
```

全域設定（影響所有專案）：
```bash
git config --global user.name "你的GitHub使用者名稱"
git config --global user.email "你的Email"
```

## Step 3：檢查是否已有 SSH key

```bash
ls ~/.ssh/id_ed25519.pub
```

若沒有，產生新的 SSH key：
```bash
ssh-keygen -t ed25519 -C "你的Email"
```
（一路按 Enter 使用預設值即可）

## Step 4：複製 SSH public key

```bash
cat ~/.ssh/id_ed25519.pub
```

輸出內容開頭應為 `ssh-ed25519 AAAA...`。

## Step 5：到 GitHub 加入 SSH key

1. 前往 **https://github.com/settings/ssh/new**
2. Title 隨意填（例如 `My MacBook`）
3. Key 欄位貼上上一步複製的 public key
4. 按 **Add SSH key**

## Step 6：驗證 SSH 連線

先將 GitHub 加入 known_hosts：
```bash
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
```

測試連線：
```bash
ssh -T git@github.com
```
成功會顯示 `Hi xxx! You've successfully authenticated...`

## Step 7：初始化本地專案

若專案尚未有 git：
```bash
git init
git branch -M main
```

若已有 git：
```bash
git branch -M main   # 確保分支名稱是 main
```

## Step 8：加入遠端 repository

```bash
git remote add origin git@github.com:<使用者名稱>/<專案名稱>.git
```

若之前用 HTTPS 已設過 remote，先切換成 SSH：
```bash
git remote set-url origin git@github.com:<使用者名稱>/<專案名稱>.git
```

## Step 9：加入檔案並提交

```bash
git add .
git commit -m "Initial commit"
```

## Step 10：推送到 GitHub

```bash
git push -u origin main
```

後續推送只需：
```bash
git push
```

## 查看 remote 網址

不需開瀏覽器，直接在本機查：
```bash
git remote -v
```

或看 `.git/config` 檔案：
```bash
cat .git/config
```

## 不同專案推到不同 repo

每個專案各自初始化即可，互不影響：

```bash
cd /path/to/專案A
git init && git remote add origin git@github.com:<帳號>/專案A.git
# ...

cd /path/to/專案B
git init && git remote add origin git@github.com:<帳號>/專案B.git
# ...
```

若不小心設錯 remote，直接改：
```bash
git remote set-url origin git@github.com:<帳號>/正確的專案.git
```

## 使用 GitHub CLI 開 repo（不需開網頁）

安裝 GitHub CLI：
```bash
brew install gh
```

登入：
```bash
gh auth login
```

建立 repo 並推送（一氣呵成）：
```bash
gh repo create 專案名稱 --public --push
```

## 常見問題

### Host key verification failed

尚未將 GitHub 加入 known_hosts：
```bash
ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
```

### Permission denied (publickey)

SSH key 未正確加入 GitHub 帳號。重複 Step 4 和 Step 5。

### Repository not found

請確認：
- repository 名稱拼寫正確
- remote URL 格式正確：`git@github.com:<帳號>/<專案>.git`

### already exists

```bash
# 覆蓋遠端（僅首次推送需要）
git push -u origin main --force

# 或先 pull 再 push
git pull origin main --allow-unrelated-histories
git push
```

### 使用 HTTPS + Personal Access Token（替代方案）

若不想用 SSH，可用 HTTPS + token：
1. 前往 **https://github.com/settings/tokens** → Generate new token (classic)
2. Scope 勾選 **repo**
3. 複製 token
4. 推送時以 token 作為密碼：
```bash
git remote set-url origin https://github.com/<帳號>/<專案>.git
git push
# username: 你的帳號
# password: 貼上 token
```

但 SSH 是推薦方式，一次設定永久使用。
