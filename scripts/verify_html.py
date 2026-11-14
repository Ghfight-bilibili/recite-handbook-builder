#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单文件背诵手册的四档冒烟测试。

用法：
  python verify_html.py handbook.html
  python verify_html.py handbook.html --chrome /path/to/chrome-headless-shell --shots shots/

检查：
  - 1280/1024/820/390 四档无横向溢出
  - console error / pageerror 为 0
  - 卡片、part-mark、keys-view、pdf-u 数量
  - 五种模式切换、设置弹窗、全屏按钮是否存在
  - 截图（可选）
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit("需要 playwright：pip install playwright")


async def check_width(browser, url, w, h, shots):
    page = await browser.new_page(viewport={"width": w, "height": h})
    errors = []
    page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    page.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    await page.goto(url, wait_until="load")
    await page.wait_for_timeout(350)

    data = await page.evaluate("""() => ({
      iw: innerWidth,
      sw: document.documentElement.scrollWidth,
      cards: document.querySelectorAll('article.card').length,
      parts: document.querySelectorAll('.part-mark').length,
      keys: document.querySelectorAll('.keys-view').length,
      underlines: document.querySelectorAll('u.pdf-u').length,
      modes: document.querySelectorAll('.seg button[data-mode]').length,
      hasReader: !!document.getElementById('reader'),
      hasSettings: !!document.getElementById('settings')
    })""")
    data["overflow"] = data["sw"] > data["iw"] + 1
    data["errors"] = errors

    if shots:
        shots.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(shots / f"top_{w}.png"))
        # 模式切换
        for mode in ["brief", "blank", "keys", "quiz", "read"]:
            btn = page.locator(f'.seg button[data-mode="{mode}"]')
            if await btn.count():
                await btn.first.click()
                await page.wait_for_timeout(150)
        # 设置
        if await page.locator("#settingsBtn").count():
            await page.locator("#settingsBtn").click()
            await page.wait_for_timeout(200)
            await page.screenshot(path=str(shots / f"settings_{w}.png"))
            if await page.locator("#setClose").count():
                await page.locator("#setClose").click()

    await page.close()
    return data


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--chrome", default="", help="Chrome/headless shell 可执行文件路径")
    ap.add_argument("--shots", default="", help="截图目录")
    ap.add_argument("--widths", default="1280x900,1024x768,820x1180,390x844")
    args = ap.parse_args()

    path = Path(args.html).resolve()
    if not path.exists():
        sys.exit(f"文件不存在: {path}")
    url = path.as_uri()
    shots = Path(args.shots) if args.shots else None

    async with async_playwright() as p:
        launch_kwargs = {"args": ["--no-sandbox"]}
        if args.chrome:
            launch_kwargs["executable_path"] = args.chrome
        try:
            browser = await p.chromium.launch(**launch_kwargs)
        except Exception as e:
            sys.exit(
                "无法启动浏览器。请检查 --chrome 路径，或先安装：\n"
                "  pip install playwright\n"
                "  python -m playwright install chromium\n"
                "国内网络可用 npmmirror 的 chrome-for-testing 包，手动解压后传 --chrome。\n"
                f"原始错误: {e}"
            )

        failed = False
        for item in args.widths.split(","):
            w, h = [int(x) for x in item.lower().split("x")]
            data = await check_width(browser, url, w, h, shots)
            print(f"{w}x{h}: " + json.dumps(data, ensure_ascii=False))
            if data["overflow"] or data["errors"]:
                failed = True

        await browser.close()
        if failed:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
