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
        # Try single quotes (can contain escaped double quotes)
        desc_match = re.search(r"PLUGIN_DESCRIPTION\s*=\s*'((?:[^'\\]|\\.)*)'", content, re.MULTILINE)
    if not desc_match:
        # Try double quotes (can contain escaped single quotes and line continuations)
        desc_match = re.search(r'PLUGIN_DESCRIPTION\s*=\s*"((?:[^"\\]|\\.)*)"', content, re.MULTILINE | re.DOTALL)

    if desc_match:
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
                ]
            ):
                continue

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

    # Generate MANIFEST.toml
    module_name = input_path.stem
    manifest_content = generate_manifest_toml(metadata, module_name)
    manifest_path = out_path / 'MANIFEST.toml'
    manifest_path.write_text(manifest_content, encoding='utf-8')
    print(f"  Created: {manifest_path}")

    # Convert plugin code
    new_code = convert_plugin_code(content, metadata)
    code_path = out_path / '__init__.py'
    code_path.write_text(new_code, encoding='utf-8')
    print(f"  Created: {code_path}")

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
