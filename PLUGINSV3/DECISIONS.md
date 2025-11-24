# Plugin v3 Design Decisions

This document records design decisions made during Plugin v3 development, including rationale and alternatives considered.

---

## Resolved Questions

### Q1: Should install/uninstall hooks exist?

**Decision:** NO

**Rationale:**
- Keeps system simple
- Most plugins don't need it
- Plugins can do setup in `enable()` and cleanup in `disable()`
- Can add later if needed

**Status:** CLOSED

---

### Q2: Is TOML the right format for MANIFEST?

**Decision:** YES, keep TOML

**Rationale:**
- Already implemented and working
- Python 3.11+ has native support (tomllib)
- More human-readable than JSON
- Less complex than YAML
- Used by pyproject.toml (familiar to Python devs)
- Good balance of simplicity and features

**Alternatives considered:**
- JSON: Less human-friendly, no comments
- YAML: Too complex, security issues
- INI: Too limited

**Status:** CLOSED

---

### Q3: How should plugins provide translations?

**Decision:** Use JSON-based translations

**Rationale:**
- `.mo` files are compiled, binary, platform-specific
- JSON is portable, human-readable, git-friendly
- Simple flat structure with dot notation
- Easy to parse and use
- No compilation step needed

**Format:**
```json
{
  "ui.button.login": "Login",
  "error.network": "Network error: {error}"
}
```

**Alternatives considered:**
- gettext (.mo files): Binary, not portable
- YAML: Overkill for simple key-value
- Nested JSON: More complex to use

**Status:** CLOSED

See [TRANSLATIONS.md](TRANSLATIONS.md) for details.

---

### Q4: Plugin life cycle details?

**Decision:** Simple enable/disable model

**Life cycle:**
1. **Discovered** - Plugin found in plugins3 directory
2. **Loaded** - MANIFEST.toml parsed, module loaded
3. **Enabled** - `plugin_main()` called, hooks registered
4. **Disabled** - Hooks unregistered (module stays loaded)

**Rationale:**
- Simple and predictable
- No complex state machine
- Matches Picard 2 behavior (filtering, not unloading)
- Safer than unload/reload

**Status:** CLOSED

---

### Q5: How to handle blacklisting plugins?

**Decision:** Website-based blacklist with client enforcement

**Approach:**
- Centralized blacklist in registry JSON
- Checked on install and startup
- Supports repository-level patterns (e.g., `https://github.com/badorg/*`)
- Can be updated independently of Picard releases

**Rationale:**
- Fast response to malicious plugins
- No Picard release needed for updates
- Centralized management
- Repository patterns allow blocking entire organizations

**Status:** CLOSED

See [REGISTRY.md](REGISTRY.md) for blacklist specification.

---

### Q6: Categorization and Trust Levels?

**Decision:** Implement both category and trust level

**Categories (functional):**
- `metadata` - Metadata providers and processors
- `coverart` - Cover art providers
- `ui` - User interface enhancements
- `scripting` - Script functions and variables
- `formats` - File format support
- `other` - Miscellaneous

**Trust Levels (security/quality):**
- `official` - Team maintained, reviewed (in registry)
- `trusted` - Well-known authors, not reviewed (in registry)
- `community` - Other authors, not reviewed (in registry)
- `unregistered` - Not in registry (client-side only)

**Usage:**
- Category: For filtering/browsing ("show me all metadata plugins")
- Trust level: For security warnings ("this plugin is not reviewed")

**Rationale:**
- Categories help users find plugins
- Trust levels help users make security decisions
- Dual classification provides both discovery and safety

**Status:** CLOSED

See [REGISTRY.md](REGISTRY.md) for trust level details.

---

### Q7: Extra data files API?

**Decision:** Simple file access via plugin directory

**Approach:**
```python
def plugin_main(api: PluginApi):
    plugin_dir = api.plugin_dir
    data_file = plugin_dir / 'data' / 'config.json'
    with open(data_file) as f:
        data = json.load(f)
```

**Rationale:**
- Simple and flexible
- No special API needed
- Plugins can organize files as they want
- Standard Python file operations

**Status:** CLOSED

---

### Q8: Additional extension points?

**Decision:** Start with core set, add more as needed

**Initial extension points:**
- Album/file metadata hooks
- UI actions (album, file, track)
- File processors
- Cover art providers
- Metadata providers
- Script functions/variables
- Options pages

**Rationale:**
- Cover most common use cases
- Can add more based on plugin developer feedback
- Better to start minimal and expand

**Status:** CLOSED

---

### Q9: ZIP plugin support?

**Decision:** NO, git-only for now

**Rationale:**
- Git provides versioning, updates, and history
- Simpler implementation
- Easier to review code
- Can add ZIP support later if needed

**Future consideration:**
- Could support ZIP for offline/airgapped environments
- Would need signature verification
- Lower priority than core functionality

**Status:** CLOSED

---

### Q10: Manifest field inconsistencies?

**Decision:** Standardize on plural forms and arrays

**Changes:**
- `author` → `authors` (array)
- `category` → `categories` (array)
- `api_versions` → `api` (array)

**Rationale:**
- Consistent naming
- Arrays support multiple values naturally
- Matches common conventions

**Status:** CLOSED

See [MANIFEST.md](MANIFEST.md) for field reference.

---

### Q11: Multi-lingual `name` field?

**Decision:** Use `name_i18n` and `description_i18n` tables in MANIFEST.toml

**Format:**
```toml
name = "Last.fm Scrobbler"
description = "Scrobble your music to Last.fm"

[name_i18n]
de = "Last.fm-Scrobbler"
fr = "Scrobbleur Last.fm"

[description_i18n]
de = "Scrobble deine Musik zu Last.fm"
fr = "Scrobblez votre musique sur Last.fm"
```

**Rationale:**
- Single source of truth
- Website extracts and includes in registry
- Simple format
- Easy to maintain

**Status:** CLOSED

See [TRANSLATIONS.md](TRANSLATIONS.md) for details.

---

### Q12: Legacy plugin coexistence?

**Decision:** Support both v2 and v3 plugins simultaneously

**Approach:**
- v2 plugins in `plugins/` directory
- v3 plugins in `plugins3/` directory
- Both systems run in parallel
- Gradual migration path

**Rationale:**
- Smooth transition for users
- Plugin developers have time to migrate
- No breaking changes for existing users
- Can deprecate v2 later

**Status:** CLOSED

See [MIGRATION.md](MIGRATION.md) for migration guide.

---

## Open Questions Requiring Decisions

### Q13: Plugin dependencies?

**Question:** How should plugins declare dependencies on other plugins or Python packages?

**Options:**
1. No dependency system (current)
2. Declare in MANIFEST.toml, manual installation
3. Automatic dependency resolution (like pip)

**Status:** OPEN - Defer to Phase 2 or 3

---

### Q14: Plugin ratings and reviews?

**Question:** Should the registry include user ratings and reviews?

**Options:**
1. No ratings (current)
2. Simple star ratings
3. Full review system (like browser extensions)

**Status:** OPEN - Defer to Phase 3 or later

---

### Q15: Plugin update notifications?

**Question:** How should users be notified of plugin updates?

**Options:**
1. Manual check via CLI (current)
2. Automatic check on startup
3. Background check with notifications
4. Update badges in GUI

**Status:** OPEN - Defer to Phase 2

---

## Questions for Future Consideration

### Plugin Marketplace

- Should there be a web-based plugin marketplace?
- How to handle plugin submissions?
- Review process for community plugins?

### Plugin Analytics

- Should plugins be able to report usage statistics?
- Privacy considerations?
- Opt-in vs opt-out?

### Plugin Signing

- Code signing for official plugins?
- Certificate infrastructure?
- Verification process?

---

## Decision Priority

| Priority | Question | Phase | Impact |
|----------|----------|-------|--------|
| P0 | Q1-Q12 | 1 | ✅ Resolved |
| P1 | Q15 | 2 | Medium |
| P2 | Q13 | 2-3 | Low |
| P3 | Q14 | 3+ | Low |

---

## See Also

- **[ROADMAP.md](ROADMAP.md)** - Development phases
- **[MANIFEST.md](MANIFEST.md)** - MANIFEST.toml specification
- **[REGISTRY.md](REGISTRY.md)** - Registry system
- **[SECURITY.md](SECURITY.md)** - Security model
- **[TRANSLATIONS.md](TRANSLATIONS.md)** - Translation system
