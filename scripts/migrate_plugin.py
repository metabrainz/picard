#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate Picard Plugin v2 to v3 format.

Usage:
    python migrate-plugin.py <input_file.py> [output_dir]
"""

import argparse
import ast
from io import StringIO
from pathlib import Path
import re
import sys


def format_import_statement(module, names):
    """Format import statement with trailing comma for ruff formatting.

    Args:
        module: Module name (e.g., 'picard.plugin3.api')
        names: List of names to import or single name string

    Returns:
        Formatted import statement
    """
    if isinstance(names, str):
        names = [names]

    if len(names) == 1:
        return f"from {module} import {names[0]}"

    # Multiple imports - use parentheses with trailing comma for ruff formatting
    names_str = ",\n    ".join(names) + ","
    return f"from {module} import (\n    {names_str}\n)"


def extract_plugin_metadata(content, input_path=None):
    """Extract PLUGIN_* metadata from v2 plugin using AST parsing."""
    metadata = {}

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Error: Failed to parse plugin file: {e}")
        return metadata

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith('PLUGIN_'):
                    key = target.id[7:].lower()  # Remove 'PLUGIN_' prefix
                    value = _extract_value(node.value)
                    if value is not None:
                        metadata[key] = value

    # If no metadata found and we have a path, check for wildcard imports
    if not metadata and input_path:
        metadata = _follow_wildcard_imports(tree, input_path)

    return metadata


def _follow_wildcard_imports(tree, input_path):
    """Follow 'from ... import *' to find PLUGIN_* metadata."""
    metadata = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            # Check for wildcard import
            if node.names and any(alias.name == '*' for alias in node.names):
                # Try to resolve the import
                if node.module:
                    # Convert module path to file path
                    # e.g., "picard.plugins.add_to_collection.manifest" -> "manifest.py"
                    parts = node.module.split('.')
                    # Get the last part as the module name
                    module_file = parts[-1] + '.py'
                    module_path = input_path.parent / module_file

                    if module_path.exists():
                        try:
                            imported_content = module_path.read_text(encoding='utf-8')
                            metadata = extract_plugin_metadata(imported_content, None)
                            if metadata:
                                break
                        except Exception:
                            pass

    return metadata


def _extract_value(node):
    """Extract Python value from AST node."""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.List):
        return [_extract_value(elt) for elt in node.elts]
    elif isinstance(node, ast.Tuple):
        # Check if it's a tuple of strings (implicit concatenation)
        values = [_extract_value(elt) for elt in node.elts]
        if all(isinstance(v, str) for v in values):
            return ''.join(values)
        return values
    elif isinstance(node, ast.JoinedStr):  # f-string
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.Str):
                parts.append(value.s)
        return ''.join(parts)
    return None


def generate_manifest_toml(metadata, module_name):
    """Generate MANIFEST.toml content."""
    import uuid

    # Generate UUID for the plugin
    plugin_uuid = str(uuid.uuid4())

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
    if len(full_description) <= 200 and '\n' not in full_description:
        description = escape_toml_string(full_description)
        long_description = None
        use_multiline = False
    else:
        # Use multiline string for descriptions with newlines or long text
        use_multiline = True
        # Try to split at sentence boundary for short description
        sentences = full_description.split('. ')
        description = sentences[0]
        if len(description) > 200 or '\n' in description:
            # Truncate at word boundary
            description = full_description[:197] + '...'
        long_description = full_description

    toml = f'''uuid = "{plugin_uuid}"
name = "{name}"
authors = ["{author}"]
'''

    if use_multiline:
        toml += f'description = """{description}"""\n'
    else:
        toml += f'description = "{description}"\n'

    toml += f'''api = {api_versions}
license = "{license_name}"
license_url = "{license_url}"
'''

    if long_description and use_multiline:
        toml += f'long_description = """{long_description}"""\n'
    elif long_description:
        toml += f'long_description = "{escape_toml_string(long_description)}"\n'

    return toml


def convert_qt5_to_qt6(content):
    """Convert PyQt5 imports and patterns to PyQt6."""
    warnings = []

    # Replace PyQt5 with PyQt6
    content = content.replace('from PyQt5', 'from PyQt6')
    content = content.replace('import PyQt5', 'import PyQt6')

    # Module reorganization - QAction moved to QtGui
    if 'QAction' in content:
        content = re.sub(
            r'from PyQt6\.QtWidgets import ([^;\n]*\b)QAction(\b[^;\n]*)',
            r'from PyQt6.QtGui import \1QAction\2',
            content,
        )
        if 'from PyQt6.QtGui import' in content and 'QAction' in content:
            warnings.append("✓ Moved QAction from QtWidgets to QtGui")

    # QShortcut moved to QtGui
    if 'QShortcut' in content:
        content = re.sub(
            r'from PyQt6\.QtWidgets import ([^;\n]*\b)QShortcut(\b[^;\n]*)',
            r'from PyQt6.QtGui import \1QShortcut\2',
            content,
        )

    # Method renames
    method_renames = [
        (r'\.exec_\(\)', '.exec()'),
        (r'\.width\(', '.horizontalAdvance('),  # QFontMetrics
        (r'\.toTime_t\(\)', '.toSecsSinceEpoch()'),  # QDateTime
        (r'\.setResizeMode\(', '.setSectionResizeMode('),  # QHeaderView
    ]
    for old, new in method_renames:
        if re.search(old, content):
            content = re.sub(old, new, content)
            warnings.append(f"✓ Renamed {old} → {new}")

    # QRegExp → QRegularExpression
    if 'QRegExp' in content:
        content = re.sub(r'\bQRegExp\b', 'QRegularExpression', content)
        warnings.append("✓ Replaced QRegExp with QRegularExpression")
        warnings.append("   ⚠️  Note: QRegularExpression API differs - review usage")

    # Signal renames (PyQt6 specific)
    signal_renames = [
        (r'currentIndexChanged\[str\]', 'currentTextChanged'),
        (r'activated\[str\]', 'textActivated'),
    ]
    for old, new in signal_renames:
        if re.search(old, content):
            content = re.sub(old, new, content)
            warnings.append(f"✓ Renamed signal {old} → {new}")

    # QDesktopWidget → QScreen warning
    if 'QDesktopWidget' in content:
        warnings.append("⚠️  QDesktopWidget removed in Qt6 - use QScreen instead")
        warnings.append("   See: https://doc.qt.io/qt-6/qscreen.html")

    # Comprehensive enum conversions
    enum_mappings = [
        # Alignment flags
        (r'\bQt\.AlignLeft\b', 'Qt.AlignmentFlag.AlignLeft'),
        (r'\bQt\.AlignRight\b', 'Qt.AlignmentFlag.AlignRight'),
        (r'\bQt\.AlignCenter\b', 'Qt.AlignmentFlag.AlignCenter'),
        (r'\bQt\.AlignHCenter\b', 'Qt.AlignmentFlag.AlignHCenter'),
        (r'\bQt\.AlignVCenter\b', 'Qt.AlignmentFlag.AlignVCenter'),
        (r'\bQt\.AlignTop\b', 'Qt.AlignmentFlag.AlignTop'),
        (r'\bQt\.AlignBottom\b', 'Qt.AlignmentFlag.AlignBottom'),
        (r'\bQt\.AlignJustify\b', 'Qt.AlignmentFlag.AlignJustify'),
        # Window types
        (r'\bQt\.Window\b', 'Qt.WindowType.Window'),
        (r'\bQt\.Dialog\b', 'Qt.WindowType.Dialog'),
        (r'\bQt\.WindowSystemMenuHint\b', 'Qt.WindowType.WindowSystemMenuHint'),
        (r'\bQt\.WindowTitleHint\b', 'Qt.WindowType.WindowTitleHint'),
        (r'\bQt\.WindowCloseButtonHint\b', 'Qt.WindowType.WindowCloseButtonHint'),
        (r'\bQt\.WindowMinimizeButtonHint\b', 'Qt.WindowType.WindowMinimizeButtonHint'),
        (r'\bQt\.WindowMaximizeButtonHint\b', 'Qt.WindowType.WindowMaximizeButtonHint'),
        # Window modality
        (r'\bQt\.NonModal\b', 'Qt.WindowModality.NonModal'),
        (r'\bQt\.WindowModal\b', 'Qt.WindowModality.WindowModal'),
        (r'\bQt\.ApplicationModal\b', 'Qt.WindowModality.ApplicationModal'),
        # Item data roles
        (r'\bQt\.UserRole\b', 'Qt.ItemDataRole.UserRole'),
        (r'\bQt\.DisplayRole\b', 'Qt.ItemDataRole.DisplayRole'),
        (r'\bQt\.EditRole\b', 'Qt.ItemDataRole.EditRole'),
        (r'\bQt\.DecorationRole\b', 'Qt.ItemDataRole.DecorationRole'),
        (r'\bQt\.ToolTipRole\b', 'Qt.ItemDataRole.ToolTipRole'),
        (r'\bQt\.StatusTipRole\b', 'Qt.ItemDataRole.StatusTipRole'),
        # Check states
        (r'\bQt\.Checked\b', 'Qt.CheckState.Checked'),
        (r'\bQt\.Unchecked\b', 'Qt.CheckState.Unchecked'),
        (r'\bQt\.PartiallyChecked\b', 'Qt.CheckState.PartiallyChecked'),
        # Sort order
        (r'\bQt\.AscendingOrder\b', 'Qt.SortOrder.AscendingOrder'),
        (r'\bQt\.DescendingOrder\b', 'Qt.SortOrder.DescendingOrder'),
        # Orientation
        (r'\bQt\.Horizontal\b', 'Qt.Orientation.Horizontal'),
        (r'\bQt\.Vertical\b', 'Qt.Orientation.Vertical'),
        # Widget attributes
        (r'\bQt\.WA_DeleteOnClose\b', 'Qt.WidgetAttribute.WA_DeleteOnClose'),
        (r'\bQt\.WA_TranslucentBackground\b', 'Qt.WidgetAttribute.WA_TranslucentBackground'),
        # Global colors
        (r'\bQt\.white\b', 'Qt.GlobalColor.white'),
        (r'\bQt\.black\b', 'Qt.GlobalColor.black'),
        (r'\bQt\.red\b', 'Qt.GlobalColor.red'),
        (r'\bQt\.darkRed\b', 'Qt.GlobalColor.darkRed'),
        (r'\bQt\.green\b', 'Qt.GlobalColor.green'),
        (r'\bQt\.darkGreen\b', 'Qt.GlobalColor.darkGreen'),
        (r'\bQt\.blue\b', 'Qt.GlobalColor.blue'),
        (r'\bQt\.darkBlue\b', 'Qt.GlobalColor.darkBlue'),
        (r'\bQt\.cyan\b', 'Qt.GlobalColor.cyan'),
        (r'\bQt\.darkCyan\b', 'Qt.GlobalColor.darkCyan'),
        (r'\bQt\.magenta\b', 'Qt.GlobalColor.magenta'),
        (r'\bQt\.darkMagenta\b', 'Qt.GlobalColor.darkMagenta'),
        (r'\bQt\.yellow\b', 'Qt.GlobalColor.yellow'),
        (r'\bQt\.darkYellow\b', 'Qt.GlobalColor.darkYellow'),
        (r'\bQt\.gray\b', 'Qt.GlobalColor.gray'),
        (r'\bQt\.darkGray\b', 'Qt.GlobalColor.darkGray'),
        (r'\bQt\.lightGray\b', 'Qt.GlobalColor.lightGray'),
        # Cursor shapes
        (r'\bQt\.ArrowCursor\b', 'Qt.CursorShape.ArrowCursor'),
        (r'\bQt\.PointingHandCursor\b', 'Qt.CursorShape.PointingHandCursor'),
        (r'\bQt\.WaitCursor\b', 'Qt.CursorShape.WaitCursor'),
        (r'\bQt\.BusyCursor\b', 'Qt.CursorShape.BusyCursor'),
        # Keyboard modifiers
        (r'\bQt\.NoModifier\b', 'Qt.KeyboardModifier.NoModifier'),
        (r'\bQt\.ShiftModifier\b', 'Qt.KeyboardModifier.ShiftModifier'),
        (r'\bQt\.ControlModifier\b', 'Qt.KeyboardModifier.ControlModifier'),
        (r'\bQt\.AltModifier\b', 'Qt.KeyboardModifier.AltModifier'),
        (r'\bQt\.MetaModifier\b', 'Qt.KeyboardModifier.MetaModifier'),
        # Focus policy
        (r'\bQt\.NoFocus\b', 'Qt.FocusPolicy.NoFocus'),
        (r'\bQt\.TabFocus\b', 'Qt.FocusPolicy.TabFocus'),
        (r'\bQt\.ClickFocus\b', 'Qt.FocusPolicy.ClickFocus'),
        (r'\bQt\.StrongFocus\b', 'Qt.FocusPolicy.StrongFocus'),
        (r'\bQt\.WheelFocus\b', 'Qt.FocusPolicy.WheelFocus'),
        # Text interaction
        (r'\bQt\.NoTextInteraction\b', 'Qt.TextInteractionFlag.NoTextInteraction'),
        (r'\bQt\.TextSelectableByMouse\b', 'Qt.TextInteractionFlag.TextSelectableByMouse'),
        (r'\bQt\.TextSelectableByKeyboard\b', 'Qt.TextInteractionFlag.TextSelectableByKeyboard'),
        (r'\bQt\.TextEditable\b', 'Qt.TextInteractionFlag.TextEditable'),
        # QHeaderView resize modes
        (r'\bQHeaderView\.Interactive\b', 'QHeaderView.ResizeMode.Interactive'),
        (r'\bQHeaderView\.Fixed\b', 'QHeaderView.ResizeMode.Fixed'),
        (r'\bQHeaderView\.Stretch\b', 'QHeaderView.ResizeMode.Stretch'),
        (r'\bQHeaderView\.ResizeToContents\b', 'QHeaderView.ResizeMode.ResizeToContents'),
        # QSizePolicy
        (r'\bQSizePolicy\.Fixed\b', 'QSizePolicy.Policy.Fixed'),
        (r'\bQSizePolicy\.Minimum\b', 'QSizePolicy.Policy.Minimum'),
        (r'\bQSizePolicy\.Maximum\b', 'QSizePolicy.Policy.Maximum'),
        (r'\bQSizePolicy\.Preferred\b', 'QSizePolicy.Policy.Preferred'),
        (r'\bQSizePolicy\.Expanding\b', 'QSizePolicy.Policy.Expanding'),
        (r'\bQSizePolicy\.MinimumExpanding\b', 'QSizePolicy.Policy.MinimumExpanding'),
        (r'\bQSizePolicy\.Ignored\b', 'QSizePolicy.Policy.Ignored'),
    ]

    for old_pattern, new_value in enum_mappings:
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_value, content)

    return content, warnings


def convert_plugin_api_v2_to_v3(content):
    """Convert Plugin API v2 patterns to v3."""
    warnings = []

    # Replace imports with import from `picard.plugin3.api`.
    imports_to_replace = [
        ('picard.album', 'Album'),
        ('picard.cluster', 'Cluster'),
        ('picard.coverart.image', 'CoverArtImage'),
        ('picard.coverart.providers', 'CoverArtProvider'),
        ('picard.coverart.providers', 'ProviderOptions'),
        ('picard.file', 'File'),
        ('picard.metadata', 'Metadata'),
        ('picard.track', 'Track'),
        ('picard.ui.itemviews', 'BaseAction'),
        ('picard.ui.options', 'OptionsPage'),
        ('picard.util.imageinfo', 'ImageInfo'),
    ]

    # Helper function to replace multi-line and single-line imports
    def replace_import(old_module, class_name):
        nonlocal content
        if f'from {old_module} import' in content and class_name in content:
            # Remove the entire import block (multi-line with parentheses or single-line)
            content = re.sub(
                rf'from {re.escape(old_module)} import\s*\([^)]*\)',
                f'from picard.plugin3.api import {class_name}',
                content,
                flags=re.MULTILINE | re.DOTALL,
            )
            # Also handle single-line imports
            content = re.sub(
                rf'from {re.escape(old_module)} import\s+[^\n]+',
                f'from picard.plugin3.api import {class_name}',
                content,
            )
            warnings.append(f"✓ Updated {class_name} import to plugin3 API")

    # Keep base classes for inheritance but update them to plugin3 API
    for module, class_name in imports_to_replace:
        replace_import(module, class_name)

    # Consolidate multiple plugin3 API imports into one block with proper formatting
    api_imports = []
    for class_name in [class_name for _mod, class_name in imports_to_replace]:
        if f'from picard.plugin3.api import {class_name}' in content:
            api_imports.append(class_name)
            # Remove individual import lines
            content = re.sub(
                rf'^from picard\.plugin3\.api import {class_name}\s*$',
                '',
                content,
                flags=re.MULTILINE,
            )

    # Add consolidated import block if there are any imports (sorted alphabetically)
    if api_imports:
        api_imports.sort()
        import_block = 'from picard.plugin3.api import (\n'
        for class_name in api_imports:
            import_block += f'    {class_name},\n'
        import_block += ')\n'

        # Find the first non-__future__ import statement and insert before it
        # __future__ imports must be at the top
        match = re.search(r'^(?!from __future__)(?:from |import )', content, flags=re.MULTILINE)
        if match:
            pos = match.start()
            content = content[:pos] + import_block + '\n' + content[pos:]
        else:
            # No imports found, add after docstring/comments/__future__
            match = re.search(r'(""".*?"""|\'\'\'.*?\'\'\'|from __future__.*?\n)\s*\n', content, flags=re.DOTALL)
            if match:
                pos = match.end()
                content = content[:pos] + '\n' + import_block + '\n' + content[pos:]

    # PluginPriority
    if 'PluginPriority' in content:
        content = re.sub(r'PluginPriority\.HIGH', '100', content)
        content = re.sub(r'PluginPriority\.NORMAL', '0', content)
        content = re.sub(r'PluginPriority\.LOW', '-100', content)
        warnings.append("✓ Converted PluginPriority constants to integers")

    return content, warnings


def analyze_function_signatures(tree):
    """Analyze function signatures that need updating for v3."""
    warnings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check for metadata processor signatures
            if 'process' in node.name.lower():
                args = [arg.arg for arg in node.args.args]

                # Track metadata processor (v2: album, metadata, track, release)
                if len(args) == 4 and 'album' in args and 'track' in args:
                    warnings.append(f"⚠️  Function '{node.name}': Track metadata processor signature changed")
                    warnings.append(f"   v2: def {node.name}(album, metadata, track, release)")
                    warnings.append(f"   v3: def {node.name}(track, metadata)")

                # Album metadata processor (v2: album, metadata, release)
                elif len(args) == 3 and 'album' in args and 'release' in args:
                    warnings.append(f"⚠️  Function '{node.name}': Album metadata processor signature changed")
                    warnings.append(f"   v2: def {node.name}(album, metadata, release)")
                    warnings.append(f"   v3: def {node.name}(album, metadata)")

    return warnings


def detect_instance_method_registrations(tree):
    """Detect instance method registrations like register_*(instance.method)."""
    instance_registrations = []
    register_funcs = {
        'register_track_metadata_processor',
        'register_album_metadata_processor',
        'register_file_post_load_processor',
        'register_file_post_save_processor',
        'register_file_post_addition_to_track_processor',
        'register_file_post_removal_from_track_processor',
        'register_album_post_removal_processor',
    }

    for node in tree.body:
        # Find module-level register calls
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name) and node.value.func.id in register_funcs:
                func_name = node.value.func.id
                if node.value.args:
                    arg = node.value.args[0]
                    # Check if argument is instance.method
                    if isinstance(arg, ast.Attribute):
                        instance_name = arg.value.id if isinstance(arg.value, ast.Name) else None
                        method_name = arg.attr
                        if instance_name:
                            # Extract priority if present
                            priority = None
                            for keyword in node.value.keywords:
                                if keyword.arg == 'priority':
                                    if isinstance(keyword.value, ast.Constant):
                                        priority = keyword.value.value

                            instance_registrations.append(
                                {
                                    'register_func': func_name,
                                    'instance': instance_name,
                                    'method': method_name,
                                    'priority': priority,
                                    'node': node,
                                }
                            )

    return instance_registrations


def convert_plugin_code(content, metadata):
    """Convert v2 plugin code to v3 format using AST."""
    all_warnings = []

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Error: Failed to parse plugin code: {e}")
        return content, []

    # Track what needs to be converted
    has_log_import = False
    has_config_import = False
    has_tagger_import = False

    # Track variable assignments for instantiated actions/pages
    # Maps variable name to class name: {'vv': 'ViewVariables'}
    instantiated_vars = {}

    # Detect instance method registrations first
    instance_registrations = detect_instance_method_registrations(tree)

    # Find register calls and imports to remove
    register_calls = []
    register_funcs = {
        'register_track_metadata_processor',
        'register_album_metadata_processor',
        'register_file_post_load_processor',
        'register_file_post_save_processor',
        'register_file_post_addition_to_track_processor',
        'register_file_post_removal_from_track_processor',
        'register_album_post_removal_processor',
        'register_cluster_action',
        'register_clusterlist_action',
        'register_file_action',
        'register_album_action',
        'register_track_action',
        'register_options_page',
        'register_script_function',
        'register_script_variable',
        'register_cover_art_provider',
        'register_cover_art_filter',
        'register_cover_art_metadata_filter',
        'register_cover_art_processor',
        'register_format',
        'register_ui_init',
    }

    nodes_to_remove = set()
    imports_to_remove = set()
    decorators_to_remove = {}  # func_name -> decorator_name
    method_processors = []  # Track processors that are class methods
    replace_assignments = set()  # set of tuples (old_var, value, new_var)

    # First pass: collect potential instantiated action/page variables
    # e.g., vv = ViewVariables()
    potential_instantiated_vars = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            # Check for pattern: var = ClassName()
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
            ):
                var_name = node.targets[0].id
                class_name = node.value.func.id
                # Store mapping for later resolution
                potential_instantiated_vars[var_name] = (class_name, node)

    # Second pass: find which variables are actually used in register calls
    for node in tree.body:
        # Find decorated functions
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            for dec in node.decorator_list:
                dec_name = None
                if isinstance(dec, ast.Name):
                    dec_name = dec.id
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    dec_name = dec.func.id

                if dec_name in register_funcs:
                    register_calls.append((dec_name, node.name))
                    decorators_to_remove[node.name] = dec_name

        # Find module-level register calls
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            # Handle direct calls: register_*()
            if isinstance(node.value.func, ast.Name) and node.value.func.id in register_funcs:
                func_name = node.value.func.id
                if node.value.args:
                    arg = node.value.args[0]
                    if isinstance(arg, ast.Name):
                        # Check if this is an instantiated variable
                        if arg.id in potential_instantiated_vars:
                            # Resolve to class name and mark for removal
                            class_name, assign_node = potential_instantiated_vars[arg.id]
                            instantiated_vars[arg.id] = class_name
                            register_calls.append((func_name, class_name))
                            nodes_to_remove.add(assign_node)  # Remove the instantiation
                        else:
                            # Direct function registration
                            register_calls.append((func_name, arg.id))
                        nodes_to_remove.add(node)
                    elif isinstance(arg, ast.Call):
                        # Instantiated registration: register_cluster_action(MyAction())
                        if isinstance(arg.func, ast.Name):
                            register_calls.append((func_name, arg.func.id))
                            nodes_to_remove.add(node)
                    elif isinstance(arg, ast.Attribute):
                        # Check if it's an instantiated object method: Class().method
                        if isinstance(arg.value, ast.Call) and isinstance(arg.value.func, ast.Name):
                            # register_processor(MyClass().my_method)
                            # Convert to: instance = MyClass(); api.register_processor(instance.my_method)
                            class_name = arg.value.func.id
                            method_name = arg.attr
                            instance_registrations.append(
                                {
                                    'register_func': func_name,
                                    'class_name': class_name,
                                    'method': method_name,
                                    'priority': None,
                                }
                            )
                            nodes_to_remove.add(node)
                        else:
                            # Instance method registration - will be handled separately
                            nodes_to_remove.add(node)
            # Handle qualified calls: providers.register_*(), metadata.register_*()
            elif isinstance(node.value.func, ast.Attribute):
                if node.value.func.attr in register_funcs:
                    func_name = node.value.func.attr
                    if node.value.args:
                        arg = node.value.args[0]
                        if isinstance(arg, ast.Name):
                            # Qualified registration: providers.register_cover_art_provider(Provider)
                            register_calls.append((func_name, arg.id))
                            nodes_to_remove.add(node)
                        elif isinstance(arg, ast.Call):
                            # Instantiated registration: register_cluster_action(MyAction())
                            if isinstance(arg.func, ast.Name):
                                register_calls.append((func_name, arg.func.id))
                                nodes_to_remove.add(node)

        # Handle classes
        elif isinstance(node, ast.ClassDef):
            class_methods = {}
            has_registration = False

            # Rewrite action class titles
            if any('BaseAction' in (base.id if isinstance(base, ast.Name) else '') for base in node.bases):
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        target = item.targets[0]
                        if (
                            isinstance(target, ast.Name)
                            and target.id == 'NAME'
                            and isinstance(item.value, ast.Constant)
                        ):
                            replace_assignments.add((target.id, item.value.value, 'TITLE'))

            # Check for class methods that might be processors
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    # Skip private/helper methods (start with _)
                    if item.name.startswith('_'):
                        continue

                    # Check if method has processor-like signature
                    args = [arg.arg for arg in item.args.args]

                    # Track metadata processor: (self, track, metadata) or (self, album, metadata)
                    if len(args) == 3 and args[0] == 'self' and 'metadata' in args:
                        class_methods[item.name] = 'metadata_processor'
                    # File processor: (self, file)
                    elif len(args) == 2 and args[0] == 'self' and 'file' in args:
                        class_methods[item.name] = 'file_processor'

                    # Check if this method registers processors
                    method_source = ast.unparse(item) if hasattr(ast, 'unparse') else ''
                    if any(
                        f'register_{proc}' in method_source for proc in ['track_metadata', 'album_metadata', 'file']
                    ):
                        has_registration = True

            # Only warn if there are processor methods but no registration found
            if class_methods and not has_registration:
                for method_name, proc_type in class_methods.items():
                    method_processors.append((node.name, method_name, proc_type))

        # Find PLUGIN_* assignments to remove
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith('PLUGIN_'):
                    nodes_to_remove.add(node)

        # Find imports to remove/track
        elif isinstance(node, (ast.ImportFrom, ast.Import)):
            if isinstance(node, ast.ImportFrom):
                # Track picard imports
                if node.module == 'picard':
                    for alias in node.names:
                        if alias.name == 'log':
                            has_log_import = True
                            imports_to_remove.add(node)
                        elif alias.name == 'config':
                            has_config_import = True
                            imports_to_remove.add(node)
                elif node.module == 'picard.config':
                    # Check if importing config option types
                    option_types = {'TextOption', 'BoolOption', 'IntOption', 'FloatOption', 'ListOption', 'Option'}
                    imported_options = {alias.name for alias in node.names if alias.name in option_types}
                    if imported_options:
                        imports_to_remove.add(node)
                elif node.module == 'picard.tagger':
                    has_tagger_import = True
                    imports_to_remove.add(node)
                elif node.module and any(func in [alias.name for alias in node.names] for func in register_funcs):
                    imports_to_remove.add(node)

    # Convert function signatures
    content = fix_function_signatures(content, tree)

    # Convert assignments to new variable names
    for old_var, value, new_var in replace_assignments:
        pattern = rf'''{re.escape(old_var)}\s*=\s*["']{re.escape(value)}["']'''
        content = re.sub(pattern, f'{new_var} = "{value}"', content, flags=re.MULTILINE)

    # Convert config/log/tagger access
    if has_log_import:
        content = convert_log_access(content)
        all_warnings.append("✓ Converted log.* calls to api.logger.*")

    # Convert config option definitions (TextOption, BoolOption, etc.)
    content, option_warnings, option_map = convert_config_options(content)
    all_warnings.extend(option_warnings)

    # Remove 'options = [...]' class attribute from OptionsPage classes
    content, options_attr_warnings = remove_options_class_attribute(content)
    all_warnings.extend(options_attr_warnings)

    if has_config_import:
        content = convert_config_access(content)
        all_warnings.append("✓ Converted config.setting to api.global_config.setting")

    if has_tagger_import:
        all_warnings.append("⚠️  Tagger import found - use api._tagger (review if needed)")

    # Check for deprecated album._requests pattern
    if 'album._requests' in content or 'album.tagger.webservice' in content:
        all_warnings.append("⚠️  MANUAL MIGRATION REQUIRED: album._requests pattern detected")
        all_warnings.append("   v2: album._requests += 1; album.tagger.webservice.get(...)")
        all_warnings.append("   v3: api.add_album_task(album, task_id, description, request_factory=...)")
        all_warnings.append("   See: docs/Plugin2to3MigrationGuide.md - Pattern 1: Album Background Tasks")
        all_warnings.append("")

    # Check for deprecated register_ui_init
    if 'register_ui_init' in content:
        all_warnings.append("⚠️  MANUAL MIGRATION REQUIRED: register_ui_init pattern detected")
        all_warnings.append("   v2: register_ui_init(...)")
        all_warnings.append("   v3: register_ui_init was removed")
        all_warnings.append("   See: docs/Plugin2to3MigrationGuide.md - register_ui_init was removed")
        all_warnings.append("")

    # Convert api.* to self.api.* in class methods
    content = convert_api_in_classes(content)

    # Warn about method-based processors
    if method_processors:
        all_warnings.append("⚠️  Found processor methods in classes that may need manual registration:")
        for class_name, method_name, proc_type in method_processors:
            all_warnings.append(f"   - {class_name}.{method_name} ({proc_type})")
        all_warnings.append("")
        all_warnings.append("   If these methods should be registered as processors, add to enable():")
        all_warnings.append("   Example:")
        all_warnings.append("     def enable(api):")
        all_warnings.append("         instance = MyClass()")
        if any(pt == 'metadata_processor' for _, _, pt in method_processors):
            all_warnings.append("         api.register_track_metadata_processor(instance.method_name)")
        if any(pt == 'file_processor' for _, _, pt in method_processors):
            all_warnings.append("         api.register_file_post_load_processor(instance.method_name)")
        all_warnings.append("")
        all_warnings.append("   Or if they're not processors, you can ignore this warning.")

    # Add info about API access pattern
    if register_calls:
        all_warnings.append("ℹ️  API access pattern:")
        all_warnings.append("   - Processors: Use 'api' parameter (first argument)")
        if 'register_track_metadata_processor' in content:
            all_warnings.append("   - Processors: Parameters of track metadata processors have changed")
        all_warnings.append("   - Classes: Use 'self.api' in OptionsPage, BaseAction, CoverArtProvider")

    # Convert API patterns
    content, api_warnings = convert_plugin_api_v2_to_v3(content)
    all_warnings.extend(api_warnings)

    # Add PluginApi import
    if register_calls or instance_registrations:
        import_statement = 'from picard.plugin3.api import PluginApi\n'

        # Find the first non-__future__ import statement and insert before it
        # __future__ imports must be at the top
        match = re.search(r'^(?!from __future__)(?:from |import )', content, flags=re.MULTILINE)
        if match:
            pos = match.start()
            content = content[:pos] + import_statement + '\n' + content[pos:]
        else:
            # No imports found, add after docstring/comments/__future__
            match = re.search(r'(""".*?"""|\'\'\'.*?\'\'\'|from __future__.*?\n)\s*\n', content, flags=re.DOTALL)
            if match:
                pos = match.end()
                content = content[:pos] + '\n' + import_statement + '\n' + content[pos:]

    # Rebuild source without removed nodes
    lines = content.split('\n')
    new_lines = []
    skip_lines = set()

    # Re-parse after conversions
    try:
        tree = ast.parse(content)
        nodes_to_remove = set()
        imports_to_remove = set()

        # Rebuild instantiated_vars mapping for second pass
        # Only include variables that were actually used in register calls
        instantiated_vars_second_pass = {}
        potential_vars_second = {}

        # First collect all potential instantiated variables
        for node in tree.body:
            if isinstance(node, ast.Assign):
                if (
                    len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                ):
                    var_name = node.targets[0].id
                    class_name = node.value.func.id
                    potential_vars_second[var_name] = class_name

        # Then check which ones are used in register calls
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name) and node.value.func.id in register_funcs:
                    if node.value.args and isinstance(node.value.args[0], ast.Name):
                        var_name = node.value.args[0].id
                        if var_name in potential_vars_second:
                            instantiated_vars_second_pass[var_name] = potential_vars_second[var_name]
                elif isinstance(node.value.func, ast.Attribute) and node.value.func.attr in register_funcs:
                    if node.value.args and isinstance(node.value.args[0], ast.Name):
                        var_name = node.value.args[0].id
                        if var_name in potential_vars_second:
                            instantiated_vars_second_pass[var_name] = potential_vars_second[var_name]

        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                # Handle direct calls: register_*()
                if isinstance(node.value.func, ast.Name) and node.value.func.id in register_funcs:
                    nodes_to_remove.add(node)
                # Handle qualified calls: providers.register_*(), metadata.register_*()
                elif isinstance(node.value.func, ast.Attribute) and node.value.func.attr in register_funcs:
                    nodes_to_remove.add(node)
            elif isinstance(node, ast.Assign):
                # Remove instantiated action/page variables
                if (
                    len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id in instantiated_vars_second_pass
                ):
                    nodes_to_remove.add(node)
                # Remove PLUGIN_* assignments
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.startswith('PLUGIN_'):
                        nodes_to_remove.add(node)
            elif isinstance(node, (ast.ImportFrom, ast.Import)):
                if isinstance(node, ast.ImportFrom):
                    if node.module in ('picard', 'picard.tagger', 'picard.config'):
                        if node.module == 'picard':
                            # Only remove if importing log/config
                            if any(alias.name in ('log', 'config') for alias in node.names):
                                imports_to_remove.add(node)
                        else:
                            imports_to_remove.add(node)
                    elif node.module and any(func in [alias.name for alias in node.names] for func in register_funcs):
                        imports_to_remove.add(node)
    except (SyntaxError, ValueError):
        pass

    for node in nodes_to_remove | imports_to_remove:
        for line_no in range(node.lineno - 1, node.end_lineno):
            skip_lines.add(line_no)

    for i, line in enumerate(lines):
        if i in skip_lines:
            continue

        # Remove decorator lines
        stripped = line.strip()
        if stripped.startswith('@') and any(func in stripped for func in register_funcs):
            continue

        # Fix imports from picard.plugins.* to relative imports
        if 'from picard.plugins.' in line:
            line = re.sub(r'from picard\.plugins\.[^.]+\.', 'from .', line)

        # Replace PLUGIN_NAME references (not assignments)
        if 'PLUGIN_NAME' in line and '=' not in line.split('PLUGIN_NAME')[0]:
            plugin_name = metadata.get('name', 'Plugin')
            line = line.replace('PLUGIN_NAME', f'"{plugin_name}"')

        new_lines.append(line)

    # Remove trailing empty lines
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()

    # Add enable function with all register calls
    if register_calls or instance_registrations or option_map:
        new_lines.append('')
        new_lines.append('')
        new_lines.append('def enable(api: PluginApi):')
        new_lines.append('    """Called when plugin is enabled."""')

        # Add config option registrations
        for key, default, _type, _var_name in option_map:
            new_lines.append(f'    api.plugin_config.register_option("{key}", {default})')

        # Add direct function registrations
        for reg_type, func_name in register_calls:
            new_lines.append(f'    api.{reg_type}({func_name})')

        # Add instance method registrations
        for reg in instance_registrations:
            reg_func = reg['register_func']
            method = reg['method']
            priority = reg['priority']

            # Check if it's a class instantiation pattern
            if 'class_name' in reg:
                class_name = reg['class_name']
                # Create instance and register: instance = Class(); api.register(instance.method)
                new_lines.append(f'    _instance = {class_name}()')
                if priority is not None:
                    new_lines.append(f'    api.{reg_func}(_instance.{method}, priority={priority})')
                else:
                    new_lines.append(f'    api.{reg_func}(_instance.{method})')
            else:
                # Existing instance pattern
                instance = reg['instance']
                if priority is not None:
                    new_lines.append(f'    api.{reg_func}({instance}.{method}, priority={priority})')
                else:
                    new_lines.append(f'    api.{reg_func}({instance}.{method})')

    return '\n'.join(new_lines), all_warnings


def fix_function_signatures(content, tree):
    """Fix function signatures for v3 API."""
    replacements = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [arg.arg for arg in node.args.args]

            # Track metadata processor with tagger: (tagger, metadata, track, release) -> (api, track, metadata)
            if len(args) == 4 and 'tagger' in args and 'track' in args and 'metadata' in args:
                old_sig = f"def {node.name}(tagger, metadata, track, release)"
                new_sig = f"def {node.name}(api, track, metadata, track_node, release_node)"
                replacements.append((old_sig, new_sig))

            # Track metadata processor: (album, metadata, track, release) -> (api, track, metadata)
            elif len(args) == 4 and 'album' in args and 'track' in args and 'metadata' in args:
                old_sig = f"def {node.name}(album, metadata, track, release)"
                new_sig = f"def {node.name}(api, track, metadata, track_node, release_node)"
                replacements.append((old_sig, new_sig))

            # Album metadata processor: (album, metadata, release) -> (api, album, metadata)
            elif len(args) == 3 and 'album' in args and 'metadata' in args and 'release' in args:
                old_sig = f"def {node.name}(album, metadata, release)"
                new_sig = f"def {node.name}(api, album, metadata, release_node)"
                replacements.append((old_sig, new_sig))

            # File processor: (track, file) -> (api, file)
            elif len(args) == 2 and 'track' in args and 'file' in args:
                old_sig = f"def {node.name}(track, file)"
                new_sig = f"def {node.name}(api, file)"
                replacements.append((old_sig, new_sig))

    for old, new in replacements:
        content = content.replace(old, new)

    return content


def convert_log_access(content):
    """Convert log.* to api.logger.* (for processors) or self.api.logger.* (for classes)"""
    # In processors (functions), use api.logger
    # In classes, use self.api.logger
    # For now, convert to api.logger - class conversion happens separately
    content = re.sub(r'\blog\.debug\b', 'api.logger.debug', content)
    content = re.sub(r'\blog\.info\b', 'api.logger.info', content)
    content = re.sub(r'\blog\.warning\b', 'api.logger.warning', content)
    content = re.sub(r'\blog\.error\b', 'api.logger.error', content)
    content = re.sub(r'\blog\.exception\b', 'api.logger.exception', content)
    return content


def convert_config_options(content):
    """Convert V2 config option definitions to V3 api.plugin_config access.

    Converts:
        my_text = TextOption("setting", "my_key", "default")
        value = my_text.value
        my_text.value = "new"

        config.setting["my_key"]

    To:
        # (definition removed)
        value = api.plugin_config.get('my_key', 'default')
        api.plugin_config['my_key'] = "new"

        api.plugin_config["my_key"]
    """
    try:
        tree = ast.parse(content)
    except (SyntaxError, ValueError):
        return content, [], []

    option_types = ['TextOption', 'BoolOption', 'IntOption', 'FloatOption', 'ListOption', 'Option']
    option_list = []  # (var_name, key, default_value, option_type)
    lines_to_remove = set()

    # Find option definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    if node.value.func.id in option_types:
                        # Extract variable name
                        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                            var_name = node.targets[0].id

                            # Extract arguments: Option(section, key, default)
                            if len(node.value.args) >= 3:
                                # section = node.value.args[0]  # Usually "setting"
                                key_node = node.value.args[1]
                                default_node = node.value.args[2]

                                # Get key as string
                                if isinstance(key_node, ast.Constant):
                                    key = key_node.value
                                else:
                                    continue  # Skip complex key expressions

                                # Get default value as code
                                default_value = ast.unparse(default_node)
                                option_type = node.value.func.id

                                option_list.append((key, default_value, option_type, var_name))
                                lines_to_remove.add(node.lineno)
        # Find options that are not assigned
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in option_types:
                    # Extract arguments: Option(section, key, default)
                    if len(node.args) >= 3:
                        # section = node.value.args[0]  # Usually "setting"
                        key_node = node.args[1]
                        default_node = node.args[2]

                        # Get key as string
                        if isinstance(key_node, ast.Constant):
                            key = key_node.value
                        else:
                            continue  # Skip complex key expressions

                        # Get default value as code
                        default_value = ast.unparse(default_node)
                        option_type = node.func.id

                        option_list.append((key, default_value, option_type, None))

    if not option_list:
        return content, [], []

    # Convert content line by line
    lines = content.split('\n')
    new_lines = []
    warnings = []

    for i, line in enumerate(lines, start=1):
        # Skip option definition lines
        if i in lines_to_remove:
            continue

        # Convert .value access for each option variable
        for key, default, _opt_type, var_name in option_list:
            if var_name:
                # Write access: my_var.value = x -> api.plugin_config['key'] = x
                # Check this first to avoid false positives
                write_pattern = rf'\b{re.escape(var_name)}\.value\s*='
                if re.search(write_pattern, line):
                    line = re.sub(write_pattern, f"api.plugin_config['{key}'] =", line)
                    continue  # Skip read conversion for this line

                # Read access: my_var.value -> api.plugin_config.get('key', default)
                if f'{var_name}.value' in line:
                    line = re.sub(
                        rf'\b{re.escape(var_name)}\.value\b',
                        f"api.plugin_config.get('{key}', {default})",
                        line,
                    )
            else:
                access_pattern = rf'''\bconfig.setting\[["']{re.escape(key)}["']\]'''
                if re.search(access_pattern, line):
                    line = re.sub(access_pattern, f"api.plugin_config['{key}']", line)

        new_lines.append(line)

    if option_list:
        warnings.append(f"✓ Converted {len(option_list)} config option(s) to api.plugin_config.setting")
        for key, _default, opt_type, var_name in option_list:
            if var_name:
                warnings.append(f"  - {var_name} ({opt_type}) -> '{key}'")
            else:
                warnings.append(f"  - {opt_type} -> '{key}'")

    return '\n'.join(new_lines), warnings, option_list


def remove_options_class_attribute(content):
    """Remove V2 'options = [...]' class attribute from OptionsPage classes.

    In V2, OptionsPage classes had an 'options' attribute listing config options.
    In V3, this is not needed - options are just read/written in load()/save().
    """
    try:
        tree = ast.parse(content)
    except (SyntaxError, ValueError):
        return content, []

    lines = content.split('\n')
    lines_to_remove = set()
    warnings = []

    # Find OptionsPage classes with 'options' attribute
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if it's an OptionsPage subclass
            is_options_page = False
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == 'OptionsPage':
                    is_options_page = True
                elif isinstance(base, ast.Attribute) and base.attr == 'OptionsPage':
                    is_options_page = True

            if is_options_page:
                # Find 'options = [...]' assignment
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        if len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                            if item.targets[0].id == 'options':
                                # Mark lines for removal
                                start_line = item.lineno
                                end_line = item.end_lineno
                                for line_num in range(start_line, end_line + 1):
                                    lines_to_remove.add(line_num)
                                warnings.append(
                                    f"✓ Removed 'options' class attribute from {node.name} (not needed in V3)"
                                )

    if not lines_to_remove:
        return content, []

    # Remove marked lines
    new_lines = []
    for i, line in enumerate(lines, start=1):
        if i not in lines_to_remove:
            new_lines.append(line)

    return '\n'.join(new_lines), warnings


def convert_config_access(content):
    """Convert config.setting to api.global_config.setting (for processors) or self.api.global_config.setting (for classes)"""
    # In processors (functions), use api.global_config
    # In classes, use self.api.global_config
    # For now, convert to api.global_config - class conversion happens separately
    content = re.sub(r'\bconfig\.setting\b', 'api.global_config.setting', content)
    return content


def convert_api_in_classes(content):
    """Convert api.* to self.api.* in class methods."""
    try:
        tree = ast.parse(content)
    except (SyntaxError, ValueError):
        return content

    lines = content.split('\n')

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        # Check if it's an API enabled class
        is_api_base = any(
            any(class_name in (base.id if isinstance(base, ast.Name) else '') for base in node.bases)
            for class_name in (
                'BaseAction',
                'CoverArtProvider',
                'ImageProcessor',
                'OptionsPage',
                'ProviderOptions',
            )
        )

        if not is_api_base:
            continue

        # Convert api.* to self.api.* in class methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name != '__init__':
                # Get the method lines
                start_line = item.lineno - 1
                end_line = item.end_lineno
                for i in range(start_line, min(end_line, len(lines))):
                    # Replace api. with self.api. using negative lookbehind to avoid self.api.api
                    lines[i] = re.sub(r'(?<!self\.)(?<!\.)api\.', 'self.api.', lines[i])

    return '\n'.join(lines)


def migrate_plugin(input_file, output_dir=None):
    """Migrate a v2 plugin to v3 format."""
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: Input file '{input_file}' not found")
        return 1

    # Read input file
    content = input_path.read_text(encoding='utf-8')

    # Extract metadata
    metadata = extract_plugin_metadata(content, input_path)

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
    ui_source_files = []  # .ui files
    if input_path.parent.exists():
        # Find .ui source files
        ui_source_files = list(input_path.parent.glob('*.ui'))

        # Find compiled ui_*.py files
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

    # Generate .gitignore
    gitignore_content = (
        "# Byte-compiled / optimized / DLL files",
        "*.py[cod]",
        "__pycache__/",
        "\n# Environments and development tools",
        ".venv/",
        ".ruff_cache/\n",
    )
    gitignore_path = out_path / '.gitignore'
    gitignore_path.write_text("\n".join(gitignore_content), encoding='utf-8')
    print(f"  Created: {gitignore_path}")

    # Convert plugin code
    new_code, code_warnings = convert_plugin_code(content, metadata)
    # Also convert Qt5 to Qt6 in main code
    new_code, qt_warnings = convert_qt5_to_qt6(new_code)
    code_path = out_path / '__init__.py'
    code_path.write_text(new_code, encoding='utf-8')

    # Format with ruff
    format_with_ruff(code_path)
    print(f"  Created: {code_path}")

    # Collect all warnings
    all_warnings = code_warnings + qt_warnings

    # Process .ui source files - regenerate with pyuic6
    regenerated_files = []
    for ui_file in ui_source_files:
        ui_name = ui_file.stem  # e.g., "options" from "options.ui"

        # Check if code imports with ui_ prefix (handle both relative and absolute imports)
        has_ui_prefix = (
            f"from ui_{ui_name} import" in content
            or f"from .ui_{ui_name} import" in content
            or f".ui_{ui_name} import" in content  # Catches picard.plugins.X.ui_Y
        )

        # Generate with ui_ prefix if that's what the code expects
        if has_ui_prefix:
            py_name = f"ui_{ui_name}.py"
        else:
            py_name = f"{ui_name}.py"

        output_py = out_path / py_name

        # Try to regenerate with pyuic6
        if regenerate_ui_file(ui_file, output_py):
            regenerated_files.append(py_name)
            print(f"  Regenerated: {py_name} (from {ui_file.name})")
            # Remove from ui_files list if it was there
            ui_files = [f for f in ui_files if f.name != py_name]
        else:
            # Copy .ui file for manual regeneration
            dest = out_path / ui_file.name
            dest.write_bytes(ui_file.read_bytes())
            print(f"  Copied: {ui_file.name} (regenerate manually with pyuic6)")
            if has_ui_prefix:
                all_warnings.append(f"⚠️  {ui_file.name} expects ui_ prefix - regenerate as ui_{ui_name}.py")

    # Copy UI files if found
    qt5_files = []
    for ui_file in ui_files:
        content = ui_file.read_text(encoding='utf-8')

        # Check if it's a Qt5 file
        if 'PyQt5' in content:
            qt5_files.append(ui_file.name)
            # Convert Qt5 to Qt6
            content, file_warnings = convert_qt5_to_qt6(content)
            all_warnings.extend(file_warnings)

        dest = out_path / ui_file.name
        dest.write_text(content, encoding='utf-8')
        format_with_ruff(dest)
        print(f"  Copied: {ui_file.name}")

    if qt5_files:
        print(f"\n✓ Converted {len(qt5_files)} UI file(s) from PyQt5 to PyQt6:")
        for f in qt5_files:
            print(f"    - {f}")

    # Copy all remaining files and directories from source
    if input_path.parent.exists():
        # Files generated by migration script (never copy from source)
        skip_files = {
            'MANIFEST.toml',
            '__init__.py',
            code_path.name,
        }

        # Regenerated UI files that should get .orig backup if they exist in source
        regenerated_ui_files = set(regenerated_files)

        # Python build/cache patterns to exclude (from Python.gitignore)
        exclude_patterns = {
            '__pycache__',
            '.pytest_cache',
            '.tox',
            '.nox',
            '.coverage',
            '.cache',
            'htmlcov',
            'build',
            'dist',
            'eggs',
            '.eggs',
            '*.egg-info',
            'sdist',
            'var',
            'wheels',
            '.Python',
            'pip-log.txt',
            'pip-delete-this-directory.txt',
        }

        copied_files = []
        copied_dirs = []
        conflicts = []

        for item in input_path.parent.iterdir():
            # Skip the main input file, hidden files, Python build artifacts, and generated files
            if (
                item == input_path
                or item.name.startswith('.')
                or item.name in exclude_patterns
                or item.name in skip_files
                or item.suffix in ('.pyc', '.pyo', '.pyd', '.so')
            ):
                continue

            dest = out_path / item.name

            if item.is_file():
                # Check if this is a regenerated UI file that should get .orig backup
                if item.name in regenerated_ui_files:
                    # Rename conflicting file with .orig extension
                    new_name = f"{item.name}.orig"
                    dest = out_path / new_name
                    conflicts.append((item.name, new_name))

                dest.write_bytes(item.read_bytes())
                copied_files.append(dest.name)

                # Format Python files with ruff
                if dest.suffix == '.py':
                    format_with_ruff(dest, all_warnings)

            elif item.is_dir():
                import shutil

                shutil.copytree(item, dest, dirs_exist_ok=True)
                copied_dirs.append(item.name)

        if copied_files:
            print(f"\n✓ Copied {len(copied_files)} file(s)")
        if copied_dirs:
            print(f"✓ Copied {len(copied_dirs)} directory(ies)")
        if conflicts:
            all_warnings.append(f"⚠️  Renamed {len(conflicts)} conflicting file(s):")
            for old, new in conflicts:
                all_warnings.append(f"   {old} → {new}")

    # Print warnings
    if all_warnings:
        print(f"\n{'=' * 70}")
        print("MIGRATION WARNINGS - Manual Review Required:")
        print('=' * 70)
        for warning in all_warnings:
            print(warning)
        print('=' * 70)

    print(f"\nMigration complete! Plugin saved to: {out_path}")
    print("\nNext steps:")
    print("  1. Review the generated code in __init__.py")
    print("  2. Address all warnings above")
    print("  3. Update function signatures as needed")
    print("  4. Test the plugin with Picard 3.0")
    print("  5. See docs/PLUGINSV3/MIGRATION.md for details")
    print(f"  6. Create a tag for the current version '{metadata.get('version', '1.0.0')}'")

    return 0


def format_with_ruff(file_path, warnings_list=None):
    """Format Python file with ruff.

    Args:
        file_path: Path to Python file to format
        warnings_list: Optional list to append warnings to

    Returns:
        True if formatting succeeded, False otherwise
    """
    import subprocess

    try:
        subprocess.run(['ruff', 'format', str(file_path)], capture_output=True, check=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        # Ruff failed - log warning but don't fail migration
        msg = f"⚠️  Failed to format {file_path.name}: {e.stderr.strip()}"
        if warnings_list is not None:
            warnings_list.append(msg)
        return False
    except FileNotFoundError:
        # Ruff not available - skip silently
        return False


def regenerate_ui_file(ui_file, output_py):
    """Regenerate .py file from .ui using pyuic6."""
    try:
        from PyQt6 import uic
        from PyQt6.uic.exceptions import UIFileException
    except ImportError:
        print("  PyQt6 not available, regenerate UI file by running pyuic6")
        return False

    try:
        tmp_out = StringIO()
        uic.compileUi(ui_file, tmp_out)

        # Post-process to add noqa comments for unused imports
        # pyuic6 generates imports that may not all be used
        content = tmp_out.getvalue()
        lines = content.split('\n')

        # Add header comment
        header = [
            '# Form implementation generated from reading ui file',
            '# Run pyuic6 to regenerate if .ui file changes',
            '# Note: PyQt6 imports may have unused modules, use # noqa: F401 to silence linters',
            '',
        ]

        # Find where to insert header (after any existing comments)
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('#'):
                insert_pos = i + 1
            elif line.strip():
                break

        for i, line in enumerate(lines):
            # Add noqa to PyQt imports to suppress unused import warnings
            if line.startswith('from PyQt6 import') and '# noqa' not in line:
                lines[i] = line + '  # noqa: F401'

        # Insert header
        for header_line in reversed(header):
            lines.insert(insert_pos, header_line)

        output_py.write_text('\n'.join(lines), encoding='utf-8')
        return True
    except UIFileException as err:
        print(f"  pyuic6 failed: {err}")
        return False


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
