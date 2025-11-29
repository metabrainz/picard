#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate Picard Plugin v2 to v3 format.

Usage:
    python migrate-plugin.py <input_file.py> [output_dir]
"""

import argparse
import ast
from pathlib import Path
import re
import sys


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
version = "{metadata.get('version', '1.0.0')}"
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

    # Remove imports that will be accessed via api
    # BaseAction, OptionsPage, File, Track, Album, Cluster, CoverArtImage
    # These are now available as api.BaseAction, api.OptionsPage, etc.
    imports_to_remove = [
        'from picard.ui.itemviews import BaseAction',
        'from picard.ui.options import OptionsPage',
        'from picard.file import File',
        'from picard.track import Track',
        'from picard.album import Album',
        'from picard.cluster import Cluster',
        'from picard.coverart.image import CoverArtImage',
    ]

    for old_import in imports_to_remove:
        if old_import in content:
            # Remove the import line
            content = re.sub(rf'^{re.escape(old_import)}.*$', '', content, flags=re.MULTILINE)
            class_name = old_import.split()[-1]
            warnings.append(f"✓ Removed {class_name} import - use _api.{class_name} instead")

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
        'register_track_post_removal_processor',
        'register_cluster_action',
        'register_file_action',
        'register_album_action',
        'register_track_action',
        'register_options_page',
        'register_script_function',
        'register_cover_art_provider',
        'register_format',
    }

    nodes_to_remove = set()
    imports_to_remove = set()
    decorators_to_remove = {}  # func_name -> decorator_name
    method_processors = []  # Track processors that are class methods

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
            if isinstance(node.value.func, ast.Name) and node.value.func.id in register_funcs:
                func_name = node.value.func.id
                if node.value.args:
                    arg = node.value.args[0]
                    if isinstance(arg, ast.Name):
                        register_calls.append((func_name, arg.id))
                        nodes_to_remove.add(node)

        # Check for class methods that might be processors
        elif isinstance(node, ast.ClassDef):
            class_methods = {}
            has_registration = False

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
                elif node.module == 'picard.tagger':
                    has_tagger_import = True
                    imports_to_remove.add(node)
                elif node.module and any(func in [alias.name for alias in node.names] for func in register_funcs):
                    imports_to_remove.add(node)

    # Convert function signatures
    content = fix_function_signatures(content, tree)

    # Convert config/log/tagger access
    if has_log_import:
        content = convert_log_access(content)
        all_warnings.append("✓ Converted log.* calls to api.logger.*")

    if has_config_import:
        content = convert_config_access(content)
        all_warnings.append("✓ Converted config.setting to api.global_config.setting")

    if has_tagger_import:
        all_warnings.append("⚠️  Tagger import found - using api._tagger (review if needed)")

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

    # Add info about _api pattern
    if register_calls:
        all_warnings.append("ℹ️  Module-level _api variable added for accessing API")
        all_warnings.append("   Use _api.logger.info(...) for logging")
        all_warnings.append("   Use _api.BaseAction, _api.OptionsPage, etc. for base classes")
        all_warnings.append("   Or pass api explicitly to classes: MyClass(api)")

    # Inject api in classes
    content, injection_warnings = inject_api_in_classes(content)
    all_warnings.extend(injection_warnings)

    # Check for remaining api usage in classes
    try:
        check_tree = ast.parse(content)
        class_warnings = check_api_usage_in_classes(check_tree)
        all_warnings.extend(class_warnings)
    except (SyntaxError, ValueError):
        pass

    # Convert API patterns
    content, api_warnings = convert_plugin_api_v2_to_v3(content)
    all_warnings.extend(api_warnings)

    # Rebuild source without removed nodes
    lines = content.split('\n')
    new_lines = []
    skip_lines = set()

    # Re-parse after conversions
    try:
        tree = ast.parse(content)
        nodes_to_remove = set()
        imports_to_remove = set()

        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name) and node.value.func.id in register_funcs:
                    nodes_to_remove.add(node)
            elif isinstance(node, ast.Assign):
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

        # Convert class references to use _api
        # e.g., class MyAction(BaseAction) -> class MyAction(_api.BaseAction)
        for class_name in ['BaseAction', 'OptionsPage', 'File', 'Track', 'Album', 'Cluster', 'CoverArtImage']:
            if f'({class_name})' in line or f'({class_name},' in line:
                line = line.replace(f'({class_name})', f'(_api.{class_name})')
                line = line.replace(f'({class_name},', f'(_api.{class_name},')

        new_lines.append(line)

    # Remove trailing empty lines
    while new_lines and not new_lines[-1].strip():
        new_lines.pop()

    # Add enable function with all register calls
    if register_calls:
        new_lines.append('')
        new_lines.append('')
        new_lines.append('# Module-level api reference for use in classes/functions')
        new_lines.append('_api = None')
        new_lines.append('')
        new_lines.append('')
        new_lines.append('def enable(api):')
        new_lines.append('    """Called when plugin is enabled."""')
        new_lines.append('    global _api')
        new_lines.append('    _api = api')
        for reg_type, func_name in register_calls:
            new_lines.append(f'    api.{reg_type}({func_name})')

    return '\n'.join(new_lines), all_warnings


def fix_function_signatures(content, tree):
    """Fix function signatures for v3 API."""
    replacements = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [arg.arg for arg in node.args.args]

            # Track metadata processor with tagger: (tagger, metadata, track, release) -> (track, metadata)
            if len(args) == 4 and 'tagger' in args and 'track' in args and 'metadata' in args:
                old_sig = f"def {node.name}(tagger, metadata, track, release)"
                new_sig = f"def {node.name}(track, metadata)"
                replacements.append((old_sig, new_sig))

            # Track metadata processor: (album, metadata, track, release) -> (track, metadata)
            elif len(args) == 4 and 'album' in args and 'track' in args and 'metadata' in args:
                old_sig = f"def {node.name}(album, metadata, track, release)"
                new_sig = f"def {node.name}(track, metadata)"
                replacements.append((old_sig, new_sig))

            # Album metadata processor: (album, metadata, release) -> (album, metadata)
            elif len(args) == 3 and 'album' in args and 'metadata' in args and 'release' in args:
                old_sig = f"def {node.name}(album, metadata, release)"
                new_sig = f"def {node.name}(album, metadata)"
                replacements.append((old_sig, new_sig))

            # File processor: (track, file) -> (file)
            elif len(args) == 2 and 'track' in args and 'file' in args:
                old_sig = f"def {node.name}(track, file)"
                new_sig = f"def {node.name}(file)"
                replacements.append((old_sig, new_sig))

    for old, new in replacements:
        content = content.replace(old, new)

    return content


def convert_log_access(content):
    """Convert log.* to api.logger.*"""
    # Replace log method calls
    content = re.sub(r'\blog\.debug\b', 'api.logger.debug', content)
    content = re.sub(r'\blog\.info\b', 'api.logger.info', content)
    content = re.sub(r'\blog\.warning\b', 'api.logger.warning', content)
    content = re.sub(r'\blog\.error\b', 'api.logger.error', content)
    content = re.sub(r'\blog\.exception\b', 'api.logger.exception', content)
    return content


def convert_config_access(content):
    """Convert config.setting to api.global_config.setting"""
    content = re.sub(r'\bconfig\.setting\b', 'api.global_config.setting', content)
    return content


def inject_api_in_classes(content):
    """Inject api parameter in OptionsPage and Action __init__ methods."""
    try:
        tree = ast.parse(content)
    except (SyntaxError, ValueError):
        return content, []

    warnings = []
    lines = content.split('\n')
    modifications = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        # Check if it's OptionsPage or Action
        is_options = any('OptionsPage' in (base.id if isinstance(base, ast.Name) else '') for base in node.bases)
        is_action = any('Action' in (base.id if isinstance(base, ast.Name) else '') for base in node.bases)

        if not (is_options or is_action):
            continue

        # Check if class uses api
        class_source = '\n'.join(lines[node.lineno - 1 : node.end_lineno])
        if 'api.' not in class_source:
            continue

        # Find __init__ method
        init_method = None
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                init_method = item
                break

        if init_method:
            # Has __init__ - add api parameter
            args = [arg.arg for arg in init_method.args.args]
            if 'api' in args:
                continue

            init_line_idx = init_method.lineno - 1
            init_line = lines[init_line_idx]

            if 'def __init__(self' in init_line:
                new_line = init_line.replace('def __init__(self', 'def __init__(self, api')
                modifications.append(('replace', init_line_idx, init_line, new_line))

                first_body_line_idx = init_method.lineno
                indent = len(lines[first_body_line_idx]) - len(lines[first_body_line_idx].lstrip())
                api_assignment = ' ' * indent + 'self.api = api'
                modifications.append(('insert', first_body_line_idx, None, api_assignment))

                warnings.append(f"✓ Injected api in {node.name}.__init__")
        else:
            # No __init__ - create one and convert api.* to self.api.*
            insert_line = node.lineno

            # Find where to insert (after class variables, before first method)
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    insert_line = item.lineno - 1
                    break
                elif isinstance(item, ast.Assign):
                    insert_line = item.end_lineno

            # Get indentation
            if node.body:
                first_item_line = lines[node.body[0].lineno - 1]
                indent = len(first_item_line) - len(first_item_line.lstrip())
            else:
                indent = 4

            # Create __init__ method
            init_lines = [
                ' ' * indent + 'def __init__(self, api):',
                ' ' * (indent + 4) + 'self.api = api',
                ' ' * (indent + 4) + 'super().__init__()',
                '',
            ]

            for line in reversed(init_lines):
                modifications.append(('insert', insert_line, None, line))

            warnings.append(f"✓ Created __init__ for {node.name}")

            # Mark class for api.* → self.api.* conversion
            modifications.append(('convert_api', node.name, node.lineno - 1, node.end_lineno))

    # Apply modifications
    for mod in sorted(modifications, key=lambda x: x[1] if isinstance(x[1], int) else 0, reverse=True):
        if mod[0] == 'convert_api':
            # Convert api.* to self.api.* in class methods
            _, start_line, end_line = mod[1], mod[2], mod[3]
            for i in range(start_line, min(end_line, len(lines))):
                if 'api.' in lines[i] and 'self.api' not in lines[i] and 'def ' not in lines[i]:
                    lines[i] = lines[i].replace('api.', 'self.api.')
        elif mod[0] == 'insert':
            lines.insert(mod[1], mod[3])
        elif mod[0] == 'replace':
            lines[mod[1]] = mod[3]

    return '\n'.join(lines), warnings


def check_api_usage_in_classes(tree):
    """Check if api is used in classes that still need manual injection."""
    warnings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if class uses api
            class_source = ast.unparse(node) if hasattr(ast, 'unparse') else ''
            if 'api.' not in class_source:
                continue

            # Check if it's an Action or OptionsPage
            is_action = any('Action' in base.id if isinstance(base, ast.Name) else False for base in node.bases)
            is_options = any('OptionsPage' in base.id if isinstance(base, ast.Name) else False for base in node.bases)

            if not (is_action or is_options):
                continue

            # Check if __init__ has api parameter
            has_api_param = False
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                    args = [arg.arg for arg in item.args.args]
                    if 'api' in args:
                        has_api_param = True
                    break

            # Only warn if api injection failed (complex case)
            if not has_api_param:
                warnings.append(f"⚠️  Class '{node.name}' uses 'api' but injection failed - needs manual review")

    return warnings


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

    return 0


def format_with_ruff(file_path):
    """Format Python file with ruff."""
    import subprocess

    try:
        subprocess.run(['ruff', 'format', str(file_path)], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Ruff not available or failed, skip formatting
        pass


def regenerate_ui_file(ui_file, output_py):
    """Regenerate .py file from .ui using pyuic6."""
    import subprocess

    try:
        subprocess.run(['pyuic6', str(ui_file), '-o', str(output_py)], capture_output=True, check=True, text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
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
