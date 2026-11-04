"""Visible patch attribution in the upstream clients' About screens."""
REPO = 'https://github.com/mkalmousli/BitwardenPatched'
NOTICE = 'Unofficial patch of Bitwarden. Client-side premium checks enabled. Not affiliated with Bitwarden Inc.'


def android(src, sub):
    content = '''        val patchUriHandler = androidx.compose.ui.platform.LocalUriHandler.current
        Text(
            text = "Bitwarden Patched — NOTICE",
            modifier = Modifier.standardHorizontalMargin(),
        )
        androidx.compose.material3.TextButton(
            onClick = { patchUriHandler.openUri("REPO") },
        ) { Text("Patch source and changes") }
'''.replace('NOTICE', NOTICE).replace('REPO', REPO)
    sub(src, 'isVisible = state.shouldShowCrashLogsButton,', r'        CrashLogsCard\(\n',
        lambda match: content + match[0])


def browser(src, sub):
    content = (f'<p>{NOTICE}</p>\n'
               f'<p><a href="{REPO}" target="_blank" rel="noopener noreferrer">'
               'Patch source and changes</a></p>\n')
    sub(src, '<div bitDialogTitle>Bitwarden</div>',
        r'<div bitDialogTitle>Bitwarden</div>', '<div bitDialogTitle>Bitwarden Patched</div>')
    sub(src, '<div bitDialogTitle>Bitwarden Patched</div>', r'(<div bitDialogContent>)', lambda match: match[0] + content)


def desktop(src, sub):
    anchor = 'const aboutInformation ='
    sub(src, anchor, r'(const aboutInformation =\s*\n)',
        lambda match: match[0] + f'          "{NOTICE}\\n{REPO}\\n\\n" +\n')
    sub(src, anchor, r'(title|message): productName', lambda match: f'{match[1]}: "Bitwarden Patched (" + productName + ")"')
    sub(src, anchor, r'buttons: \[this.localize\("ok"\), this.localize\("copy"\)\]',
        'buttons: [this.localize("ok"), this.localize("copy"), "Patch repository"]')
    sub(src, anchor, r'if \(result.response === 1\) \{',
        lambda match: f'if (result.response === 2) {{ await shell.openExternal("{REPO}"); }}\n        ' + match[0])
    sub(src, anchor, r'import \{ BrowserWindow, clipboard, dialog,',
        'import { BrowserWindow, clipboard, dialog, shell,')
