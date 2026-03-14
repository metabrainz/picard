#!/usr/bin/env python3
"""Detect attributes that shadow Qt methods.

This tool scans Python files to find class attributes that shadow inherited
Qt methods, which can cause type checker errors and runtime bugs.

Example issues detected:
    class MyWidget(QWidget):
        def __init__(self):
            self.actions = {}  # Shadows QWidget.actions() method!

The tool understands Qt's inheritance hierarchy, so it will detect shadowing
of methods inherited from parent classes (e.g., QWidget inherits from QObject).

Usage:
    python3 scripts/tools/detect_qt_shadowing.py

Exit codes:
    0 - No issues found
    1 - Shadowing issues detected
"""

import ast
from pathlib import Path
import sys


# Common Qt base classes and their methods that are often shadowed
# Also includes inheritance relationships
QT_METHODS = {
    'QWidget': ['actions', 'close', 'show', 'hide', 'update', 'resize', 'move'],
    'QObject': ['parent', 'children', 'deleteLater'],
    'QMenu': ['actions', 'clear'],
    'QMainWindow': ['actions', 'statusBar', 'menuBar'],
    'QDialog': ['accept', 'reject', 'done'],
}

# Qt inheritance hierarchy (child -> parents)
QT_INHERITANCE = {
    'QWidget': ['QObject'],
    'QMainWindow': ['QWidget', 'QObject'],
    'QDialog': ['QWidget', 'QObject'],
    'QMenu': ['QWidget', 'QObject'],
}


class ShadowingDetector(ast.NodeVisitor):
    """AST visitor that detects attribute assignments shadowing Qt methods."""

    def __init__(self, filepath):
        self.filepath = filepath
        self.issues = []
        self.current_class = None
        self.class_bases = {}

    def visit_ClassDef(self, node):
        """Track class definitions and their base classes."""
        old_class = self.current_class
        self.current_class = node.name

        # Extract base class names (handles both QWidget and QtWidgets.QWidget)
        bases = [
            base.id if isinstance(base, ast.Name) else base.attr
            for base in node.bases
            if isinstance(base, (ast.Name, ast.Attribute))
        ]
        self.class_bases[node.name] = bases

        self.generic_visit(node)
        self.current_class = old_class

    def visit_Assign(self, node):
        """Check self.attribute assignments for shadowing."""
        if self.current_class:
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    if isinstance(target.value, ast.Name) and target.value.id == 'self':
                        self._check_shadowing(target.attr, node.lineno, 'attribute')
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Check method definitions for shadowing."""
        if self.current_class:
            self._check_shadowing(node.name, node.lineno, 'method')
        self.generic_visit(node)

    def _check_shadowing(self, name, lineno, kind):
        """Check if an attribute or method shadows a Qt method."""
        if not self.current_class:
            return

        # Get all base classes including inherited ones
        bases = self.class_bases.get(self.current_class, [])
        all_bases = set(bases)
        for base in bases:
            all_bases.update(QT_INHERITANCE.get(base, []))

        # Check if name shadows any Qt method
        for base in all_bases:
            if base in QT_METHODS and name in QT_METHODS[base]:
                self.issues.append(
                    {
                        'file': self.filepath,
                        'line': lineno,
                        'class': self.current_class,
                        'base': base,
                        'name': name,
                        'kind': kind,
                    }
                )


def check_file(filepath):
    """Parse a Python file and detect shadowing issues."""
    try:
        with open(filepath) as f:
            tree = ast.parse(f.read(), filepath)
        detector = ShadowingDetector(filepath)
        detector.visit(tree)
        return detector.issues
    except Exception as e:
        print(f"Error parsing {filepath}: {e}", file=sys.stderr)
        return []


def main():
    picard_dir = Path('picard')
    if not picard_dir.exists():
        print("Run from picard root directory", file=sys.stderr)
        sys.exit(1)

    all_issues = []
    for pyfile in picard_dir.rglob('*.py'):
        issues = check_file(pyfile)
        all_issues.extend(issues)

    if all_issues:
        attributes = [i for i in all_issues if i['kind'] == 'attribute']
        methods = [i for i in all_issues if i['kind'] == 'method']

        if attributes:
            print(f"Found {len(attributes)} attribute shadowing issues (likely bugs):\n")
            for issue in attributes:
                print(
                    f"{issue['file']}:{issue['line']}: "
                    f"Class {issue['class']} (inherits {issue['base']}) "
                    f"shadows {issue['kind']} '{issue['name']}'"
                )

        if methods:
            print(f"\nFound {len(methods)} method shadowing (usually intentional overrides):\n")
            for issue in methods:
                print(
                    f"{issue['file']}:{issue['line']}: "
                    f"Class {issue['class']} (inherits {issue['base']}) "
                    f"overrides {issue['kind']} '{issue['name']}'"
                )

        return 1 if attributes else 0
    else:
        print("No shadowing issues detected!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
