# Qt Standard Button Translation Issue

## Problem

Qt standard buttons (Cancel, Help, OK, etc.) in dialogs were not being translated to the user's language, even though:
- Picard's own strings were translated correctly via gettext
- Qt translation files (qtbase_*.qm, qt_*.qm) were present
- The system locale was set correctly

## Root Cause

The issue was caused by **plugin Qt translators interfering with Picard's Qt translators**:

1. **Plugin translators were installed after Picard's translators**
   - Qt searches translators in reverse installation order (most recent first)
   - Plugin translators were being checked before Picard's Qt translators

2. **Plugin translators were returning source text instead of None**
   - When a plugin translator didn't have a translation, it returned the English source text
   - Qt interpreted this as a "match" and stopped searching other translators
   - This prevented Qt's own translators from being consulted

3. **Translators were getting into a broken state**
   - Something during UI initialization was breaking the translator functionality
   - The exact cause is unknown, but reinstalling translators fixes it

## Evidence

- Running with `--no-plugins` showed translated buttons → confirmed plugins were the cause
- Qt documentation states: "Translations are searched for in the reverse order in which they were installed"
- Qt documentation states: "The search stops as soon as a translation containing a matching string is found"

## Solution

### 1. Fix PluginTranslator to return None for Qt standard contexts

**File:** `picard/plugin3/i18n.py`

Changed `PluginTranslator.translate()` to return `None` (not empty string, not source text) for Qt standard contexts like:
- QDialogButtonBox
- QPlatformTheme
- QMessageBox
- QFileDialog
- etc.

This signals Qt to continue checking other translators.

### 2. Load both qtbase_ and qt_ translation files

**File:** `picard/tagger.py`

Changed `setup_translator()` to load both:
- `qtbase_*.qm` - Base Qt translations
- `qt_*.qm` - Additional Qt translations

Store references in `tagger._qt_translators` list to prevent garbage collection.

### 3. Reinstall translators before adding standard buttons

**File:** `picard/ui/options/dialog.py`

Added `tagger.reinstall_qt_translator()` call before adding standard buttons to the Options dialog.

This works around the issue where translators get into a broken state during UI initialization.

## Technical Details

### Qt Translator Search Order

From Qt documentation:
> Multiple translation files can be installed. Translations are searched for in the reverse order in which they were installed, so the most recently installed translation file is searched first and the first translation file installed is searched last.

### Translation Matching

From Qt documentation:
> The search stops as soon as a translation containing a matching string is found.

This means:
- If a translator returns a non-null string, Qt stops searching
- If a translator returns null (None in Python), Qt continues to the next translator
- Returning empty string `""` is treated as a match and stops the search

### Why Reinstalling Works

Reinstalling translators:
1. Removes them from Qt's translator list
2. Re-adds them, making them "most recently installed"
3. Ensures they're searched in the correct order relative to plugin translators
4. Somehow resets internal Qt state that was broken

The exact reason why translators break during initialization is unknown, but reinstalling them fixes the issue.

## Files Modified

1. `picard/plugin3/i18n.py` - PluginTranslator returns None for Qt contexts
2. `picard/tagger.py` - Load multiple translators, add reinstall method
3. `picard/ui/options/dialog.py` - Reinstall before adding buttons

## Testing

To verify the fix works:
1. Run Picard with plugins enabled
2. Open Options dialog → Cancel and Help buttons should be translated
3. Open File dialog → All buttons should be translated
4. Run with `--no-plugins` → Should still work (no regression)
