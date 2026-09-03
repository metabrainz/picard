# Environment Variables

This document lists the environment variables that influence MusicBrainz
Picard, both at runtime and when building it.

Most `PICARD_*` variables are intended for debugging, providing workarounds,
enabling special setups, or for experimental behavior. They are **not** a
stable configuration interface: they may be changed, removed, or replaced by a
proper option at any time.

Boolean variables are parsed by `picard.env.parse_bool_env()`. It accepts
(case-insensitively, ignoring surrounding whitespace):

- Truthy: `1`, `true`, `yes`, `on`
- Falsy: `0`, `false`, `no`, `off`, empty string

Unset or unrecognized values fall back to the documented default.

## Runtime variables

These affect a running Picard instance.

| Variable | Type | Default | Description |
| --- | --- | --- | --- |
| `PICARD_DEBUG` | presence | unset | Enable debug logging when set (any value), equivalent to the `--debug` command line option. |
| `PICARD_MODAL_OPTIONS` | boolean | platform-dependent (modal on macOS, non-modal elsewhere) | Force the Options dialog to be modal (truthy) or non-modal (falsy). |
| `PICARD_FORCE_FUSION` | boolean | `false` | Force the Qt "Fusion" style on every platform, including macOS and Haiku, which otherwise keep their native style. Mainly useful on macOS; no visible effect where Fusion is already the default. |
| `PICARD_COLLATOR` | `qt`, `strxfrm` or `string` | `strxfrm` on Windows, `qt` elsewhere | Select the string collation backend used for sorting. An unrecognized value falls back to the default. |
| `PICARD_CONFIG_DIR` | path | OS application config location | Override the directory used to store the configuration. |
| `PICARD_CACHE_DIR` | path | OS cache location | Override the directory used for caches. |
| `PICARD_PLUGIN_DIR` | path | `<appdata>/plugins3` | Override the directory used for version 3 plugins. |
| `PICARD_PLUGIN_REGISTRY_URL` | URL | built-in registry list (`DEFAULT_PLUGIN_REGISTRY_URLS`) | Override the plugin registry with a single URL used to discover plugins. |

## Build variables

These are read by the build tooling (`setup.py`, `picard.spec`) and packaging
scripts, not by Picard at runtime.

| Variable | Type | Default | Description |
| --- | --- | --- | --- |
| `PICARD_BUILD_PORTABLE` | boolean | `false` | Build a portable Windows package (PyInstaller). |
| `PICARD_DISABLE_AUTOUPDATE` | boolean | `false` | Disable the built-in auto-update mechanism at build time (see PICARD-3003). |
| `PICARD_APPX_PUBLISHER` | string | fixed MetaBrainz publisher string | Publisher identity used when building the Windows Store (APPX) package. |
| `TARGET_ARCH` | string | unset | Target architecture passed to PyInstaller. |
| `CODESIGN_IDENTITY` | string | unset | macOS code signing identity passed to PyInstaller. |
| `MACOSX_DEPLOYMENT_TARGET` | string | `11.0` | Standard macOS toolchain variable (not Picard-specific): sets the minimum macOS version targeted by the compiler/linker, which can change the produced binaries (e.g. avoiding newer APIs). Picard's PyInstaller config additionally uses it to set `LSMinimumSystemVersion` in the app bundle. |

The packaging scripts under `scripts/pyinstaller/` also *set* some of the
runtime `PICARD_*` variables above (e.g. `PICARD_CONFIG_DIR`,
`PICARD_CACHE_DIR`, `PICARD_PLUGIN_DIR`) to relocate data for portable builds.

## Developer / tooling variables

Used by helper scripts, not by Picard itself.

| Variable | Type | Description |
| --- | --- | --- |
| `WEBLATE_API_KEY` | string | API key used by translation helper scripts. |
| `GITHUB_TOKEN` | string | Token used by release/authorship helper scripts. |
| `CI` | presence | Set by CI systems; used to skip tests that require a display. |

## Third-party variables

Picard also honors a number of standard environment variables provided by the
operating system and its libraries. These are not defined by Picard; refer to
the relevant documentation for details.

- **Qt** (e.g. `QT_QPA_PLATFORM`, `QT_QPA_PLATFORMTHEME`, `QT_SCALE_FACTOR`,
  and other `QT_*` variables): see the
  [Qt environment variable reference](https://doc.qt.io/qt-6/qguiapplication.html#supported-command-line-options)
  and [Qt platform documentation](https://doc.qt.io/qt-6/qpa.html).
- **C library / locale** (`LANG`, `LC_ALL`, and other `LC_*` variables):
  see your platform's locale documentation (e.g. `man 7 locale` on Linux).
- **XDG / desktop** (`XDG_CURRENT_DESKTOP`, `XDG_SESSION_DESKTOP`,
  `XDG_SESSION_TYPE`, `XDG_DATA_DIRS`, `XDG_RUNTIME_DIR`, `DESKTOP_SESSION`,
  `KDE_FULL_SESSION`): used for desktop and icon-theme detection on Linux
  (and logged for diagnostics); see the
  [freedesktop.org specifications](https://specifications.freedesktop.org/).
- **Other**: `PATH`, `HOME`, `NO_COLOR`, `SNAP`, `SNAP_REAL_HOME`, and
  `DYLD_FALLBACK_LIBRARY_PATH` (macOS, set by the packaging hooks) are used
  where relevant and follow their standard platform meanings.
