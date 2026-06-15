# Local Non-Git Plugins

## Purpose

Local non-git plugins allow developers and testers to load a plugin directly from a directory on disk **without requiring a git repository**. This is intended exclusively for **testing and development** workflows where setting up git is unnecessary overhead.

> **Important:** A git repository is required to distribute a plugin and to have it added to the official Picard plugin registry. Without git, version management and automatic updates are not available.

## When to Use

- Rapid prototyping of a new plugin idea
- Testing a plugin during development before initializing a git repository
- Loading a plugin received as a plain directory (e.g., from a zip archive)

For anything beyond personal testing, use `picard-plugins --init` to create a proper git-managed plugin project.

## How It Works

A local non-git plugin:

- Lives in place on disk — nothing is copied, symlinked, or cloned.
- Requires a valid `MANIFEST.toml` (same fields as any plugin: `uuid`, `name`, `description`, `api`) and an `__init__.py` with `enable(api)`.
- Is registered via its metadata entry (`ref_type='local'`) in the existing `plugins3_metadata` config.
- Is loaded on startup from its original path.
- Is **automatically removed** from config if the directory disappears.

## CLI Usage

### Install

```bash
picard-plugins --install /path/to/my-plugin
```

A confirmation prompt warns about the absence of git:

```text
⚠ This plugin is not managed by git.
⚠   A git repository is required to distribute a plugin and to have it
    added to the official registry.
⚠   Without git, version management and automatic updates are not available.
Do you want to continue? [y/N]
```

Use `--yes` to skip the prompt.

### List

```bash
picard-plugins --list
```

Local non-git plugins show a `[local]` marker:

```text
  My Plugin (enabled) [local]
    Short description
    UUID: ...
    Source: /path/to/my-plugin
    Path: /path/to/my-plugin
```

### Update (Reload)

```bash
picard-plugins --update my-plugin
```

For local non-git plugins, this performs a **reload**: disable → re-read manifest → enable. This picks up any code or manifest changes without restarting Picard.

Output: `✓ my-plugin: Plugin reloaded`

### Remove (Unregister)

```bash
picard-plugins --remove my-plugin
```

This **unregisters** the plugin from Picard's config. The files on disk are **not deleted**.

### Unsupported Operations

The following commands are not available for local non-git plugins:

| Command | Behavior |
|---------|----------|
| `--switch-ref` | Error: "not managed by git" |
| `--list-refs` | Error: "not managed by git" |
| `--check-updates` | Silently skipped |

## GUI Usage

In the Install Plugin dialog → **Local** tab:

1. Select a directory containing `MANIFEST.toml` and `__init__.py`.
2. If the directory has no `.git`, a confirmation dialog appears with the same warning about git being required for distribution.
3. Click **Yes** to proceed.

Local non-git plugins appear in the plugin list with a visual indicator and support the same enable/disable/remove actions as git-managed plugins.

## Metadata Storage

Local non-git plugins use the same `plugins3_metadata` config dict as git-managed plugins, with:

```python
{
    "uuid": "...",
    "name": "plugin-dir-name",
    "url": "/absolute/path/to/plugin",
    "ref": "local",
    "commit": "",
    "ref_type": "local"
}
```

On startup, entries with `ref_type='local'` are loaded directly from the stored path. If the path no longer exists, the entry is automatically removed.

## Limitations

- No version tracking — there is no commit history or tags.
- No automatic updates — `--update` only reloads from disk.
- Not distributable — cannot be shared via the plugin registry.
- No ref switching — there are no branches or tags.
- Plugin name collisions with git-managed plugins are rejected (UUID uniqueness is enforced).

## Migrating to Git

When ready to distribute your plugin:

```bash
cd /path/to/my-plugin
git init
git add -A
git commit -m "Initial commit"
```

Then reinstall via git:

```bash
picard-plugins --install /path/to/my-plugin --reinstall
```

The plugin will now be managed by git with full update/ref support. Alternatively, use `picard-plugins --init` from the start for a proper project scaffold with git already configured.
