# Upstream contribution kit (JBR-7721)

Draft of the proper fix for [JetBrainsRuntime](https://github.com/JetBrains/JetBrainsRuntime),
which the local `install.py` overlay works around.

- **`jbr-7721-chromeos-clipboard.patch`** — the change (42 insertions, 3 files):
  - `WLToolkit.c` — detect Exo from its `zcr_*`/`zaura_shell` registry interfaces;
    expose `isExoCompositorImpl()` (mirrors `isSSDAvailableImpl`).
  - `WLToolkit.java` — `isExoCompositor()` accessor.
  - `WLDataTransferer.java` — skip the UTF-16 text natives only under Exo.
- **`PR.md`** — pull-request title/body.
- **`youtrack-comment.md`** — comment to post on JBR-7721 first.

The patch is generated against JBR source commit `aa719f98f3da` (JBR-25.0.3+9).
Apply with:

```bash
git apply jbr-7721-chromeos-clipboard.patch
```

Difference from the local overlay: this detects Exo at the Wayland-protocol level
in native code (canonical), whereas the shipped overlay gates on the
`SOMMELIER_VERSION` env var to avoid a native rebuild.
