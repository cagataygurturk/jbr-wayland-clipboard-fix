# PR: Fix garbled clipboard text under the ChromeOS Exo compositor (JBR-7721)

**Branch:** `chromeos-exo-clipboard-utf16`
**Target:** the active JBR 25 development branch (the one bundled JBR-25.0.3+9 is cut from)
**Patch:** `jbr-7721-chromeos-clipboard.patch` (42 insertions, 3 files)

## Summary

On ChromeOS (Crostini → Sommelier → Exo Wayland compositor), text copied inside a
Wayland JBR application and pasted back comes out as garbled CJK ("Chinese")
characters.

`WLDataTransferer.getPlatformMappingsForFlavor` offers a `text/plain` native for
every standard charset, including `text/plain;charset=UTF-16` (and `-LE`/`-BE`).
The Exo compositor *always prefers* the UTF-16 type when it is offered. However,
these dynamically generated text natives are never registered in
`DataTransferer.nativeCharsets`, so the send path
(`translateTransferableString` → `getBestCharsetForTextFormat` →
`getCharsetForTextFormat` → `null`) falls back to `Charset.defaultCharset()`
(UTF-8). The bytes handed to Exo for the `charset=UTF-16` native are therefore
UTF-8, Exo decodes them as UTF-16, and every ASCII pair collapses into one CJK
codepoint.

## Fix

Stop offering the UTF-16 text natives **only when running under Exo**, so the
compositor falls back to `text/plain;charset=UTF-8`, which is serialized
correctly. Behaviour on every other Wayland compositor is unchanged.

Exo is detected in the native registry handler (`registry_global`) from the
aura-shell / Chrome-specific `zcr_*` interfaces it advertises, surfaced to Java
through a new `WLToolkit.isExoCompositor()` (mirroring the existing
`isSSDAvailable()` pattern).

## Why gate it instead of dropping UTF-16 outright

A previous unconditional "drop UTF-16" change was reverted because removing UTF-16
affects **all** Wayland users. Gating on Exo confines the change to the only
compositor that exhibits the bug, so there is no behavioural change for
GNOME/KDE/wlroots users — which should also make it testable to merge without
ChromeOS CI hardware.

## Why not "honor" the UTF-16 charset instead

Encoding to Java's `"UTF-16"` produces UTF-16BE **with a BOM**, but Exo/Chromium
read `charset=utf-16` as native-endian (UTF-16LE on x86) and ignore the BOM, so
honoring the charset would still corrupt cross-application pastes (e.g. into a
browser). Falling back to UTF-8 is correct for every consumer.

## Detection detail

On current ChromeOS, `zaura_shell` is not advertised to Crostini clients, but the
Chrome-specific `zcr_*` interfaces (e.g. `zcr_text_input_crostini_manager_v1`)
are. The detection matches the `zcr_` prefix and `zaura_shell`, verified by
enumerating the Wayland registry on a live ChromeOS/Crostini session.

## Testing

- ChromeOS (Crostini, JBR-25.0.3+9): copy a line in the IDE editor and paste it
  back — correct before/after restart; pasting into a browser field is also
  clean. Confirmed via `wl-paste -t text/plain;charset=utf-8`.
- The same change applied as a `--patch-module` overlay (Exo gate via the
  `zcr_*` registry probe) resolved the bug for GoLand/WebStorm/PyCharm 2026.1.3.
- Non-ChromeOS Wayland: `getPlatformMappingsForFlavor` output is unchanged
  (`isExoCompositor()` returns false), verified by unit check of the offered
  natives.

Fixes: JBR-7721
