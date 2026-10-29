#!/usr/bin/env python3
"""Regenerate the F-Droid listing images (icon, feature graphic, promo screenshots) under fdroid/locale/en-US. Needs Pillow."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image, ImageDraw, ImageFont
import brand

OUT = f"{HERE}/locale/en-US"
FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"]
font = lambda n: ImageFont.truetype(next(f for f in FONTS if os.path.exists(f)), n)


def bez(p0, p1, p2, p3, n=24):
    return [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))
            for t in (i / n for i in range(1, n + 1))]


def shield(size):
    """The Bitwarden shield (white, blue left half) with the fork badge, on a transparent square."""
    s = 8
    img = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = size * s / 64
    P = lambda pts: [(x * k, y * k) for x, y in pts]
    outline = [(32, 8), (12, 16), (12, 32)] + bez((12, 32), (12, 44), (20, 51), (32, 56)) + bez((32, 56), (44, 51), (52, 44), (52, 32)) + [(52, 16)]
    d.polygon(P(outline), fill="white")
    left = [(32, 14), (32, 50)] + bez((32, 50), (23, 46), (18, 40), (18, 32)) + [(18, 19)]
    d.polygon(P(left), fill="#175DDC")
    badge = brand.fork_badge(int(size * s * .42))
    img.alpha_composite(badge, (int(size * s * .56), int(size * s * .56)))
    return img.resize((size, size), Image.LANCZOS)


def gradient(w, h, c1="#0b2e3c", c2="#0f766e"):
    g = Image.linear_gradient("L").resize((w, h)).rotate(0)
    return Image.composite(Image.new("RGB", (w, h), c2), Image.new("RGB", (w, h), c1), g)


def centered(d, w, y, text, f, fill):
    d.text(((w - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def card(w, h, title, lines, shield_px, top=.12):
    img = gradient(w, h).convert("RGBA")
    img.alpha_composite(shield(shield_px), ((w - shield_px) // 2, int(h * top)))
    d = ImageDraw.Draw(img)
    y = int(h * top) + shield_px + int(h * .05)
    centered(d, w, y, title, font(int(w * .075)), "white")
    y += int(w * .11)
    for l in lines:
        centered(d, w, y, l, font(int(w * .04)), "#bfe9e3")
        y += int(w * .06)
    return img.convert("RGB")


os.makedirs(f"{OUT}/phoneScreenshots", exist_ok=True)
shield(512).save(f"{OUT}/icon.png")
# The repo icon stays a plain square so F-Droid clients can round it themselves.
g = gradient(512, 512).convert("RGBA")
g.alpha_composite(shield(400), (56, 56))
g.save(f"{HERE}/repo-icon.png")
card(1024, 500, "Bitwarden Patched", ["Unofficial, auto-updated build", "of the open-source Bitwarden app"], 140, .06).save(f"{OUT}/featureGraphic.png")
SHOTS = [("Bitwarden, patched", ["Open-source Bitwarden client", "rebuilt from every release"]),
         ("Smaller APKs", ["One build per CPU type", "arm64, armv7, x86 and x86_64"]),
         ("Side by side", ["Own app id, original logo", "with a fork badge"]),
         ("Updates via F-Droid", ["Pinned signing key", "SHA-256 checksums, source included"])]
for i, (t, ls) in enumerate(SHOTS, 1):
    card(1080, 1920, t, ls, 560, .26).save(f"{OUT}/phoneScreenshots/{i}.png")
