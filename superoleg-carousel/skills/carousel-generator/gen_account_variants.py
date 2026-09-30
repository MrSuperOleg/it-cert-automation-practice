#!/usr/bin/env python3
# coding: utf-8
"""
Генерирует варианты слайдов 1 и 7 для дополнительных аккаунтов.

Запускается ПОСЛЕ основного рендера карусели @dengi_s_olegom.

Usage:
    python3 gen_account_variants.py <html-path> <output-dir>

Args:
    html-path   Путь к временному HTML карусели (тот же, что передаётся в render_png.py)
    output-dir  Папка с основными PNG (output/{дата}_{slug}_png/)

Output (в той же output-dir):
    slide_01_dengi_oleg.png     slide_07_dengi_oleg.png
    slide_01_oleg_capital.png   slide_07_oleg_capital.png

Requirements:
    pip install playwright --break-system-packages --quiet
    python3 -m playwright install chromium
    (устанавливается один раз за сессию, уже выполнено render_png.py)
"""
import asyncio
import os
import sys
from pathlib import Path

# Дополнительные аккаунты: (handle, rubric, slug)
ACCOUNTS = [
    ("@dengi_oleg",   "Финансы · Капитал", "dengi_oleg"),
    ("@oleg_capital", "Финансы · Капитал", "oleg_capital"),
]

MAIN_HANDLE = "@dengi_s_olegom"
MAIN_RUBRIC = "Финансы · Капитал"


def make_variant_html(original_html: str, handle: str, rubric: str) -> str:
    """Заменяет хэндл и рубрику в brand-head секциях (слайды 1 и 7) и в cta-button."""
    html = original_html
    # Замена имени аккаунта в brand-head
    html = html.replace(
        f'<div class="name">{MAIN_HANDLE}</div>',
        f'<div class="name">{handle}</div>'
    )
    # Замена хэндла в кнопке CTA (слайд 7)
    html = html.replace(
        f'Подписаться · {MAIN_HANDLE}',
        f'Подписаться · {handle}'
    )
    # Замена рубрики (только если отличается)
    if rubric != MAIN_RUBRIC:
        html = html.replace(
            f'<div class="rubric">{MAIN_RUBRIC}</div>',
            f'<div class="rubric">{rubric}</div>'
        )
    return html


async def render_slides(html_path: str, out_dir: str, handle: str, rubric: str, slug: str):
    """Рендерит slide_01 и slide_07 для одного аккаунта."""
    from playwright.async_api import async_playwright

    with open(html_path) as f:
        original = f.read()

    variant_html = make_variant_html(original, handle, rubric)

    # Пишем во временный файл рядом с оригиналом
    tmp_path = html_path.replace(".html", f"_{slug}.html")
    with open(tmp_path, "w") as f:
        f.write(variant_html)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": 1180, "height": 1450},
            device_scale_factor=2,
        )
        page = await ctx.new_page()
        await page.goto("file://" + os.path.abspath(tmp_path), wait_until="networkidle")
        await page.wait_for_timeout(2500)
        await page.evaluate("document.fonts.ready")

        slides = await page.locator(".slide").element_handles()
        if len(slides) != 7:
            print(f"WARN: ожидали 7 слайдов, получили {len(slides)}", file=sys.stderr)

        # Рендерим только слайд 1 и слайд 7
        for idx in [0, 6]:
            if idx < len(slides):
                slide_num = idx + 1
                out_path = os.path.join(out_dir, f"slide_{slide_num:02d}_{slug}.png")
                await slides[idx].screenshot(path=out_path, omit_background=False)
                print(f"saved {out_path}")

        await browser.close()

    # Удаляем временный HTML варианта
    os.remove(tmp_path)


async def main_async(html_path: str, out_dir: str):
    for handle, rubric, slug in ACCOUNTS:
        print(f"\n--- {handle} ({slug}) ---")
        await render_slides(html_path, out_dir, handle, rubric, slug)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    html_path = os.path.abspath(sys.argv[1])
    out_dir = os.path.abspath(sys.argv[2])

    if not os.path.exists(html_path):
        print(f"Ошибка: HTML не найден: {html_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(out_dir):
        print(f"Ошибка: output-dir не найден: {out_dir}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(main_async(html_path, out_dir))
    print(f"\nГотово. Варианты сохранены в: {out_dir}")


if __name__ == "__main__":
    main()
