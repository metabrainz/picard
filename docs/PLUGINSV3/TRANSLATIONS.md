# Plugin Translation System

This document describes the translation system for Plugin v3, including both plugin UI translations and registry metadata translations.

---

## Overview

Plugin v3 supports two types of translations:

1. **Plugin UI translations** - For plugin interface text (buttons, messages, etc.)
2. **Registry metadata translations** - For plugin name and description in the registry

---

## Plugin UI Translations

### File Structure

```
myplugin/
├── __init__.py
├── MANIFEST.toml
└── locale/
    ├── en.json          # English (required, fallback)
    ├── de.json          # German
    ├── fr.json          # French
    └── ja.json          # Japanese
```

### Translation File Format

Simple flat JSON structure with dot notation for namespacing:

```json
{
  "ui.menu.submit listens": "Submit listens Now",
  "ui.menu.configure": "Configure ListenBrainz",
  "ui.button.login": "Login to ListenBrainz",
  "ui.button.logout": "Logout",

  "options.title": "ListenBrainz Options",
  "options.username": "Username",
  "options.password": "Password",

  "error.network": "Network error: {error}",
  "error.auth_failed": "Authentication failed",

  "status.submitting_listens": "Submitting: {artist} - {title}",
  "status.submit listensd": "Submit listensd {count} tracks",

  "message.login_success": "Successfully logged in as {username}"
}
```

### Usage in Plugin Code

```python
from picard.plugin3 import PluginApi

def enable(api: PluginApi):
    _ = api.gettext  # Shorthand alias

    # Simple translation
    button_text = _('ui.button.login')
    # Returns: "Login to ListenBrainz"

    # With parameters
    message = _('status.submit listensd', count=5)
    # Returns: "Submit listensd 5 tracks"

    # Error messages
    error_msg = _('error.network', error='Connection timeout')
    # Returns: "Network error: Connection timeout"
```

### Key Naming Conventions

Use consistent prefixes for organization:

- `ui.*` - User interface elements (buttons, labels, menus)
- `options.*` - Settings/options page
- `error.*` - Error messages
- `status.*` - Status messages
- `message.*` - User notifications
- `help.*` - Help text

### Placeholders

Use `{variable}` syntax for dynamic content:

```json
{
  "status.processing": "Processing {filename}...",
  "error.file_not_found": "File not found: {path}",
  "message.saved": "Saved {count} files successfully"
}
```

### Locale Fallback

1. Try current locale (e.g., `de_DE`)
2. Try language without region (e.g., `de`)
3. Fall back to English (`en`)
4. Return `?key?` if not found (with warning logged)

---

## Registry Metadata Translations

### In MANIFEST.toml

Plugin name and description can be translated directly in MANIFEST.toml:

```toml
name = "ListenBrainz Submitter"
description = "Submit your music to ListenBrainz"

[name_i18n]
de = "ListenBrainz-Submitter"
fr = "Soumetteur ListenBrainz"
ja = "ListenBrainzサブミッター"

[description_i18n]
de = "Submit listens deine Musik zu ListenBrainz"
fr = "Submit listensz votre musique sur ListenBrainz"
ja = "ListenBrainzに音楽をスクロブルする"
```

### In Registry JSON

The website extracts these translations and includes them in the registry:

```json
{
  "id": "listenbrainz",
  "name": "ListenBrainz Submitter",
  "description": "Submit your music to ListenBrainz",
  "name_i18n": {
    "de": "ListenBrainz-Submitter",
    "fr": "Soumetteur ListenBrainz",
    "ja": "ListenBrainzサブミッター"
  },
  "description_i18n": {
    "de": "Submit listens deine Musik zu ListenBrainz",
    "fr": "Submit listensz votre musique sur ListenBrainz",
    "ja": "ListenBrainzに音楽をスクロブルする"
  }
}
```

### Benefits

- Single source of truth (MANIFEST.toml)
- No separate translation files needed for registry
- Plugin developers manage translations
- Website automatically includes them
- Picard and website can display localized names/descriptions

---

## PluginApi.gettext() Implementation

```python
from PyQt6.QtCore import QLocale

class PluginApi:
    def __init__(self, manifest: PluginManifest, tagger) -> None:
        self._manifest = manifest
        self._tagger = tagger
        self._translations = {}
        self._current_locale = None
        self._load_translations()

    def _load_translations(self):
        """Load translation files for the plugin"""
        plugin_dir = Path(self._manifest.module_name)
        locale_dir = plugin_dir / 'locale'

        if not locale_dir.exists():
            return

        # Get current locale from Qt (e.g., "de_DE", "en_US")
        # This respects user's UI language setting in Picard
        self._current_locale = QLocale().name()

        # Always load English as fallback
        en_file = locale_dir / 'en.json'
        if en_file.exists():
            with open(en_file, 'r', encoding='utf-8') as f:
                self._translations['en'] = json.load(f)

        # Load current locale (e.g., "de_DE")
        locale_file = locale_dir / f'{self._current_locale}.json'
        if locale_file.exists():
            with open(locale_file, 'r', encoding='utf-8') as f:
                self._translations[self._current_locale] = json.load(f)
        else:
            # Try language without region (e.g., 'de' from 'de_DE')
            lang = self._current_locale.split('_')[0]
            lang_file = locale_dir / f'{lang}.json'
            if lang_file.exists():
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self._translations[lang] = json.load(f)

    def gettext(self, key: str, **kwargs) -> str:
        """Get translated string for the given key.

        Args:
            key: Translation key (e.g., 'ui.button.login')
            **kwargs: Format parameters for string interpolation

        Returns:
            Translated and formatted string, or ?key? if not found
        """
        # Try current locale
        if self._current_locale in self._translations:
            text = self._translations[self._current_locale].get(key)
            if text:
                return text.format(**kwargs) if kwargs else text

        # Fallback to English
        if 'en' in self._translations:
            text = self._translations['en'].get(key)
            if text:
                return text.format(**kwargs) if kwargs else text

        # Missing key - return ?key? and log warning
        log.warning(f"Translation key not found: {key} (plugin: {self._manifest.id})")
        return f"?{key}?"

    def reload_translations(self):
        """Reload translations when locale changes"""
        self._translations.clear()
        self._load_translations()
```

---

## Translation Workflow

### For Plugin Developers

1. Create `locale/en.json` with English strings
2. Add translation keys to code using `api.gettext()`
3. Create additional locale files (e.g., `de.json`, `fr.json`)
4. Add translations to MANIFEST.toml for name/description
5. Test with different locales

### For Translators

1. Copy `en.json` to new locale file (e.g., `de.json`)
2. Translate all values (keep keys unchanged)
3. Test translations
4. Submit PR or send to plugin developer

### For Website

1. Scan plugin repositories
2. Extract `name_i18n` and `description_i18n` from MANIFEST.toml
3. Include in registry JSON
4. Serve to clients

---

## Best Practices

1. **Always provide `en.json`** - Required fallback
2. **Use consistent key naming** - Follow conventions (ui.*, error.*, etc.)
3. **Keep translations in sync** - All locale files should have same keys
4. **Use placeholders** - For dynamic content: `{variable}`
5. **Test with multiple locales** - Verify fallback behavior
6. **Document context** - Add comments explaining when/where text is used
7. **Keep strings short** - UI space is limited
8. **Avoid concatenation** - Use complete sentences with placeholders

---

## Locale Codes

Use standard locale codes:

- `en` - English
- `de` - German
- `fr` - French
- `es` - Spanish
- `it` - Italian
- `ja` - Japanese
- `zh_CN` - Chinese (Simplified)
- `zh_TW` - Chinese (Traditional)
- `pt_BR` - Portuguese (Brazilian)
- `ru` - Russian

---

## Example: Complete Translation Setup

### MANIFEST.toml
```toml
name = "ListenBrainz Submitter"
description = "Submit your music to ListenBrainz"

[name_i18n]
de = "ListenBrainz-Submitter"
fr = "Soumetteur ListenBrainz"

[description_i18n]
de = "Submit listens deine Musik zu ListenBrainz"
fr = "Submit listensz votre musique sur ListenBrainz"
```

### locale/en.json
```json
{
  "ui.button.login": "Login to ListenBrainz",
  "ui.button.logout": "Logout",
  "error.auth_failed": "Authentication failed",
  "status.submit listensd": "Submit listensd {count} tracks"
}
```

### locale/de.json
```json
{
  "ui.button.login": "Bei ListenBrainz anmelden",
  "ui.button.logout": "Abmelden",
  "error.auth_failed": "Authentifizierung fehlgeschlagen",
  "status.submit listensd": "{count} Titel geübermittelt Hördaten"
}
```

### __init__.py
```python
from picard.plugin3 import PluginApi

def enable(api: PluginApi):
    _ = api.gettext

    # Use translations
    login_text = _('ui.button.login')
    logout_text = _('ui.button.logout')

    # With parameters
    status = _('status.submit listensd', count=5)
```

---

## Weblate Integration (Future)

For collaborative translation, plugins could integrate with Weblate:

1. Plugin repository connected to Weblate
2. Translators contribute via web interface
3. Translations automatically committed to repository
4. Plugin developer merges translation updates

**Community Feedback:**
> **rdswift:** "Perhaps the final plugin developer documentation could contain links to information pertaining to setup and use of a weblate server to help facilitate the process for plugins not managed by Picard, and ultimately provide more user-friendly plugins."

**Recommendation:** Include in plugin developer documentation:
- Link to Weblate setup guide
- Instructions for connecting plugin repository
- Configuration examples
- Best practices for managing translation PRs
- Information about MusicBrainz Weblate instance (if available for community plugins)

---

## See Also

- **[MANIFEST.md](MANIFEST.md)** - MANIFEST.toml specification
- **[REGISTRY.md](REGISTRY.md)** - Registry metadata translations
- **[WEBSITE.md](WEBSITE.md)** - Website translation extraction


---

## PROPOSED: Alternative Translation Approach (Under Discussion)

**Note:** This section describes a proposed alternative to the key-based approach documented above. It is not yet implemented and is under active discussion.

### Motivation

The current key-based approach (`api.gettext('ui.button.login')`) has readability issues - developers must look up JSON files to understand what text is displayed. This is especially problematic for UI code where readability is important.

Traditional gettext uses the actual English text as the key (`_("Login to ListenBrainz")`), which is much more readable but has stability issues when text changes.

### Proposed Solution: Hybrid Text + Key Approach

Combine the readability of text-in-code with the stability of keys:

```python
api.tr("Login to ListenBrainz", key="ui.button.login")
api.tr("Processing {filename}...", key="status.processing", filename=file)
```

### Key Changes

**1. Use `api.tr()` instead of `api.gettext()`**
- Avoids confusion with Picard's gettext `_()`
- Allows plugins to use both Picard and plugin translations simultaneously
- Familiar to Qt developers (`QObject.tr()`)

```python
from picard.i18n import gettext as _  # Picard's translations

def enable(api: PluginApi):
    # Both available without conflict
    picard_text = _("Save")  # Picard's UI string
    plugin_text = api.tr("Login to ListenBrainz", key="ui.button.login")  # Plugin's string
```

**2. Declare source locale in MANIFEST.toml**

```toml
source_locale = "en_US"  # Default if not specified
# Can be: "en_GB", "de_DE", "pt_BR", "fr_CA", etc.
```

This allows:
- Plugin developers to write code in their native language
- Regional variants (en_US vs en_GB, pt_BR vs pt_PT, etc.)
- Inclusive development for non-English speakers

**3. Source locale text lives in code**

```python
# German developer
api.tr("Bei ListenBrainz anmelden", key="ui.button.login")
```

```toml
source_locale = "de_DE"
```

No `de_DE.json` needed - German text is in the code. Other locales in JSON:

```json
// en_US.json
{
  "ui.button.login": "Login to ListenBrainz"
}

// fr_FR.json
{
  "ui.button.login": "Connexion à ListenBrainz"
}
```

### Lookup Logic

1. If current locale matches source_locale → return text from code
2. Otherwise → look up key in current locale JSON (with fallback to language without region)
3. Fall back to source locale text from code if translation not found

### Benefits

- **Readable code**: Actual text visible, not cryptic keys
- **Inclusive**: Developers can write in their native language
- **Organized**: Keys provide namespacing and stability
- **No redundant source JSON at runtime**: Source language in code
- **Stable**: Changing text doesn't break translations (key remains same)
- **Clear fallback**: Source text always available

### Example: Complete Setup

**MANIFEST.toml**
```toml
name = "ListenBrainz Submitter"
source_locale = "en_US"

[name_i18n]
de = "ListenBrainz-Submitter"
fr = "Soumetteur ListenBrainz"

[description_i18n]
de = "Sende deine Musik zu ListenBrainz"
fr = "Soumettez votre musique sur ListenBrainz"
```

**__init__.py**
```python
from picard.plugin3 import PluginApi
from picard.i18n import gettext as _  # Picard's translations

def enable(api: PluginApi):
    # Use Picard's translations for standard UI
    menu_text = _("Plugins")  # Picard translates this

    # Use plugin translations for plugin-specific text
    login_text = api.tr("Login to ListenBrainz", key="ui.button.login")
    logout_text = api.tr("Logout", key="ui.button.logout")

    # With parameters
    status = api.tr("Submitted {count} tracks", key="status.submitted", count=5)
    error = api.tr("Network error: {error}", key="error.network", error="Timeout")
```

**locale/de_DE.json**
```json
{
  "ui.button.login": "Bei ListenBrainz anmelden",
  "ui.button.logout": "Abmelden",
  "status.submitted": "{count} Titel übermittelt",
  "error.network": "Netzwerkfehler: {error}"
}
```

**locale/fr_FR.json**
```json
{
  "ui.button.login": "Connexion à ListenBrainz",
  "ui.button.logout": "Déconnexion",
  "status.submitted": "{count} pistes soumises",
  "error.network": "Erreur réseau: {error}"
}
```

### Qt Integration

Plugin translations work alongside Qt's translation system:

```python
from PyQt6.QtWidgets import QDialog, QPushButton, QLabel

class MyPluginDialog(QDialog):
    def __init__(self, api):
        super().__init__()
        self.api = api

        # Qt's built-in translations (inherited from QObject)
        ok_button = QPushButton(self.tr("&OK"))
        cancel_button = QPushButton(self.tr("&Cancel"))

        # Plugin-specific translations
        title = self.api.tr("ListenBrainz Options", key="options.title")
        label = QLabel(self.api.tr("Username:", key="options.username"))
```

- `self.tr()` → Qt's translation system (for standard UI elements)
- `self.api.tr()` → Plugin's translation system (for plugin-specific text)
- Both use the same locale from `QLocale().name()`

### Open Question: Translator Workflow

**Challenge:** Translators (especially via Weblate) need a source file to translate from.

**Possible approaches:**

**A. Require source locale JSON (accept duplication)**
- Developer maintains both code text and source locale JSON
- Simple, no tools required
- Picard validates they match at runtime and warns on mismatch
- Standard translator workflow works out of the box

**B. Optional extraction tool**
- Tool scans code for `api.tr()` calls, generates source locale JSON
- Optional for developers who want it
- Adds complexity, requires tooling

**C. Generated reference file**
- `_source.json` auto-generated for translators (not used at runtime)
- Requires CI/tooling setup
- Separates translator needs from runtime needs

**Decision pending:** Need to balance developer convenience, translator experience, and implementation complexity.

### Implementation Notes

```python
class PluginApi:
    def __init__(self, manifest: PluginManifest, tagger) -> None:
        self._manifest = manifest
        self._tagger = tagger
        self._translations = {}
        self._source_locale = manifest.source_locale or "en_US"
        self._current_locale = QLocale().name()
        self._load_translations()

    def tr(self, text: str, key: str = None, **kwargs) -> str:
        """Get translated string.

        Args:
            text: Source locale text (always provided)
            key: Translation key (optional but recommended)
            **kwargs: Format parameters for string interpolation

        Returns:
            Translated and formatted string
        """
        # If no key provided, just return the text (no translation)
        if key is None:
            return text.format(**kwargs) if kwargs else text

        # If current locale is source locale, use text from code
        if self._current_locale == self._source_locale:
            return text.format(**kwargs) if kwargs else text

        # Try current locale (e.g., "de_DE")
        if self._current_locale in self._translations:
            translated = self._translations[self._current_locale].get(key)
            if translated:
                return translated.format(**kwargs) if kwargs else translated

        # Try language without region (e.g., "de" from "de_DE")
        lang = self._current_locale.split('_')[0]
        if lang in self._translations:
            translated = self._translations[lang].get(key)
            if translated:
                return translated.format(**kwargs) if kwargs else translated

        # Fall back to source locale text from code
        return text.format(**kwargs) if kwargs else text
```

### Comparison with Current Approach

**Current (key-based):**
```python
api.gettext('ui.button.login')  # What does this say?
```

**Proposed (text + key):**
```python
api.tr("Login to ListenBrainz", key="ui.button.login")  # Clear what it says
```

**Tradeoffs:**
- Current: Less verbose, but harder to read
- Proposed: More verbose, but self-documenting and more flexible

---

**Status:** This proposal is under discussion. Feedback welcome on the MusicBrainz community forums or issue tracker.
