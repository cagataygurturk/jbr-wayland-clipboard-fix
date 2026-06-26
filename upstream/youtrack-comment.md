# Comment for JBR-7721

I tracked down the exact mechanism and have a minimal, Exo-gated fix (patch +
PR draft linked below).

**Root cause.** `WLDataTransferer.getPlatformMappingsForFlavor` offers a
`text/plain` native for every standard charset, including
`text/plain;charset=UTF-16`. ChromeOS's Exo compositor always *prefers* UTF-16
when offered. But these dynamically generated text natives are never registered
in `DataTransferer.nativeCharsets`, so the send path
(`translateTransferableString` → `getBestCharsetForTextFormat` →
`getCharsetForTextFormat`) returns `null` and falls back to
`Charset.defaultCharset()` = UTF-8. So the bytes served for the `charset=UTF-16`
native are actually UTF-8; Exo decodes them as UTF-16 and every ASCII pair
becomes one CJK codepoint.

**Why the earlier fix regressed.** Dropping UTF-16 unconditionally changes
behaviour for all Wayland users, so it was reverted. The fix below instead
**gates the change on Exo**, leaving GNOME/KDE/wlroots untouched — which should
also make it safe to merge without ChromeOS CI hardware.

**Exo detection.** Exo advertises Chrome-specific `zcr_*` interfaces in the
registry (on current ChromeOS `zaura_shell` is not exposed to Crostini clients,
but e.g. `zcr_text_input_crostini_manager_v1` is). I detect this in
`registry_global` and surface it as `WLToolkit.isExoCompositor()`, mirroring the
existing `isSSDAvailable()` pattern. Then `getPlatformMappingsForFlavor` skips the
UTF-16 family only when `isExoCompositor()` is true, so Exo falls back to UTF-8.

**Not honoring UTF-16 on purpose:** Java's `"UTF-16"` is BE-with-BOM, but
Exo/Chromium read `charset=utf-16` as native-endian LE and ignore the BOM, so
honoring it would still corrupt cross-app pastes. UTF-8 fallback is correct for
every consumer.

Verified on ChromeOS/Crostini with JBR-25.0.3+9: in-IDE copy/paste and paste into
a browser are both clean; non-ChromeOS offered-natives output is unchanged.

Happy to open the PR against the current dev branch — patch is 42 lines across
`WLToolkit.c`, `WLToolkit.java`, `WLDataTransferer.java`.
