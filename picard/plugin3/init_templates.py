# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""Templates and helpers for `picard-plugins --init` plugin scaffolding."""

from __future__ import annotations

from pathlib import Path
import re
import unicodedata

from picard.plugin3.validator import generate_uuid


def slugify_name(name: str) -> str:
    """Convert a plugin name to a URL/directory-friendly slug.

    Handles non-ASCII names by decomposing accented characters to their
    ASCII equivalents (e.g. É→E, ü→u). Characters that cannot be
    decomposed (e.g. CJK) are kept as-is.

    Args:
        name: Plugin name (e.g. "My Cool Plugin", "Plugin d'Étiquetage")

    Returns:
        str: Slugified name (e.g. "my-cool-plugin", "plugin-d-etiquetage")
    """
    # Decompose accented characters (É → E + combining accent), then
    # drop the combining marks to get ASCII equivalents
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_approx = ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')
    slug = ascii_approx.lower()
    # Keep alphanumerics (including non-Latin scripts), replace the rest
    slug = re.sub(r'[^\w]+', '-', slug, flags=re.UNICODE)
    slug = re.sub(r'_', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


def toml_escape(value: str) -> str:
    """Escape a string for use in a TOML basic string (double-quoted).

    Handles backslashes, quotes, and control characters per the TOML spec.
    """
    value = value.replace('\\', '\\\\')
    value = value.replace('"', '\\"')
    value = value.replace('\b', '\\b')
    value = value.replace('\t', '\\t')
    value = value.replace('\n', '\\n')
    value = value.replace('\f', '\\f')
    value = value.replace('\r', '\\r')
    return value


def generate_manifest(
    name: str,
    description: str = '',
    authors: list[str] | None = None,
    categories: list[str] | None = None,
    license_id: str = '',
    license_url: str = '',
    with_i18n: bool = False,
    report_bugs_to: str = '',
) -> str:
    """Generate a filled-in MANIFEST.toml for a new plugin.

    Args:
        name: Plugin name (required)
        description: Short description
        authors: List of author names
        categories: List of category strings
        license_id: SPDX license identifier
        license_url: License URL
        with_i18n: Whether to include translation fields
        report_bugs_to: Bug tracker URL or mailto: address

    Returns:
        str: MANIFEST.toml content
    """
    generated_uuid = generate_uuid()
    lines = [
        f'uuid = "{generated_uuid}"',
        f'name = "{toml_escape(name)}"',
        f'description = "{toml_escape(description or "A Picard plugin")}"',
        'api = ["3.0"]',
    ]
    if authors:
        authors_str = ', '.join(f'"{toml_escape(a)}"' for a in authors)
        lines.append(f'authors = [{authors_str}]')
    if license_id:
        lines.append(f'license = "{toml_escape(license_id)}"')
    if license_url:
        lines.append(f'license_url = "{toml_escape(license_url)}"')
    if categories:
        cats_str = ', '.join(f'"{toml_escape(c)}"' for c in categories)
        lines.append(f'categories = [{cats_str}]')
    lines.append('# homepage = "https://github.com/username/plugin-name"')
    if report_bugs_to:
        lines.append(f'report_bugs_to = "{toml_escape(report_bugs_to)}"')
    else:
        lines.append('# report_bugs_to = "https://your.plugin.bugtracker/issues"')
    if with_i18n:
        lines.append('source_locale = "en"')
        lines.append('')
        lines.append('# [name_i18n]')
        lines.append('# de = ""')
        lines.append('')
        lines.append('# [description_i18n]')
        lines.append('# de = ""')
    lines.append('')  # trailing newline
    return '\n'.join(lines)


def generate_plugin_init_py(with_i18n: bool = False) -> str:
    """Generate a minimal __init__.py for a new plugin.

    Args:
        with_i18n: Whether to include translation examples

    Returns:
        str: __init__.py content
    """
    if with_i18n:
        return _generate_plugin_init_py_i18n()
    else:
        return _generate_plugin_init_py_basic()


def _generate_plugin_init_py_i18n() -> str:
    """Generate __init__.py with translation support."""
    return '''"""Basic Picard 3 plugin with translation support."""

from picard.plugin3.api import (
    PluginApi,
    t_,
)

# Module-level translatable strings (resolved at runtime via api.tr)
GREETING = t_("message.greeting", "Hello from the plugin!")


def enable(api: PluginApi) -> None:
    """Called when the plugin is enabled.

    Use api to register plugin hooks and access essential Picard APIs.
    """
    # Translate a string at runtime
    greeting = api.tr(GREETING, "Hello from the plugin!")
    api.logger.info(greeting)


def disable() -> None:
    """Called when the plugin is disabled."""
'''


def _generate_plugin_init_py_basic() -> str:
    """Generate basic __init__.py without translation support."""
    return '''"""Basic Picard 3 plugin."""

from picard.plugin3.api import PluginApi


def enable(api: PluginApi) -> None:
    """Called when the plugin is enabled.

    Use api to register plugin hooks and access essential Picard APIs.
    """
    api.logger.info("Plugin enabled")


def disable() -> None:
    """Called when the plugin is disabled."""
'''


def markdown_escape(text: str) -> str:
    """Escape Markdown special characters in text."""
    for char in r'\`*_{}[]()#+-.!|>~':
        text = text.replace(char, '\\' + char)
    return text


def generate_readme(name: str) -> str:
    """Generate a basic README.md for a new plugin.

    Args:
        name: Plugin name

    Returns:
        str: README.md content
    """
    slug = slugify_name(name)
    escaped_name = markdown_escape(name)
    return f'''# {escaped_name}

A plugin for [MusicBrainz Picard](https://picard.musicbrainz.org/).

## Installation

```bash
picard-plugins --install /path/to/{slug}
```

## Development

To validate your plugin:

```bash
picard-plugins --validate .
```

## License

See MANIFEST.toml for license information.
'''


def generate_gitignore() -> str:
    """Generate a .gitignore for a new plugin.

    Returns:
        str: .gitignore content
    """
    return '''# Byte-compiled / optimized / DLL files
*.py[cod]
__pycache__/

# Environments and development tools
.venv/
.ruff_cache/

# Distribution / packaging
*.egg-info/
dist/
'''


def generate_source_locale_toml() -> str:
    """Generate a source locale TOML file matching the i18n plugin skeleton.

    Returns:
        str: en.toml content
    """
    return '''"message.greeting" = "Hello from the plugin!"
'''


def write_plugin_project(
    target: Path,
    name: str,
    description: str = '',
    authors: list[str] | None = None,
    categories: list[str] | None = None,
    license_id: str = '',
    license_url: str = '',
    with_i18n: bool = False,
    report_bugs_to: str = '',
) -> list[str]:
    """Write plugin scaffold files to target directory.

    Creates the directory (if needed) and writes all project files.

    Args:
        target: Path to the plugin directory
        name: Plugin name
        description: Short description
        authors: List of author names
        categories: List of category strings
        license_id: SPDX license identifier
        license_url: License URL
        with_i18n: Whether to generate translation-enabled skeleton
        report_bugs_to: Bug tracker URL or mailto: address

    Returns:
        list: Filenames/dirs created (for display purposes)
    """
    target.mkdir(parents=True, exist_ok=True)
    (target / 'MANIFEST.toml').write_text(
        generate_manifest(
            name,
            description,
            authors,
            categories,
            license_id,
            license_url,
            with_i18n=with_i18n,
            report_bugs_to=report_bugs_to,
        ),
        encoding='utf-8',
    )
    (target / '__init__.py').write_text(generate_plugin_init_py(with_i18n=with_i18n), encoding='utf-8')
    (target / 'README.md').write_text(generate_readme(name), encoding='utf-8')
    (target / '.gitignore').write_text(generate_gitignore(), encoding='utf-8')
    filenames = ['MANIFEST.toml', '__init__.py', 'README.md', '.gitignore']
    if with_i18n:
        locale_dir = target / 'locale'
        locale_dir.mkdir()
        (locale_dir / 'en.toml').write_text(generate_source_locale_toml(), encoding='utf-8')
        filenames.append('locale/')
    return filenames


def parse_author_string(author: str) -> tuple[str, str]:
    """Parse 'Name <email>' notation into (name, email).

    Args:
        author: Author string, e.g. "Jane Doe" or "Jane Doe <jane@example.com>"

    Returns:
        tuple: (name, email) where email may be empty
    """
    match = re.match(r'^(.+?)\s*<([^>]+)>\s*$', author)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return author, ''


def get_git_config_author() -> tuple[str, str]:
    """Read author name and email from git config.

    Returns:
        tuple: (name, email) from git config, or ('', '') if unavailable
    """
    try:
        from picard.git.factory import git_backend

        backend = git_backend()
        name = backend.get_config_value('user.name')
        email = backend.get_config_value('user.email')
        return name, email
    except Exception:
        return '', ''


def get_git_author(authors: list[str] | None = None, author_email: str = '') -> tuple[str, str]:
    """Get author name and email for git commit.

    Uses the first provided author (supporting "Name <email>" notation),
    falls back to git config, then to a generic default.
    The git backend requires both name and email to be non-empty.

    Returns:
        tuple: (author_name, author_email)
    """
    default_email = 'picard@musicbrainz.org'
    git_name, git_email = get_git_config_author()

    if authors:
        name, parsed_email = parse_author_string(authors[0])
        email = parsed_email or author_email or git_email or default_email
        return name, email

    if git_name:
        return git_name, git_email or default_email

    return 'picard-plugins', default_email
