"""Bitwarden Patched branding: the original Bitwarden logo and colours plus a small "fork" badge, applied to upstream source trees."""
import glob, json, os

NAME = "Bitwarden Patched"
PAGES = "https://mkalmousli.github.io/bitwarden-patched"
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


def android(src, sub):
    sub(src, 'translatable="false">Bitwarden</string>', r">Bitwarden<", f">{NAME}<")
    sub(src, 'applicationId = "com.x8bit.bitwarden"', r'(applicationId = "com.x8bit.bitwarden)"', r'\1.patched"')  # installs next to the official app
    for f in glob.glob(f"{src}/app/src/*/res/drawable/ic_launcher_foreground.xml"):
        text = open(f).read()
        open(f, "w").write(text.replace("</vector>", vector_badge() + "</vector>"))
    # One APK per ABI plus a universal one. The version code gets an ABI digit so each can be installed and indexed separately.
    # CI builds one ABI per job (NANO_ABI); without it, all of them plus a universal APK in one go.
    abi = os.environ.get("NANO_ABI", "")
    if abi == "universal":
        splits = ""
    elif abi:
        splits = f'    splits {{ abi {{ isEnable = true; reset(); include("{abi}"); isUniversalApk = false }} }}\n'
    else:
        splits = '    splits { abi { isEnable = true; reset(); include("x86", "x86_64", "armeabi-v7a", "arm64-v8a"); isUniversalApk = true } }\n'
    if splits:
        sub(src, "configure<ApplicationExtension> {", r"(configure<ApplicationExtension> \{\n)", lambda m: m[1] + splits)
    sub(src, "output.outputFileName.set(", r'( *)output\.outputFileName\.set\("\$fileNameWithoutExtension\.apk"\)',
        r'''\1val abi = output.filters.find { it.filterType == com.android.build.api.variant.FilterConfiguration.FilterType.ABI }?.identifier
\1val abiDigit = mapOf("x86" to 1, "x86_64" to 2, "armeabi-v7a" to 3, "arm64-v8a" to 4)[abi] ?: 0
\1output.versionCode.set((output.versionCode.orNull ?: 0) * 10 + abiDigit)
\1output.outputFileName.set("$fileNameWithoutExtension-${abi ?: "universal"}.apk")''')

    # The AAB rename task is per variant, but with ABI splits a variant has several outputs: register it once.
    sub(src, "val renameTaskName =", r'( *)(val renameTaskName = [^\n]*\n)', r'\1\2\1if (renameTaskName in tasks.names) return@forEach\n')


def browser(src, sub):
    sub(src, '"Bitwarden Password Manager"', r'"message": "Bitwarden Password Manager"', f'"message": "{NAME}"')
    sub(src, '"extDesc"', r'("extDesc": \{\s*"message": )"[^"]*"',
        r'\1"Unofficial patched build of the open-source Bitwarden client. Not affiliated with Bitwarden Inc."')
    sub(src, '"__firefox__browser_specific_settings"', r'"id": "\{446900e4-[^}]*\}"',  # own add-on id, so it never collides with the official one
        f'"id": "nanowarden@mkalmousli.github.io", "update_url": "{PAGES}/firefox/updates.json"')
    for f in glob.glob(f"{src}/apps/browser/src/images/icon*.png"):
        stamp(f)


def desktop(src, sub):
    """Own name and app id so it installs next to the official desktop app; no signing, notarising or store packaging."""
    path = f"{src}/apps/desktop/electron-builder.json"
    cfg = json.load(open(path))
    cfg["productName"], cfg["appId"] = NAME, "com.bitwarden.desktop.patched"
    cfg.setdefault("extraMetadata", {})["name"] = "bitwarden-patched"
    cfg["copyright"] = "GPL-3.0. Unofficial build of the Bitwarden desktop app."
    for hook in ("afterSign", "appxManifestCreated", "publish"):
        cfg.pop(hook, None)
    cfg.get("win", {}).pop("signtoolOptions", None)
    cfg.get("win", {}).pop("signExts", None)
    cfg["mac"].update({"identity": None, "hardenedRuntime": False, "gatekeeperAssess": False})
    for key in ("provisioningProfile", "entitlements", "entitlementsInherit"):
        cfg["mac"].pop(key, None)
    for kind in ("appImage", "deb"):
        cfg.setdefault(kind, {})["artifactName"] = "bitwarden-patched-${version}-${arch}.${ext}"
    json.dump(cfg, open(path, "w"), indent=2)
