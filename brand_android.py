"""Android application identity and ABI versioning."""
import glob, os
import brand_about
from brand_images import vector_badge
NAME = "Bitwarden Patched"

def android(src, sub):
    brand_about.android(src, sub)
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


