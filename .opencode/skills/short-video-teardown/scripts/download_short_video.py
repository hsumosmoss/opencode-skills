#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
短影音下載工具（抖音 / TikTok / Instagram Reels）。

使用 yt-dlp + cookies 下載影片。
抖音支援短链、分享链接、页面链接、从分享文本中提取URL；
TikTok / Reels 直接傳頁面連結。

Usage:
    uv run download_short_video.py --urls "https://v.douyin.com/xxx" "https://www.tiktok.com/@user/video/123"
    uv run download_short_video.py --urls "7.56 复制打开抖音，看看【某某的作品】 https://v.douyin.com/xxx"
    uv run download_short_video.py --output-dir /path/to/output
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DOUYIN_HOSTS = ('v.douyin.com', 'www.douyin.com', 'www.iesdouyin.com')
TIKTOK_HOSTS = ('www.tiktok.com', 'vm.tiktok.com', 'm.tiktok.com')
REELS_HOSTS = ('www.instagram.com',)


def is_douyin(url: str) -> bool:
    return any(h in url for h in DOUYIN_HOSTS)


def clear_proxy_for_china_sites():
    """清除代理环境变量，避免国内站点（抖音）走代理导致失败。"""
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY',
                  'all_proxy', 'ALL_PROXY']
    cleared = []
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
            cleared.append(var)
    if cleared:
        print(f"  已清除代理环境变量: {', '.join(cleared)}", file=sys.stderr)


def extract_urls(texts: list[str]) -> list[str]:
    """从文本列表中提取影片URL。支持短链、页面链接、分享文本中的URL。"""
    url_pattern = re.compile(
        r'https?://(?:'
        + '|'.join(re.escape(h) for h in (DOUYIN_HOSTS + TIKTOK_HOSTS + REELS_HOSTS))
        + r')[^\s\'"<>]*'
    )
    urls = []
    for text in texts:
        text = text.strip()
        if re.match(r'^https?://', text):
            host_ok = any(h in text for h in (DOUYIN_HOSTS + TIKTOK_HOSTS + REELS_HOSTS))
            if host_ok:
                # 抖音长链接去参数；其余原样
                urls.append(text.split('?')[0] if 'www.douyin.com/video/' in text else text)
        else:
            found = url_pattern.findall(text)
            urls.extend(found)
    return urls


def extract_video_id(url: str) -> str:
    """尝试从URL中提取视频ID。"""
    # 抖音长链接：www.douyin.com/video/7xxxxxxxxx
    match = re.search(r'douyin\.com/video/(\d+)', url)
    if match:
        return match.group(1)
    # TikTok：tiktok.com/@user/video/123
    match = re.search(r'tiktok\.com/@[^/]+/video/(\d+)', url)
    if match:
        return match.group(1)
    # 短链接等无法直接提取，用URL hash
    return re.sub(r'[^\w]', '', url)[-12:]


def download_video(url: str, output_dir: Path, index: int, cookies_browser: str) -> dict:
    """用 yt-dlp 下载单个影片。"""
    video_id = extract_video_id(url)
    prefix = 'douyin' if is_douyin(url) else 'short'
    output_template = str(output_dir / f"{prefix}-{index}-{video_id}.%(ext)s")

    cmd = [
        "yt-dlp",
        "--cookies-from-browser", cookies_browser,
        "--output", output_template,
        "--no-warnings",
        "--no-check-certificates",
        url
    ]
    # 抖音（国内站点）强制不走代理
    if is_douyin(url):
        cmd[cmd.index("--no-warnings"):cmd.index("--no-warnings")] = ["--proxy", ""]

    print(f"  [{index}] 下载中: {url}", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or "未知错误"
            if "cookies" in error_msg.lower() or "login" in error_msg.lower():
                error_msg = f"需要登录Cookie: {error_msg[:200]}"
            elif "not found" in error_msg.lower() or "unavailable" in error_msg.lower():
                error_msg = f"视频不存在或已删除: {error_msg[:200]}"
            print(f"  [{index}] 下载失败: {error_msg}", file=sys.stderr)
            return {"url": url, "success": False, "error": error_msg}

        downloaded = list(output_dir.glob(f"{prefix}-{index}-{video_id}.*"))
        video_files = [f for f in downloaded if f.suffix.lower() in ('.mp4', '.webm', '.mkv', '.flv')]

        if video_files:
            file_path = str(video_files[0])
            size_mb = video_files[0].stat().st_size / (1024 * 1024)
            print(f"  [{index}] 下载成功: {video_files[0].name} ({size_mb:.1f}MB)", file=sys.stderr)
            return {"url": url, "success": True, "path": file_path, "size_mb": round(size_mb, 1)}
        else:
            print(f"  [{index}] 下载完成但未找到视频文件", file=sys.stderr)
            return {"url": url, "success": False, "error": "下载完成但未找到视频文件"}

    except subprocess.TimeoutExpired:
        print(f"  [{index}] 下载超时（180秒）", file=sys.stderr)
        return {"url": url, "success": False, "error": "下载超时（180秒）"}
    except FileNotFoundError:
        print(f"  [{index}] 未找到yt-dlp，请安装: pip install yt-dlp 或 brew install yt-dlp", file=sys.stderr)
        return {"url": url, "success": False, "error": "未安装yt-dlp"}


def main():
    parser = argparse.ArgumentParser(description="短影音下载工具（抖音/TikTok/Reels）")
    parser.add_argument(
        "--urls", "-u", nargs="+", required=True,
        help="影片URL（1-5个），抖音支持短链/分享文本，TikTok/Reels 传页面链接"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=str(Path.cwd() / "_temp" / "short-video-downloads"),
        help="输出目录（默认：当前目录/_temp/short-video-downloads/）"
    )
    parser.add_argument(
        "--cookies-browser", "-c", default="chrome",
        help="从哪个浏览器提取cookies（默认：chrome）"
    )

    args = parser.parse_args()

    urls = extract_urls(args.urls)
    if not urls:
        print("错误：未从输入中提取到有效的影片URL", file=sys.stderr)
        print("支持的格式：", file=sys.stderr)
        print("  - https://v.douyin.com/xxx（抖音短链）", file=sys.stderr)
        print("  - https://www.douyin.com/video/123（抖音页面链接）", file=sys.stderr)
        print("  - https://www.tiktok.com/@user/video/123（TikTok）", file=sys.stderr)
        print("  - https://www.instagram.com/reel/xxx（Reels）", file=sys.stderr)
        print("  - 分享文本（包含URL的文本）", file=sys.stderr)
        sys.exit(1)

    if len(urls) > 5:
        print(f"警告：输入了{len(urls)}个URL，仅处理前5个", file=sys.stderr)
        urls = urls[:5]

    # 抖音等国内站点不走代理
    if any(is_douyin(u) for u in urls):
        clear_proxy_for_china_sites()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"准备下载 {len(urls)} 个视频到 {output_dir}", file=sys.stderr)
    print(f"使用 {args.cookies_browser} 浏览器Cookie", file=sys.stderr)
    print("", file=sys.stderr)

    results = []
    for i, url in enumerate(urls, 1):
        result = download_video(url, output_dir, i, args.cookies_browser)
        results.append(result)

    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count

    print("", file=sys.stderr)
    print(f"下载完成：{success_count} 成功，{fail_count} 失败", file=sys.stderr)

    if fail_count > 0:
        print("", file=sys.stderr)
        print("下载失败的视频可以尝试：", file=sys.stderr)
        print("  1. 确认浏览器已登录对应平台（抖音/TikTok/Instagram）", file=sys.stderr)
        print("  2. 使用 --cookies-browser edge/firefox 切换浏览器", file=sys.stderr)
        print("  3. 手动下载视频后放入输出目录", file=sys.stderr)

    output = {
        "total": len(results),
        "success": success_count,
        "failed": fail_count,
        "output_dir": str(output_dir),
        "results": results
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
