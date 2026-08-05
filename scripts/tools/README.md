# scripts/tools/

Developer utility scripts for MusicBrainz Picard. These are not shipped with
releases — they assist with development, releases, and asset generation.

## Scripts

| Script | Description |
|--------|-------------|
| `authors-between-releases.py` | List code contributors and translators between two git tags, for release notes. |
| `changelog-for-version.py` | Extract changelog entries for a given version from git history. |
| `check_settings.py` | Check for references to undefined option settings in the codebase. |
| `detect_qt_shadowing.py` | Detect class attributes that shadow inherited Qt methods. |
| `fix-header.py` | Regenerate source file copyright/license headers from git log. |
| `generate_icons.sh` | Generate PNG icons (multiple sizes) from an SVG source file. |
| `generate_match_icons.py` | Generate match quality bookmark PNGs (normal + pending, 1× + 2×). |
| `multiple_imports_on_one_line.py` | Find import statements with multiple names on one line. |
| `patch-version.sh` | Patch the version string with git commit count/hash for dev builds. |
| `pull-shared-translations.py` | Pull shared translation strings from Weblate/upstream. |
| `tag-release.sh` | Create a git tag for the current release version. |
