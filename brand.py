"""NanoWarden branding: name, teal palette and an original "N" logo, applied to upstream source trees."""
import colorsys, functools, glob, os, re, struct, zlib

NAME = "NanoWarden"
TEAL = 172 / 360  # hue the upstream blue scale is rotated to
GLYPH = [  # unit-square polygons forming an "N": left bar, right bar, diagonal
    [(.28, .25), (.40, .25), (.40, .75), (.28, .75)],
    [(.60, .25), (.72, .25), (.72, .75), (.60, .75)],
    [(.28, .25), (.40, .25), (.72, .75), (.60, .75)],
]


def recolor(hex6):
    """Rotate a blue hex colour (no #) to the teal hue, keeping saturation and lightness."""
    r, g, b = (int(hex6[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if s > .15 and .5 < h < .7:  # only touch blues, leave greys/whites alone
        h = TEAL
    return "".join(f"{round(c * 255):02x}" for c in colorsys.hls_to_rgb(h, l, s * (.8 if h == TEAL else 1)))


def inside(poly, x, y):
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


@functools.cache
def png(size, gray=False):
    """Rounded teal square with a white N, supersampled 4x for smooth edges."""
    rows, n = [], 4
    for py in range(size):
        row = bytearray([0])
        for px in range(size):
            a = g = 0
            for i in range(n * n):
                x, y = (px + (i % n + .5) / n) / size, (py + (i // n + .5) / n) / size
                dx, dy = max(abs(x - .5) - .28, 0), max(abs(y - .5) - .28, 0)
                if dx * dx + dy * dy <= .22 * .22:
                    a += 1
                    g += any(inside(p, x, y) for p in GLYPH)
            t = py / size
            bg = (round(20 - 8 * t), round(184 - 66 * t), round(166 - 60 * t))
            if gray:
                bg = (150,) * 3
            mix = g / a if a else 0
            row += bytes([round(c + (255 - c) * mix) for c in bg]) + bytes([round(255 * a / n / n)])
        rows.append(bytes(row))
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))


def vector():
    d = "".join("M" + " ".join(f"{54 + (x - .5) * 54:.1f},{54 + (y - .5) * 54:.1f}" for x, y in p) + "z" for p in GLYPH)
    return ('<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp"'
            f' android:viewportWidth="108" android:viewportHeight="108"><path android:fillColor="#FFFFFFFF" android:pathData="{d}"/></vector>')


def android(src, sub):
    sub(src, 'translatable="false">Bitwarden</string>', r">Bitwarden<", f">{NAME}<")
    sub(src, 'applicationId = "com.x8bit.bitwarden"', r'(applicationId = "com.x8bit.bitwarden)"', r'\1.nano"')
    sub(src, "val blue500: Color", r"(val blue\d+: Color = Color\(color = 0xFF)([0-9A-Fa-f]{6})", lambda m: m[1] + recolor(m[2]).upper())
    sub(src, 'name="ic_launcher_background"', r"#FF175DDC", "#FF0F766E")
    for f in glob.glob(f"{src}/app/src/*/res/drawable/ic_launcher_[fm]*.xml"):
        open(f, "w").write(vector())


def browser(src, sub):
    sub(src, '"Bitwarden Password Manager"', r'"message": "Bitwarden Password Manager"', f'"message": "{NAME}"')
    sub(src, '"extDesc"', r'("extDesc": \{\s*"message": )"[^"]*"',
        r'\1"Unofficial community build of the open-source Bitwarden client. Not affiliated with Bitwarden Inc."')
    sub(src, "--color-brand-700:", r"(--color-brand-\d+: #)([0-9a-f]{6})", lambda m: m[1] + recolor(m[2]))
    sub(src, "--color-brand-700-rgb", r"23, 93, 220", "15, 118, 110")
    for f in glob.glob(f"{src}/apps/browser/src/images/icon*.png"):
        size = int(re.search(r"icon(\d+)", os.path.basename(f))[1])
        open(f, "wb").write(png(size, gray="gray" in f))
