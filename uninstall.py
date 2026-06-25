#!/usr/bin/env python3
"""Undo install.py: remove the patch line from every JetBrains vmoptions file."""
import os, shutil
from pathlib import Path

cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "JetBrains"
for vmo in cfg.glob("*/*.vmoptions"):
    lines = vmo.read_text().splitlines()
    kept = [l for l in lines if "jbr-wayland-clipboard-fix" not in l]
    if kept != lines:
        vmo.write_text("\n".join(kept) + ("\n" if kept else ""))
        print(f"cleaned {vmo}")

shutil.rmtree(Path.home() / ".local/share/jbr-wayland-clipboard-fix", ignore_errors=True)
print("Done. Restart any running IDE.")
