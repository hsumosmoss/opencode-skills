param([switch]$Force)

$ErrorActionPreference = 'Stop'
Write-Host "=== video-maker 環境設定 ===" -ForegroundColor Cyan

# 1. Python + edge-tts
Write-Host "`n[1/4] Python + edge-tts" -ForegroundColor Yellow
python --version
pip install --quiet edge-tts
Write-Host "  OK edge-tts"

# 2. 字體：源石黑體
Write-Host "`n[2/4] 字體：源石黑體 GenSekiGothic2TW" -ForegroundColor Yellow
$FontsDir = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
$Upstream = "https://github.com/ButTaiwan/genseki-font/raw/master/TW"
foreach ($f in @("GenSekiGothic2TW-H.otf","GenSekiGothic2TW-B.otf","GenSekiGothic2TW-M.otf")) {
    $dest = "$FontsDir\$f"
    if ((Test-Path $dest) -and -not $Force) {
        Write-Host "  OK $f"
    } else {
        Write-Host "  DOWNLOAD $f"
        Invoke-WebRequest -Uri "$Upstream/$f" -OutFile $dest
    }
}

# 3. Node.js + Playwright（裝在 %TEMP% 避開同步問題）
Write-Host "`n[3/4] Playwright（%TEMP%/cvs-render）" -ForegroundColor Yellow
$WorkDir = "$env:TEMP\cvs-render"
if (-not (Test-Path "$WorkDir\package.json")) {
    New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
    Push-Location $WorkDir
    npm init -y | Out-Null
    Pop-Location
}
if ((Test-Path "$WorkDir\node_modules\playwright") -and -not $Force) {
    Write-Host "  OK playwright"
} else {
    Push-Location $WorkDir
    npm install playwright
    npx playwright install chromium
    Pop-Location
    Write-Host "  OK playwright installed"
}

# 4. ffmpeg 檢查（不自動裝，提示手動）
Write-Host "`n[4/4] ffmpeg" -ForegroundColor Yellow
try {
    ffmpeg -version | Out-Null
    Write-Host "  OK ffmpeg"
} catch {
    Write-Host "  MISS ffmpeg — 請自行安裝：" -ForegroundColor Red
    Write-Host "    winget install "FFmpeg (Essentials Build)""
    Write-Host "    或下載 https://www.gyan.dev/ffmpeg/builds/"
}

Write-Host "`n=== 就緒 ===" -ForegroundColor Green
Write-Host "在專案目錄下執行指令後，複製 scripts/ 內的檔案到專案開始使用。"