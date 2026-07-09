# Unified Config Upgrade System

## Summary

Redesign the config upgrade mechanism to cleanly separate **settings
transforms** (option renames, value format changes) from **non-settings
operations** (persist cleanup, UI state resets), using decorators with version
arguments instead of version-encoded function names. The settings transforms
become reusable across three contexts: base config at startup, existing profile
overrides at startup, and imported profile data.

---

## Problem Statement

### 1. Profile import needs option transforms

When importing a profile exported from an older Picard version, renamed or
restructured options must be transformed to their current equivalents. Today,
this logic only exists inside `config_upgrade_hooks.py` functions that operate
on the full `Config` object. There is no way to apply those same transforms to
an imported settings dict without duplicating the logic.

### 2. The current system conflates two concerns

Each `upgrade_to_v*` function can contain any mix of:

- **Settings transforms** — option renames, value format changes. These are
  pure dict operations applicable to base config, profile overrides, and
  imported profiles.
- **Non-settings operations** — clearing persist state, removing obsolete keys,
  showing interactive dialogs, resetting UI state. These only make sense at
  startup on the local config.

Of the ~42 existing hooks, roughly 27 are settings transforms and 15 are
non-settings operations. There is no way to distinguish them programmatically.

### 3. Duplication is inevitable under the current design

A parallel registry for profile import requires re-defining the same transforms
in two places. They will inevitably drift.

### 4. Version appears in two places

The version is encoded in the function name (`upgrade_to_v3_0_0dev8`) and
implicitly in what the function does. There is no structured way to query
"what settings transforms exist between version X and Y?" without introspecting
function names.

### 5. Plugins have no upgrade mechanism

Plugins can rename or restructure their own options between versions, but there
is no framework for migrating saved plugin configuration data. The design
should not preclude adding plugin support in the future.

---

## Design Goals

1. **Single source of truth** — each option transform is defined once
2. **Three consumers** — startup (base config), startup (profile overrides),
   and profile import all use the same transform definitions
3. **No version duplication** — version appears once per transform (in the
   decorator argument), not also in the function name
4. **Clean separation** — settings transforms vs. non-settings operations are
   structurally distinct
5. **Testable** — settings transforms are pure dict operations, testable
   without the full Config/QSettings machinery
6. **Simple to add** — adding a new option rename is one decorated function
7. **Extensible** — design does not preclude future plugin upgrade support
8. **Backward compatible** — migration from old hooks is incremental

---

## Proposed Design

### Two decorators

| Decorator | Signature | Runs at startup | Runs on import |
|-----------|-----------|-----------------|----------------|
| `@upgrade_settings(version)` | `func(settings: Settings)` | ✅ base + all profiles | ✅ |
| `@upgrade_config(version)` | `func(config: Config)` | ✅ | ❌ |

- `@upgrade_settings` functions receive a `Settings` argument (type alias for
  `dict | SettingConfigSection`). The polymorphic helpers handle both cases.
- `@upgrade_config` functions receive the full `Config` object for operations
  that cannot be expressed as settings transforms.
- Multiple functions can share the same version — they execute in definition
  order.
- Docstrings are logged when upgrades execute (same as today).

### Polymorphic helpers

All helpers accept `Settings` (dict or SettingConfigSection) and branch
internally. For the `SettingConfigSection` path, `option_type` and `default`
are required (asserted at runtime) to support QSettings deserialization.

| Helper | Purpose |
|--------|---------|
| `rename_option_in_settings(settings, old, new, option_type, default, reverse)` | Rename a key, optionally invert boolean |
| `upgrade_option_value_in_settings(settings, name, transform)` | Apply a value transform to an existing key |
| `read_old_option(settings, name, option_type, default) -> Any` | Read and remove an old option (for complex transforms: type changes, one→many) |
| `write_option(settings, name, value)` | Write a value (handles Enum→.value serialization for dicts) |

### Registry and startup flow

A single module-level registry (`_UPGRADES_REGISTRY`) is populated by both decorators
at import time, preserving declaration order. Each entry is a
`(Version, _UpgradeType, Callable)` tuple where `_UpgradeType` is either
`SETTINGS` or `CONFIG`.

At startup, `run_config_upgrades()` merges old-style `upgrade_to_v*` hooks and
new-style decorated functions into a single version-ordered execution plan:

1. For each version > stored config version (in order):
   - Run new-style entries in declaration order:
     - `SETTINGS` → run on `config.setting` + all profile override dicts
     - `CONFIG` → run on the full Config object
   - Run old-style hook if present (handles its own profiles internally)
2. Update stored config version

Declaration order gives developers full control over execution sequence within
a version — no implicit "settings before config" rule.

### Profile import flow

1. Read `picard_version` from the TOML file
2. Collect all `@upgrade_settings` functions with version > picard_version
3. Apply them in order to the imported settings dict (plain dict path)
4. Continue with normal import

Exposed as `apply_settings_upgrades_for_import(settings, from_version_str)`.

---

## Future: Plugin Upgrade Support

A similar mechanism could apply to plugins in the future — plugins could
register their own settings upgrades using the same decorator pattern and
helpers. However, plugin versions are optional and may not follow a consistent
format, making version comparison and upgrade ordering complex. This is out of
scope for now.

---

## Testing

- **Settings upgrades** are tested with plain dicts — no Config/QSettings
  fixture needed. Each function gets unit tests for the dict path.
- **Config upgrades** need the Config fixture (same as today).
- **Meta-tests** verify every registered function has a corresponding test.
- **Integration tests** verify the full startup path (base + profiles upgraded
  together).

---

## Migration Plan

Migration from the old hook system is **incremental** — one hook at a time.

### Phase 1: Framework (done)

1. Decorators, registries, polymorphic helpers
2. Merged startup runner (old + new style coexist)
3. Profile import integration (`apply_settings_upgrades_for_import`)
4. First hook converted (`upgrade_to_v3_0_0dev3`)

### Phase 2: Migrate existing hooks

Convert hooks one at a time:
simple renames → multi-renames → value transforms → complex hooks →
non-settings hooks (`@upgrade_config`).

### Phase 3: Cleanup

Once all hooks are migrated, the following can be removed from
`config_upgrade.py`:

| To remove | Reason |
|-----------|--------|
| `autodetect_upgrade_hooks()` | No more `upgrade_to_v*` functions to discover |
| `UPGRADE_FUNCTION_PREFIX` | Only used by autodetect |
| `_HOOKS_MODULE` | Only used by autodetect |
| `rename_option(config, ...)` | Old-style wrapper, delegates to polymorphic helper |
| `upgrade_option_value(config, ...)` | Old-style wrapper, delegates to polymorphic helper |

Note: `_rename_option_in_settings` and `_upgrade_option_value_in_settings`
(the old dict-only helpers) have already been removed — the old-style wrappers
now delegate to the polymorphic `rename_option_in_settings` and
`upgrade_option_value_in_settings` directly.

`run_config_upgrades()` simplifies to:

1. Iterate `_UPGRADES_REGISTRY` sorted by version (declaration order within same version)
2. For each version > stored config version:
   - `SETTINGS` entries → apply to `config.setting` + all profile dicts
   - `CONFIG` entries → apply to full Config
3. Update stored version

No more merging of old-style and new-style hooks, no closure creation, no
combined docstring assembly.

---

## Old vs New System Comparison

| Aspect | Old system (`upgrade_to_v*`) | New system (`@upgrade_settings` / `@upgrade_config`) |
|--------|------------------------------|------------------------------------------------------|
| Version source | Encoded in function name | Decorator argument |
| Function naming | Constrained (`upgrade_to_v3_0_0dev8`) | Free (descriptive: `rename_dont_write_tags`) |
| Multiple per version | Not allowed (one function per version) | Allowed (definition order) |
| Profile override handling | Manual in each hook (via `rename_option`) | Automatic (framework iterates profiles) |
| Profile import support | None | Built-in (`apply_settings_upgrades_for_import`) |
| Settings vs non-settings | Mixed in same function | Structurally separated by decorator |
| Testability | Needs full Config/QSettings fixture | Dict path testable with plain dicts |
| Discovery | Module introspection by name prefix | Decorator registration at import time |
| Adding a hook | Name function with version, call `rename_option(config, ...)` | Decorate with version, call `rename_option_in_settings(settings, ...)` |
| Type safety | `config` parameter (untyped internals) | `settings: Settings` (typed union, asserts in ConfigSection path) |

---

## File Structure

```text
picard/
├── config_upgrade.py              ← Framework: decorators, registries, helpers, runners
├── config_upgrade_hooks.py        ← All upgrade functions (both styles during migration)
└── profiles/
    └── importer.py                ← Calls upgrade framework for imported settings
```

All upgrade functions live in `config_upgrade_hooks.py`. One file to edit when
adding hooks. Separation is by decorator, not by file.

---

## Decisions

### 1. Hooks that mix settings and non-settings must be split

If a hook touches settings keys AND does non-settings work, it must be split
into two functions at the same version. `@upgrade_config` does NOT run on
profile dicts or imported data — placing a settings transform there is a bug.

The rule: if it changes a settings key (rename, value transform,
remove-and-replace), it goes in `@upgrade_settings`. Everything else goes in
`@upgrade_config`.
