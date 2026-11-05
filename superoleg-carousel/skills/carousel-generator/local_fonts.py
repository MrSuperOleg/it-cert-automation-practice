# coding: utf-8
"""
Отдаёт Google Fonts из локальной папки fonts/ вместо сети.

В облачной среде headless Chromium не достаёт fonts.googleapis.com /
fonts.gstatic.com, и слайды рендерятся системными шрифтами. Шаблон не
меняем: перехватываем запросы к Google Fonts и отвечаем локальными файлами.

fonts/google.css — CSS, который Google отдаёт по ссылке из шаблона.
fonts/<путь_после_/s/ с заменой / на _> — сами файлы шрифтов.
Если нужного файла нет локально — запрос уходит в сеть как обычно.
"""
from pathlib import Path

FONTS_DIR = Path(__file__).resolve().parents[2] / "fonts"
CORS = {"Access-Control-Allow-Origin": "*"}


async def use_local_fonts(page) -> None:
    if not FONTS_DIR.is_dir():
        return

    async def css(route):
        path = FONTS_DIR / "google.css"
        if not path.exists():
            return await route.continue_()
        await route.fulfill(path=str(path), content_type="text/css", headers=CORS)

    async def font(route):
        name = route.request.url.split("fonts.gstatic.com/s/", 1)[-1].split("?")[0]
        path = FONTS_DIR / name.replace("/", "_")
        if not path.exists():
            return await route.continue_()
        await route.fulfill(path=str(path), content_type="font/ttf", headers=CORS)

    await page.route("https://fonts.googleapis.com/**", css)
    await page.route("https://fonts.gstatic.com/**", font)
