#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate Picard Plugin v2 to v3 format.

Usage:
    python migrate-plugin.py <input_file.py> [output_dir]
"""

import argparse
from pathlib import Path
import re
import sys


def extract_plugin_metadata(content):
    """Extract PLUGIN_* metadata from v2 plugin."""
    metadata = {}

    # Special handling for multiline description with triple quotes
    desc_match = re.search(r"PLUGIN_DESCRIPTION\s*=\s*'''(.*?)'''", content, re.MULTILINE | re.DOTALL)
    if not desc_match:
        desc_match = re.search(r'PLUGIN_DESCRIPTION\s*=\s*"""(.*?)"""', content, re.MULTILINE | re.DOTALL)
    if not desc_match:
        # Try parenthesized multi-line string concatenation
        desc_match = re.search(r"PLUGIN_DESCRIPTION\s*=\s*\((.*?)\)", content, re.MULTILINE | re.DOTALL)
        if desc_match:
            # Extract all quoted strings and concatenate
            strings = re.findall(r'["\']([^"\']*)["\']', desc_match.group(1))
            desc = ''.join(strings)
            metadata['description'] = desc
    if not desc_match:
        # Try single quotes (can contain escaped double quotes)
        desc_match = re.search(r"PLUGIN_DESCRIPTION\s*=\s*'((?:[^'\\]|\\.)*)'", content, re.MULTILINE)
    if not desc_match:
        # Try double quotes (can contain escaped single quotes and line continuations)
        desc_match = re.search(r'PLUGIN_DESCRIPTION\s*=\s*"((?:[^"\\]|\\.)*)"', content, re.MULTILINE | re.DOTALL)

    if desc_match and 'description' not in metadata:
        desc = desc_match.group(1)
        # Remove line continuations (backslash followed by newline)
        desc = re.sub(r'\\\s*\n\s*', ' ', desc)
        desc = desc.strip()
        # Clean up multiple spaces
        desc = re.sub(r'\s+', ' ', desc)
        metadata['description'] = desc

    patterns = {
        'name': r'PLUGIN_NAME\s*=\s*["\'](.+?)["\']',
        'author': r"PLUGIN_AUTHOR\s*=\s*'((?:[^'\\]|\\.)*)'|" + r'PLUGIN_AUTHOR\s*=\s*"((?:[^"\\]|\\.)*)"',
        'version': r'PLUGIN_VERSION\s*=\s*["\'](.+?)["\']',
        'api_versions': r'PLUGIN_API_VERSIONS\s*=\s*\[(.+?)\]',
        'license': r'PLUGIN_LICENSE\s*=\s*["\'](.+?)["\']',
        'license_url': r'PLUGIN_LICENSE_URL\s*=\s*["\'](.+?)["\']',
    }

    for key, pattern in patterns.items():
        if key == 'description':
            continue  # Already handled above
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            # For author, check which group matched
            if key == 'author':
                value = match.group(1) if match.group(1) else match.group(2)
                # Unescape quotes
                value = value.replace('\\"', '"').replace("\\'", "'")
            else:
                value = match.group(1)

            if key == 'api_versions':
                # Parse list of versions
                versions = re.findall(r'["\']([^"\']+)["\']', value)
                metadata[key] = versions
            else:
                metadata[key] = value

    return metadata


def generate_manifest_toml(metadata, module_name):
    """Generate MANIFEST.toml content."""
    # Map v2 API versions to v3
    api_versions = []
    for v in metadata.get('api_versions', []):
        if v in ['1.0', '2.0']:
            api_versions.append('3.0')

    if not api_versions:
        api_versions = ['3.0']

    # Remove duplicates
    api_versions = sorted(set(api_versions))

    # Escape quotes and backslashes in strings for TOML
    def escape_toml_string(s):
        return s.replace('\\', '\\\\').replace('"', '\\"')

    name = escape_toml_string(metadata.get('name', 'Unknown Plugin'))
    author = escape_toml_string(metadata.get('author', 'Unknown'))
    license_name = escape_toml_string(metadata.get('license', 'GPL-2.0-or-later'))
    license_url = escape_toml_string(metadata.get('license_url', 'https://www.gnu.org/licenses/gpl-2.0.html'))

    # Handle description - split if too long (max 200 chars)
    full_description = metadata.get('description', '')
    if len(full_description) <= 200:
        description = escape_toml_string(full_description)
        long_description = None
    else:
        # Try to split at sentence boundary
        sentences = full_description.split('. ')
        description = sentences[0]
        if len(description) > 200:
            # Truncate at word boundary
            description = full_description[:197] + '...'
        description = escape_toml_string(description)
        long_description = escape_toml_string(full_description)

    toml = f'''name = "{name}"
authors = ["{author}"]
version = "{metadata.get('version', '1.0.0')}"
description = "{description}"
api = {api_versions}
license = "{license_name}"
license_url = "{license_url}"
'''

    if long_description:
        toml += f'long_description = "{long_description}"\n'

    return toml


def convert_qt5_to_qt6(content):
    """Convert PyQt5 imports and common patterns to PyQt6."""
    # Replace PyQt5 with PyQt6
    content = content.replace('from PyQt5', 'from PyQt6')
    content = content.replace('import PyQt5', 'import PyQt6')

    # Common enum changes that are straightforward
    # Note: This is not exhaustive - complex UI files may need manual review
    replacements = [
        # QHeaderView resize modes
        ('QHeaderView.Stretch', 'QHeaderView.ResizeMode.Stretch'),
        ('QHeaderView.ResizeToContents', 'QHeaderView.ResizeMode.ResizeToContents'),
        ('QHeaderView.Interactive', 'QHeaderView.ResizeMode.Interactive'),
        # QSizePolicy
        ('QSizePolicy.Expanding', 'QSizePolicy.Policy.Expanding'),
        ('QSizePolicy.Fixed', 'QSizePolicy.Policy.Fixed'),
        ('QSizePolicy.Minimum', 'QSizePolicy.Policy.Minimum'),
        ('QSizePolicy.Preferred', 'QSizePolicy.Policy.Preferred'),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    return content


def convert_plugin_code(content, metadata):
    """Convert v2 plugin code to v3 format."""
    lines = content.split('\n')
    new_lines = []

    # Track what we've seen
    in_metadata = False
    skip_until_imports = True
    register_calls = []

    for line in lines:
        # Skip PLUGIN_* metadata assignment lines (not references)
        if line.strip().startswith('PLUGIN_') and '=' in line:
            in_metadata = True
            continue

        # Skip empty lines after metadata
        if in_metadata and not line.strip():
            continue

        if line.strip().startswith('from ') or line.strip().startswith('import '):
            in_metadata = False
            skip_until_imports = False

            # Skip old register imports
            if any(
                x in line
                for x in [
                    'register_track_metadata_processor',
                    'register_album_metadata_processor',
                    'register_file_post_load_processor',
                    'register_file_post_save_processor',
                    'register_file_post_addition_to_track_processor',
                    'register_file_post_removal_from_track_processor',
                    'register_album_post_removal_processor',
                    'register_track_post_removal_processor',
                    'register_cluster_action',
                    'register_file_action',
                    'register_album_action',
                    'register_track_action',
                    'register_options_page',
                    'register_script_function',
                    'register_cover_art_provider',
                    'register_format',
                ]
            ):
                continue

            # Fix imports from picard.plugins.* to relative imports
            if 'from picard.plugins.' in line:
                # Extract the plugin name and convert to relative import
                # from picard.plugins.bpm.ui_options_bpm import X -> from .ui_options_bpm import X
                line = re.sub(r'from picard\.plugins\.[^.]+\.', 'from .', line)

            new_lines.append(line)
            continue

        if skip_until_imports:
            continue

        # Replace PLUGIN_NAME references
        if 'PLUGIN_NAME' in line:
            plugin_name = metadata.get('name', 'Plugin')
            line = line.replace('PLUGIN_NAME', f'"{plugin_name}"')

        # Capture register calls at module level
        if line and not line[0].isspace():
            for reg_type in [
                'register_track_metadata_processor',
                'register_album_metadata_processor',
                'register_file_post_load_processor',
                'register_file_post_save_processor',
                'register_file_post_addition_to_track_processor',
                'register_file_post_removal_from_track_processor',
                'register_album_post_removal_processor',
                'register_track_post_removal_processor',
                'register_cluster_action',
                'register_file_action',
                'register_album_action',
                'register_track_action',
                'register_options_page',
                'register_script_function',
                'register_cover_art_provider',
                'register_format',
            ]:
                if reg_type in line:
                    # Match everything between outer parentheses (greedy to get nested parens)
                    match = re.search(rf'{reg_type}\((.+)\)', line)
                    if match:
                        register_calls.append((reg_type, match.group(1)))
                    break

        # Skip module-level register calls
        if any(
            reg in line
            for reg in [
                'register_track_metadata_processor',
                'register_album_metadata_processor',
                'register_file_post_load_processor',
                'register_file_post_save_processor',
                'register_file_post_addition_to_track_processor',
                'register_file_post_removal_from_track_processor',
                'register_album_post_removal_processor',
                'register_track_post_removal_processor',
                'register_cluster_action',
                'register_file_action',
                'register_album_action',
                'register_track_action',
                'register_options_page',
                'register_script_function',
                'register_cover_art_provider',
                'register_format',
            ]
        ):
            if line and not line[0].isspace():
                continue

        new_lines.append(line)

    # Add enable function with all register calls
    if register_calls:
        new_lines.append('')
        new_lines.append('def enable(api):')
        new_lines.append('    """Called when plugin is enabled."""')
        for reg_type, func_name in register_calls:
            new_lines.append(f'    api.{reg_type}({func_name})')

    return '\n'.join(new_lines)


def migrate_plugin(input_file, output_dir=None):
    """Migrate a v2 plugin to v3 format."""
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: Input file '{input_file}' not found")
        return 1

    # Read input file
    content = input_path.read_text(encoding='utf-8')

    # Extract metadata
    metadata = extract_plugin_metadata(content)

    if not metadata:
        print("Error: Could not extract plugin metadata")
        return 1

    print(f"Migrating plugin: {metadata.get('name', 'Unknown')}")
    print(f"  Author: {metadata.get('author', 'Unknown')}")
    print(f"  Version: {metadata.get('version', 'Unknown')}")

    # Determine output directory
    if output_dir:
        out_path = Path(output_dir)
    else:
        # Use plugin name as directory
        plugin_name = input_path.stem
        out_path = input_path.parent / f"{plugin_name}_v3"

    out_path.mkdir(parents=True, exist_ok=True)

    # Check for UI files in same directory
    ui_files = []
    if input_path.parent.exists():
        ui_files = list(input_path.parent.glob('ui_*.py'))
        # Also check for other common patterns
        ui_files.extend(input_path.parent.glob('option_*.py'))
        ui_files.extend(input_path.parent.glob('options_*.py'))
        ui_files.extend(input_path.parent.glob('actions_*.py'))
        # Check for options.py if not __init__.py
        if (input_path.parent / 'options.py').exists():
            ui_files.append(input_path.parent / 'options.py')
        # Remove the main file if it matches
        ui_files = [f for f in ui_files if f != input_path]
        # Remove duplicates
        ui_files = list(set(ui_files))

    # Generate MANIFEST.toml
    module_name = input_path.stem
    manifest_content = generate_manifest_toml(metadata, module_name)
    manifest_path = out_path / 'MANIFEST.toml'
    manifest_path.write_text(manifest_content, encoding='utf-8')
    print(f"  Created: {manifest_path}")

    # Convert plugin code
    new_code = convert_plugin_code(content, metadata)
    # Also convert Qt5 to Qt6 in main code
    new_code = convert_qt5_to_qt6(new_code)
    code_path = out_path / '__init__.py'
    code_path.write_text(new_code, encoding='utf-8')
    print(f"  Created: {code_path}")

    # Copy UI files if found
    qt5_files = []
    for ui_file in ui_files:
        content = ui_file.read_text(encoding='utf-8')

        # Check if it's a Qt5 file
        if 'PyQt5' in content:
            qt5_files.append(ui_file.name)
            # Convert Qt5 to Qt6
            content = convert_qt5_to_qt6(content)

        dest = out_path / ui_file.name
        dest.write_text(content, encoding='utf-8')
        print(f"  Copied: {ui_file.name}")

    if qt5_files:
        print(f"\n⚠️  WARNING: Converted {len(qt5_files)} UI file(s) from PyQt5 to PyQt6:")
        for f in qt5_files:
            print(f"    - {f}")
        print("  Please review these files as some Qt6 changes may require manual adjustment.")
        print("  See: https://doc.qt.io/qt-6/portingguide.html")

    print(f"\nMigration complete! Plugin saved to: {out_path}")
    print("\nNext steps:")
    print("  1. Review the generated code in __init__.py")
    print("  2. Update API calls to use the new PluginApi")
    print("  3. Test the plugin with: picard plugins --validate <path>")
    print("  4. Install with: picard plugins --install <path>")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Migrate Picard Plugin v2 to v3 format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Migrate plugin to default directory
  python migrate-plugin.py my_plugin.py

  # Migrate to specific directory
  python migrate-plugin.py my_plugin.py /path/to/output
        ''',
    )

    parser.add_argument('input_file', help='Input v2 plugin file (.py)')
    parser.add_argument('output_dir', nargs='?', help='Output directory (optional)')

    args = parser.parse_args()

    return migrate_plugin(args.input_file, args.output_dir)


if __name__ == '__main__':
    sys.exit(main())
