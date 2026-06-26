# jbr-wayland-clipboard-fix

Fixes the JetBrains IDE clipboard bug on **ChromeOS / native Wayland** where text
copied *inside* the IDE pastes back as garbled CJK ("Chinese") characters.
([JBR-7721](https://youtrack.jetbrains.com/issue/JBR-7721))

Works for any JetBrains IDE on the JetBrains Runtime — GoLand, IntelliJ IDEA,
PyCharm, WebStorm, CLion, Rider, RubyMine, PhpStorm. Stays on native Wayland (no
X11 switch). The patch **only activates under ChromeOS's Sommelier**, so it is
harmless on normal GNOME/KDE Wayland.

## Install

Point it at your IDE folder (the one containing `jbr/` and `product-info.json`):

```bash
./install.py ~/.local/share/JetBrains/GoLand
./install.py /opt/pycharm
```

Close the IDE first (a running IDE rewrites its vmoptions on exit). Then restart
it, copy a line, paste it back — clean.

## Uninstall

```bash
./uninstall.py
```

## How it works

The fix is a one-line guard in JBR's `sun.awt.wl.WLDataTransferer`. For each IDE
the installer reads the bundled JBR's source commit from `jbr/release`, downloads
the *matching* `WLDataTransferer.java`, inserts the guard, and compiles a
`--patch-module` overlay with that IDE's own `jbr/bin/javac`. It adds one line to
the IDE's user vmoptions:

```
--patch-module=java.desktop=~/.local/share/jbr-wayland-clipboard-fix/classes
```

Nothing in the IDE install is touched; fully reversible.

## Root cause

`WLDataTransferer` offers `text/plain;charset=UTF-16` among the text formats.
ChromeOS's **Exo** compositor always prefers UTF-16, but JBR fills that format
with **UTF-8 bytes labelled UTF-16** (it never registers a charset for these
dynamic natives, so its send path defaults to UTF-8). Exo decodes them as UTF-16
→ every ASCII pair becomes one CJK codepoint. The patch drops the UTF-16 formats
when running under Sommelier, so Exo falls back to UTF-8 — correct for the IDE
and for other apps (browsers).

The guard:

```java
if (encoding.startsWith("UTF-16") && System.getenv("SOMMELIER_VERSION") != null) continue;
```

## After an IDE/JBR update

Updates replace the runtime and may bump the source commit. Just re-run
`./install.py <ide-folder>`. No-patch fallback meanwhile: paste with
**Ctrl+Shift+V** (paste as plain text).

## Upstream fix

A proper fix for the JetBrains Runtime itself (detect Exo natively from its
`zcr_*` Wayland interfaces and skip UTF-16 only there) is drafted in
[`upstream/`](upstream/) — patch, PR text, and JBR-7721 comment.

## Requirements

`python3`, the IDE's bundled `jbr/bin/javac`, and internet access at install time.
