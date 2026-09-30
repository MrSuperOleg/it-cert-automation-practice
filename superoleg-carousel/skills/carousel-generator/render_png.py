#!/usr/bin/env python3
# coding: utf-8
"""
Render a carousel HTML file as 7 PNG slides (1080x1350, retina 2x → 2160x2700).

Usage:
    python3 render_png.py <html-path> [output-dir]

Args:
    html-path   Path to the intermediate carousel HTML (any location — usually a tempfile).
    output-dir  Optional. Where PNGs go. Defaults to "<html-dir>/<html-stem>_png/".
                In the carousel-generator skill this should be
                "output/{date}_{slug}_png/" so users only ever see PNGs.

Output:
    output-dir/slide_01.png … slide_07.png (one per .slide element).

Requirements (install once per session):
    pip install playwright --break-system-packages --quiet
    python3 -m playwright install chromium
"""
import asyncio
import os
import sys
from pathlib import Path


async def render(html_path: str, out_dir: str | None = None) -> str:
    from playwright.async_api import async_playwright

    html_path = os.path.abspath(html_path)
    if out_dir is None:
        stem = Path(html_path).stem
        out_dir = os.path.join(os.path.dirname(html_path), f"{stem}_png")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": 1180, "height": 1450},
            device_scale_factor=2,
        )
        page = await ctx.new_page()
        await page.goto("file://" + html_path, wait_until="networkidle")
        # Give fonts a beat to fully load
        await page.wait_for_timeout(2500)
        await page.evaluate("document.fonts.ready")
        slides = await page.locator(".slide").element_handles()
        if len(slides) != 7:
            print(
                f"WARN: expected 7 .slide elements, got {len(slides)}",
                file=sys.stderr,
            )
        for i, slide in enumerate(slides, start=1):
            out = os.path.join(out_dir, f"slide_{i:02d}.png")
            await slide.screenshot(path=out, omit_background=False)
            print(f"saved {out}")
        await browser.close()
    return out_dir


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        sys.exit(1)
    html_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) == 3 else None
    out_dir = asyncio.run(render(html_path, out_dir))
    print(f"\nDone. Folder: {out_dir}")


if __name__ == "__main__":
    main()
