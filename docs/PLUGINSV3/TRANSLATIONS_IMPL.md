# Plugin Translation System - Implementation Plan

This document outlines the implementation plan for the Plugin v3 translation system as documented in [TRANSLATIONS.md](TRANSLATIONS.md).

---

## Phase 1: Core Translation Infrastructure (Minimal Viable)

### Step 1.1: Add `source_locale` to MANIFEST.toml schema
**File:** `picard/plugin3/manifest.py`
- Add `source_locale: str | None = None` field to `PluginManifest` dataclass
- **Default to `"en"` if not specified**
- Update validation to accept locale codes (e.g., `en`, `en_US`, `de_DE`, `pt_BR`)
- **Test:** `test/test_plugin3_manifest.py`
  - Load MANIFEST.toml without `source_locale` → defaults to `"en"`
  - Load with `source_locale = "de_DE"` → uses `"de_DE"`

### Step 1.2: Implement basic translation loading
**File:** `picard/plugin3/api.py` (or new `picard/plugin3/i18n.py`)
- Add `_load_translations()` method to `PluginApi`
- Set `self._source_locale = manifest.source_locale or "en"`
- Load JSON files from `locale/` directory
- Store in `self._translations` dict: `{locale: {key: value}}`
- Get current locale from `QLocale().name()`
- **Test:** `test/test_plugin3_translations.py`
  - No `source_locale` in MANIFEST → uses `"en"`
  - Load `locale/en.json` and `locale/de.json`, verify dict structure

### Step 1.3: Implement `api.tr()` method
**File:** `picard/plugin3/api.py`
- Add `tr(key: str, text: str = None, **kwargs) -> str` method
- Implement fallback logic:
  1. If current locale == source_locale and text provided → return text
  2. Try current locale (e.g., `de_DE`)
  3. Try language without region (e.g., `de`)
  4. Fall back to text parameter
  5. Return `?key?` with warning
- Handle string formatting with `**kwargs`
- **Test:** `test/test_plugin3_translations.py`
  - Source locale defaults to `"en"` when not specified
  - Key exists in current locale → returns translation
  - Key missing → returns text parameter
  - Key and text missing → returns `?key?`
  - String formatting with `{variable}` works

### Step 1.4: Basic integration test
**File:** `test/test_plugin3_translations.py`
- Create test plugin with `locale/en.json` and `locale/de.json`
- Test `api.tr()` with different locales
- Test fallback behavior
- **Test:** End-to-end translation lookup

---

## Phase 2: Plural Forms Support

### Step 2.1: Implement CLDR plural rules
**File:** `picard/plugin3/i18n.py` (new module)
- Create `get_plural_form(locale: str, n: int) -> str` function
- Implement CLDR rules for common languages (en, de, fr, es, ru, pl, ar)
- Return one of: `zero`, `one`, `two`, `few`, `many`, `other`
- **Test:** `test/test_plugin3_plural_rules.py`
  - Verify plural forms for different numbers in different languages
  - English: n=1 → "one", n=2 → "other"
  - Polish: n=1 → "one", n=2 → "few", n=5 → "many"
  - Arabic: n=0 → "zero", n=1 → "one", n=2 → "two"

### Step 2.2: Implement `api.trn()` method
**File:** `picard/plugin3/api.py`
- Add `trn(key: str, singular: str = None, plural: str = None, n: int = 0, **kwargs) -> str` method
- Look up plural object: `translations[key]` → `{one: "...", other: "..."}`
- Get plural form from CLDR rules
- Fall back to `other` if specific form not available
- Handle text parameters for source locale (singular → "one", plural → "other")
- **Test:** `test/test_plugin3_translations.py`
  - English: n=1 → "one", n=5 → "other"
  - Polish: n=2 → "few", n=5 → "many"
  - Fallback to singular/plural parameters when translation missing
  - Source locale uses singular/plural from code

---

## Phase 3: Qt Designer Integration

### Step 3.1: Implement `PluginTranslator` class
**File:** `picard/plugin3/i18n.py`
- Create `PluginTranslator(QTranslator)` class
- Override `translate(context, source_text, disambiguation, n)` method
- Generate key: `f"qt.{context}.{source_text}"`
- Call `api.tr(key, source_text)` for translation
- **Test:** `test/test_plugin3_qt_translator.py`
  - Mock `QCoreApplication.translate()` calls
  - Verify key generation: "VariablesDialog" + "Variable" → "qt.VariablesDialog.Variable"
  - Verify fallback to source_text when translation missing

### Step 3.2: Auto-install translator in PluginApi
**File:** `picard/plugin3/api.py`
- Add `_install_qt_translator()` method
- Call in `__init__()` after loading translations
- Create `PluginTranslator` instance
- Call `QCoreApplication.installTranslator(translator)`
- Store reference in `self._qt_translator` to prevent GC
- **Test:** `test/test_plugin3_qt_translator.py`
  - Verify translator is installed
  - Verify it's called for `.ui` files
  - Verify it doesn't interfere with Picard's own translations

### Step 3.3: Integration test with .ui file
**File:** `test/test_plugin3_qt_translator.py`
- Create test `.ui` file with translatable strings
- Generate Python code with `pyuic6`
- Load dialog, verify translations work
- Test with different locales
- **Test:** `.ui` file strings use plugin translations automatically

---

## Phase 4: Extraction Tool (Optional but Recommended)

### Step 4.1: AST parser for `api.tr()` calls
**File:** `picard/plugin3/tools/extract_translations.py` (new)
- Use Python `ast` module to parse plugin code
- Find all `api.tr()` and `api.trn()` calls
- Extract key and text parameters
- Handle both positional and keyword arguments
- **Test:** `test/test_plugin3_extraction_tool.py`
  - Parse sample code with various `api.tr()` patterns
  - Verify extracted keys and text
  - Handle missing text → generate `?key?` placeholder

### Step 4.2: .ui file parser
**File:** `picard/plugin3/tools/extract_translations.py`
- Use `xml.etree.ElementTree` to parse `.ui` files
- Find all `<string>` elements
- Extract context (class name) and text
- Generate `qt.{context}.{text}` keys
- **Test:** `test/test_plugin3_extraction_tool.py`
  - Parse sample `.ui` file
  - Verify extracted keys with `qt.` prefix
  - Handle special characters in text

### Step 4.3: JSON generator
**File:** `picard/plugin3/tools/extract_translations.py`
- Combine extracted keys from code and `.ui` files
- Generate JSON structure
- Use `?key?` for missing text
- Handle plural forms (nested objects with "one", "other", etc.)
- Sort keys alphabetically
- **Test:** `test/test_plugin3_extraction_tool.py`
  - Generate `locale/en.json` from sample plugin
  - Verify JSON structure
  - Verify plural forms are nested objects
  - Verify `?key?` placeholders for missing text

### Step 4.4: CLI command
**File:** `picard/plugin3/cli.py`
- Add `--extract-translations <plugin_dir>` command
- Call extraction tool
- Write to `locale/{source_locale}.json`
- Support `--format json|toml` option (JSON only initially)
- **Test:** `test/test_plugin3_extraction_tool.py`
  - Run on sample plugin
  - Verify generated file exists and is valid JSON
  - Verify source_locale from MANIFEST.toml is used

---

## Phase 5: TOML Support (Future)

### Step 5.1: TOML file loading
**File:** `picard/plugin3/i18n.py`
- Add TOML parsing support (using `tomllib` in Python 3.11+)
- Support both flat keys and nested tables
- Convert nested tables to flat keys internally
- **Test:** `test/test_plugin3_translations.py`
  - Load `locale/de.toml`
  - Verify same behavior as JSON
  - Test both flat and nested structures

### Step 5.2: Extraction tool TOML output
**File:** `picard/plugin3/tools/extract_translations.py`
- Add `--format toml` option
- Generate TOML structure with nested tables
- Use sections for key prefixes (e.g., `[ui]`, `[error]`)
- **Test:** `test/test_plugin3_extraction_tool.py`
  - Generate `locale/en.toml`
  - Verify TOML structure with nested tables
  - Verify it loads correctly

---

## Testing Strategy

### Unit Tests
- `test/test_plugin3_manifest.py` - MANIFEST.toml schema validation
- `test/test_plugin3_translations.py` - Core `api.tr()` and `api.trn()` functionality
- `test/test_plugin3_plural_rules.py` - CLDR plural form rules
- `test/test_plugin3_qt_translator.py` - Qt Designer integration
- `test/test_plugin3_extraction_tool.py` - Translation extraction tool

### Integration Tests
- Create sample plugin with translations in `test/data/plugin3/`
- Test with different locales (en, de, fr, pl)
- Test `.ui` file integration
- Test extraction tool end-to-end

### Manual Testing
- Test with real plugin (e.g., ViewVariables)
- Switch Picard locale in Options, verify translations change
- Test fallback behavior with missing translations
- Test with missing translation files

---

## Dependencies

**Required:**
- `PyQt6` (already in Picard)
- `tomllib` (Python 3.11+) or `tomli` (backport for Python 3.10)

**Optional:**
- `babel` - For advanced CLDR plural rules (can implement basic rules manually)

---

## Estimated Effort

- **Phase 1:** 1-2 days (core functionality)
- **Phase 2:** 1 day (plural forms)
- **Phase 3:** 1 day (Qt integration)
- **Phase 4:** 2-3 days (extraction tool)
- **Phase 5:** 1 day (TOML support)

**Total:** 6-9 days for complete implementation

---

## Minimal Viable Product (MVP)

For initial release, implement:
- ✅ Phase 1 (core translations)
- ✅ Phase 2 (plurals)
- ✅ Phase 3 (Qt integration)
- ⏸️ Phase 4 (extraction tool - can be manual initially)
- ⏸️ Phase 5 (TOML - JSON is sufficient initially)

**MVP Effort:** 3-4 days

---

## Implementation Order

1. **Phase 1.1-1.3** - Core `api.tr()` functionality (Day 1)
2. **Phase 2.1-2.2** - Plural forms with `api.trn()` (Day 2)
3. **Phase 3.1-3.3** - Qt Designer integration (Day 3)
4. **Integration testing** - Test with real plugin (Day 4)
5. **Phase 4** - Extraction tool (Days 5-7, optional)
6. **Phase 5** - TOML support (Day 8, optional)

---

## Notes

- Keep implementation minimal - avoid over-engineering
- Focus on common use cases (English, German, French, Spanish)
- CLDR plural rules can start simple and be extended later
- Extraction tool is nice-to-have but not critical for MVP
- TOML support can wait until there's demand from plugin developers

---

## See Also

- **[TRANSLATIONS.md](TRANSLATIONS.md)** - User-facing documentation
- **[API.md](API.md)** - PluginApi documentation
- **[MANIFEST.md](MANIFEST.md)** - MANIFEST.toml specification
