"""Create a grey placeholder for every screenshot the guide refers to and that does not exist yet.

    python make_placeholders.py [--main PATH] [--list]

Replace a placeholder by saving the real screenshot under the same file name (PNG, about 1280 px wide).
--list prints the shot list (file name and what it must show) without writing anything.
"""
import argparse
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import main_checkout


def font(size):
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def shots(main):
    for md in sorted((main / "docs" / "guide").glob("*.md")):
        for alt, name in re.findall(r"!\[([^\]]*)\]\(\.\./img/([^)]+)\)", md.read_text(encoding="utf-8")):
            yield md.name, name, alt


def placeholder(path, alt):
    img = Image.new("RGB", (1280, 640), "#eef1f4")
    d = ImageDraw.Draw(img)
    d.rectangle([12, 12, 1267, 627], outline="#9aa5b1", width=3)
    d.text((640, 230), f"Screenshot {path.stem.split('-')[0]}", font=font(54), fill="#5b6672", anchor="mm")
    for i, line in enumerate(textwrap.wrap(alt, 60)):
        d.text((640, 320 + 46 * i), line, font=font(34), fill="#1d2228", anchor="mm")
    d.text((640, 580), f"docs/img/{path.name}", font=font(24), fill="#5b6672", anchor="mm")
    img.save(path, optimize=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--main", type=Path)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    root = args.main or main_checkout()
    for part, name, alt in shots(root):
        target = root / "docs" / "img" / name
        if args.list:
            print(f"{name:<34} {'placeholder/missing' if not target.exists() else 'exists':<20} {alt}   [{part}]")
        elif not target.exists():
            placeholder(target, alt)
            print("created", name)


if __name__ == "__main__":
    main()
