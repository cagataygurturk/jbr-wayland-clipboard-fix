#!/usr/bin/env python3
"""
Fix garbled-CJK clipboard paste in JetBrains IDEs on ChromeOS / native Wayland.
(JBR-7721 — copy text inside the IDE, paste it back, get "Chinese" gibberish.)

Usage:   ./install.py <IDE-install-folder>
Example: ./install.py ~/.local/share/JetBrains/GoLand
         ./install.py /opt/pycharm

The folder is the one containing `jbr/` and `product-info.json`.
Close the IDE first, run this, start it again.  Undo with ./uninstall.py

The patch only activates when the IDE actually runs under ChromeOS's Sommelier
(it checks the SOMMELIER_VERSION env var), so it is harmless on other desktops.
"""
import json, os, re, subprocess, sys, urllib.request
from pathlib import Path

OUT = Path.home() / ".local/share/jbr-wayland-clipboard-fix"   # compiled classes live here
SRC_URL = ("https://raw.githubusercontent.com/JetBrains/JetBrainsRuntime/{commit}"
           "/src/java.desktop/unix/classes/sun/awt/wl/WLDataTransferer.java")

# The fix: stop offering text/plain;charset=UTF-16 *when running under ChromeOS*.
# Exo always picks UTF-16 but JBR fills it with UTF-8 bytes -> garbage. Falling
# back to UTF-8 round-trips correctly. The env check keeps it inert elsewhere.
FIND = "                if (!encoding.equals(charset)) {"
INSERT = ('                if (encoding.startsWith("UTF-16") '
          '&& System.getenv("SOMMELIER_VERSION") != null) continue; '
          '// ChromeOS/Exo clipboard fix (JBR-7721)\n')


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    ide = Path(sys.argv[1]).expanduser().resolve()
    jbr = ide / "jbr"
    if not (jbr / "bin/javac").exists():
        sys.exit(f"No bundled JBR at {jbr} — wrong folder?")

    # 1. exact JBR source commit this runtime was built from (must match).
    release = (jbr / "release").read_text()
    m = re.search(r'SOURCE="\.:git:([0-9a-f]{8,})', release)
    if not m:
        sys.exit(f"Could not read JBR source commit from {jbr}/release")
    commit = m.group(1)

    # 2. this IDE's per-user vmoptions file (from product-info.json).
    info = json.loads((ide / "product-info.json").read_text())
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    vmname = Path(info["launch"][0]["vmOptionsFilePath"]).name      # e.g. goland64.vmoptions
    vmoptions = cfg / "JetBrains" / info["dataDirectoryName"] / vmname

    # 3. download the matching source, apply the patch, compile it.
    src_dir = OUT / "src/sun/awt/wl"
    src_dir.mkdir(parents=True, exist_ok=True)
    (OUT / "classes").mkdir(parents=True, exist_ok=True)
    src_file = src_dir / "WLDataTransferer.java"
    src_file.write_bytes(urllib.request.urlopen(SRC_URL.format(commit=commit)).read())

    code = src_file.read_text()
    if "ChromeOS/Exo clipboard fix" not in code:
        if FIND not in code:
            sys.exit("JBR source layout changed — patch needs updating.")
        src_file.write_text(code.replace(FIND, INSERT + FIND, 1))

    subprocess.run([str(jbr / "bin/javac"),
                    "--patch-module", f"java.desktop={OUT/'src'}",
                    "--add-exports", "java.base/jdk.internal.misc=java.desktop",
                    "-d", str(OUT / "classes"), str(src_file)], check=True)

    # 4. point the IDE at the patched class (replace any previous line first).
    vmoptions.parent.mkdir(parents=True, exist_ok=True)
    lines = vmoptions.read_text().splitlines() if vmoptions.exists() else []
    lines = [l for l in lines if "jbr-wayland-clipboard-fix" not in l]
    lines.append(f"--patch-module=java.desktop={OUT/'classes'}")
    vmoptions.write_text("\n".join(lines) + "\n")

    print(f"Patched {info.get('name', 'IDE')}. Restart it, copy a line, paste it back — clean.")
    print(f"  vmoptions: {vmoptions}")


if __name__ == "__main__":
    main()
