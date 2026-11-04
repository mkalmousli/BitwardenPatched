"""Bitwarden Patched branding: the original Bitwarden logo and colours plus a small "fork" badge, applied to upstream source trees."""
import glob, json, os

NAME = "Bitwarden Patched"
PAGES = "https://mkalmousli.github.io/BitwardenPatched"
TEAL = "0F766E"  # badge colour
# Fork glyph in a unit square centred on the badge: three nodes joined by a branching line.
NODES = [(-.26, -.30), (.26, -.30), (0, .32)]
LINES = [[(-.26, -.30), (-.26, -.08), (0, .08), (0, .32)], [(.26, -.30), (.26, -.08), (0, .08)]]


def fork_badge(size):
    """RGBA fork badge image, drawn 8x and downsampled."""
    from PIL import Image, ImageDraw
    big = size * 8
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, big - 1, big - 1], fill="white")
    d.ellipse([big * .07, big * .07, big * .93, big * .93], fill="#" + TEAL)
    pt = lambda p: (big * (.5 + p[0] * .8), big * (.5 + p[1] * .8))
    for line in LINES:
        d.line([pt(p) for p in line], fill="white", width=max(int(big * .08), 2), joint="curve")
    for p in NODES:
        x, y = pt(p)
        r = big * .105
        d.ellipse([x - r, y - r, x + r, y + r], fill="#" + TEAL, outline="white", width=max(int(big * .06), 2))
    return img.resize((size, size), Image.LANCZOS)


def stamp(path):
    """Overlay the fork badge on the bottom-right corner of an upstream PNG icon."""
    from PIL import Image
    icon = Image.open(path).convert("RGBA")
    badge = fork_badge(max(round(icon.width * .5), 8))
    icon.alpha_composite(badge, (icon.width - badge.width, icon.height - badge.height))
    icon.save(path)


def vector_badge():
    """Android vector group drawing the same badge at the bottom-right of the 108dp adaptive-icon canvas."""
    cx, cy, r = 77, 77, 13
    pt = lambda p: (cx + p[0] * r * 1.6, cy + p[1] * r * 1.6)
    ri = r - 1.6
    out = [f'<path android:fillColor="#FFFFFFFF" android:pathData="M{cx - r},{cy}a{r},{r} 0 1,0 {2 * r},0a{r},{r} 0 1,0 {-2 * r},0z"/>',
           f'<path android:fillColor="#FF{TEAL}" android:pathData="M{cx - ri:.1f},{cy}a{ri:.1f},{ri:.1f} 0 1,0 {2 * ri:.1f},0a{ri:.1f},{ri:.1f} 0 1,0 {-2 * ri:.1f},0z"/>']
    for line in LINES:
        d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in map(pt, line))
        out.append(f'<path android:pathData="{d}" android:strokeColor="#FFFFFFFF" android:strokeWidth="1.8" '
                   'android:strokeLineCap="round" android:strokeLineJoin="round"/>')
    for p in NODES:
        x, y = pt(p)
        out.append(f'<path android:fillColor="#FF{TEAL}" android:strokeColor="#FFFFFFFF" android:strokeWidth="1.5" '
                   f'android:pathData="M{x - 2.4:.1f},{y:.1f}a2.4,2.4 0 1,0 4.8,0a2.4,2.4 0 1,0 -4.8,0z"/>')
    return "<group>" + "".join(out) + "</group>"


