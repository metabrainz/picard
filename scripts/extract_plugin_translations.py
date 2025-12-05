#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract translatable strings from Picard plugin code.

Extracts api.tr() and api.trn() calls from Python files and generates
translation files in JSON or TOML format. Respects .gitignore patterns.

Usage:
    extract_plugin_translations.py <plugin_dir> [options]

Options:
    --format {json,toml}  Output format (default: toml)
    --stdout              Output to stdout instead of file
    --help                Show this help message

Examples:
    # Extract to locale/en.toml
    extract_plugin_translations.py /path/to/plugin

    # Extract to stdout in JSON format
    extract_plugin_translations.py /path/to/plugin --format json --stdout

    # Extract to locale/de.json (if source_locale=de in MANIFEST.toml)
    extract_plugin_translations.py /path/to/plugin --format json
"""

import argparse
import ast
from fnmatch import fnmatch
import json
from pathlib import Path
import sys


def extract_from_code(plugin_dir):
    """Extract tr() and trn() calls from Python files."""
    translations = {}
    gitignore_patterns = read_gitignore(plugin_dir)

    for py_file in Path(plugin_dir).rglob('*.py'):
        if is_ignored(py_file, plugin_dir, gitignore_patterns):
            continue

        try:
            with open(py_file, encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            tree = ast.parse(content, filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in ('tr', 'trn'):
                        extract_translation_call(node, translations, py_file, lines)
        except Exception as e:
            print(f"Warning: Failed to parse {py_file}: {e}", file=sys.stderr)

    return translations


def read_gitignore(plugin_dir):
    """Read .gitignore patterns."""
    gitignore_path = Path(plugin_dir) / '.gitignore'
    if not gitignore_path.exists():
        return []

    patterns = []
    try:
        with open(gitignore_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    except Exception:
        pass

    return patterns


def is_ignored(file_path, plugin_dir, patterns):
    """Check if file matches any .gitignore pattern."""
    rel_path = file_path.relative_to(plugin_dir)
    rel_str = str(rel_path)

    for pattern in patterns:
        # Handle directory patterns
        if pattern.endswith('/'):
            if any(part == pattern.rstrip('/') for part in rel_path.parts):
                return True
        # Handle file patterns
        elif fnmatch(rel_str, pattern) or fnmatch(file_path.name, pattern):
            return True
        # Handle ** patterns
        elif '**' in pattern:
            glob_pattern = pattern.replace('**/', '**/').replace('**', '*')
            if fnmatch(rel_str, glob_pattern):
                return True

    return False


def extract_translation_call(node, translations, py_file, lines):
    """Extract key and text from tr() or trn() call."""
    if not node.args:
        return

    def warn(msg):
        line = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ''
        print(f"Warning: {msg} at {py_file}:{node.lineno}: {line}", file=sys.stderr)

    # First arg is the key
    key = get_string_value(node.args[0])
    if not key:
        warn(f"Cannot extract key from {node.func.attr}() call")
        return

    if node.func.attr == 'tr':
        # api.tr(key, text, **kwargs)
        text = get_string_value(node.args[1]) if len(node.args) > 1 else None
        if text is None and len(node.args) > 1:
            warn("Cannot extract text from tr() call")
        translations[key] = text or f"?{key}?"

    elif node.func.attr == 'trn':
        # api.trn(key, singular, plural, n=..., **kwargs)
        singular = get_string_value(node.args[1]) if len(node.args) > 1 else None
        plural = get_string_value(node.args[2]) if len(node.args) > 2 else None

        if (singular is None or plural is None) and len(node.args) > 1:
            warn("Cannot extract singular/plural from trn() call")

        translations[key] = {'one': singular or f"?{key}?", 'other': plural or f"?{key}?"}


def get_string_value(node):
    """Extract string value from AST node."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def read_source_locale(plugin_dir):
    """Read source_locale from MANIFEST.toml."""
    manifest_path = Path(plugin_dir) / 'MANIFEST.toml'
    if not manifest_path.exists():
        return 'en'

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            print("Warning: tomllib not available, using 'en' as default", file=sys.stderr)
            return 'en'

    try:
        with open(manifest_path, 'rb') as f:
            manifest = tomllib.load(f)
            return manifest.get('source_locale', 'en')
    except Exception as e:
        print(f"Warning: Failed to read MANIFEST.toml: {e}", file=sys.stderr)
        return 'en'


def format_toml(translations):
    """Format translations as TOML string."""
    lines = []
    for key in sorted(translations.keys()):
        value = translations[key]
        if isinstance(value, dict):
            lines.append(f'["{key}"]')
            for plural_key in sorted(value.keys()):
                lines.append(f'{plural_key} = {json.dumps(value[plural_key])}')
            lines.append('')
        else:
            lines.append(f'"{key}" = {json.dumps(value)}')
    return '\n'.join(lines)


def write_json(translations, output_file):
    """Write translations to JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translations, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write('\n')


def write_toml(translations, output_file):
    """Write translations to TOML file."""
    content = format_toml(translations)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
        if content:
            f.write('\n')


def main():
    parser = argparse.ArgumentParser(description='Extract translatable strings from Picard plugin')
    parser.add_argument('plugin_dir', help='Path to plugin directory')
    parser.add_argument('--format', choices=['json', 'toml'], default='toml', help='Output format')
    parser.add_argument('--stdout', action='store_true', help='Output to stdout instead of file')
    args = parser.parse_args()

    plugin_dir = Path(args.plugin_dir)
    if not plugin_dir.exists():
        print(f"Error: Plugin directory not found: {plugin_dir}", file=sys.stderr)
        return 1

    translations = extract_from_code(plugin_dir)
    if not translations:
        print("No translatable strings found", file=sys.stderr)
        return 1

    if args.stdout:
        output = (
            json.dumps(translations, indent=2, ensure_ascii=False, sort_keys=True)
            if args.format == 'json'
            else format_toml(translations)
        )
        print(output)
    else:
        source_locale = read_source_locale(plugin_dir)
        locale_dir = plugin_dir / 'locale'
        locale_dir.mkdir(exist_ok=True)

        output_file = locale_dir / f'{source_locale}.{args.format}'
        (write_json if args.format == 'json' else write_toml)(translations, output_file)
        print(f"Extracted {len(translations)} strings to {output_file}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
