# Sync the installed Motion Prompt skill from upstream and rebuild the Chinese index.
# Re-applies zh/patch-body.md and zh/patch-description.txt, backs up SKILL.md.
#
# Usage:
#   .\update.ps1            # download + rebuild
#   .\update.ps1 -Check     # compare only, write nothing
#   .\update.ps1 -Offline   # rebuild the index without downloading
param(
    [switch]$Check,
    [switch]$Offline
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

$root = $PSScriptRoot
if (-not $root) { $root = Split-Path -Parent $MyInvocation.MyCommand.Path }

$opts = @()
if ($Check) { $opts += "--check" }
if ($Offline) { $opts += "--offline" }

& node "$root\zh\update.mjs" @opts
exit $LASTEXITCODE
