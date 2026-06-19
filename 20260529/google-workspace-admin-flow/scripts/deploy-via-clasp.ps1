<#
.SYNOPSIS
  用 clasp 一鍵部署行政專案工作流到 Apps Script
.DESCRIPTION
  自動建立 Apps Script 專案、推送 Code.gs 與 appsscript.json、執行 installFlow
.PARAMETER Title
  Apps Script 專案名稱
.PARAMETER SourceDir
  含 Code.gs 與 appsscript.json 的目錄（預設 ./build）
.EXAMPLE
  .\deploy-via-clasp.ps1 -Title "行政專案工作流" -SourceDir .\build
#>

param(
  [string]$Title = "行政專案工作流",
  [string]$SourceDir = ".\build"
)

$ErrorActionPreference = 'Stop'

function Assert-Command($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "找不到指令：$name。請先安裝。"
  }
}

# 前置檢查
Write-Host "🔍 檢查環境..." -ForegroundColor Cyan
Assert-Command 'node'
Assert-Command 'npm'

# 確認 clasp 已安裝
if (-not (Get-Command 'clasp' -ErrorAction SilentlyContinue)) {
  Write-Host "📦 安裝 @google/clasp..." -ForegroundColor Yellow
  npm install -g @google/clasp
}

# 確認已登入
$loginStatus = clasp login --status 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Host "🔑 需要登入 Google 帳號..." -ForegroundColor Yellow
  clasp login
}

# 檢查來源檔案
$codePath = Join-Path $SourceDir 'Code.gs'
$manifestPath = Join-Path $SourceDir 'appsscript.json'

if (-not (Test-Path $codePath)) {
  throw "找不到 $codePath。先執行 generate-code.mjs 產出 Code.gs。"
}

if (-not (Test-Path $manifestPath)) {
  $defaultManifest = Resolve-Path (Join-Path $PSScriptRoot '..\templates\appsscript.json')
  Write-Host "📋 複製預設 appsscript.json..." -ForegroundColor Yellow
  Copy-Item $defaultManifest $manifestPath
}

# 建立 Apps Script 專案
Write-Host "🆕 建立 Apps Script 專案：$Title" -ForegroundColor Cyan
Push-Location $SourceDir

try {
  clasp create --type standalone --title $Title --rootDir .

  Write-Host "⬆️  推送程式碼..." -ForegroundColor Cyan
  clasp push --force

  Write-Host "▶️  執行 installFlow..." -ForegroundColor Cyan
  Write-Host "   (clasp run 可能要等 1-3 分鐘)" -ForegroundColor Gray
  $output = clasp run installFlow 2>&1

  Write-Host ""
  Write-Host "✅ 部署完成！" -ForegroundColor Green
  Write-Host ""
  Write-Host "執行結果：" -ForegroundColor Cyan
  Write-Host $output

  $scriptUrl = (clasp open --no-localhost 2>&1) -join ''
  Write-Host ""
  Write-Host "🔗 Apps Script 編輯器：" -ForegroundColor Cyan
  Write-Host "   (執行 clasp open 開啟)" -ForegroundColor Gray

} catch {
  Write-Host "❌ 部署失敗：$_" -ForegroundColor Red
  Write-Host ""
  Write-Host "備援方案：" -ForegroundColor Yellow
  Write-Host "  1. 開 https://script.google.com 手動建立專案"
  Write-Host "  2. 把 $codePath 貼到編輯器"
  Write-Host "  3. 執行 installFlow()"
  throw
} finally {
  Pop-Location
}
