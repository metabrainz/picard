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

**Community Feedback:**
> **rdswift:** "I concur with the 'No' recommendation for the reasons outlined in the rationale provided."

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

**Community Feedback:**
> **rdswift:** "I concur with the recommendation to use JSON-based translations. I also support the recommendations with respect to plurals: Use babel library for plural rules, support nested dict format for plurals in JSON, document plural forms in plugin dev guide, configure Weblate to handle plural forms. Perhaps the final plugin developer documentation could contain links to information pertaining to setup and use of a weblate server to help facilitate the process for plugins not managed by Picard."

**Status:** CLOSED

See [TRANSLATIONS.md](TRANSLATIONS.md) for details.

---

### Q4: Plugin life cycle details?

**Decision:** Simple enable/disable model with `enable()` and optional `disable()` functions

**Life cycle:**
1. **Discovered** - Plugin found in plugins3 directory
2. **Loaded** - MANIFEST.toml parsed, module loaded
3. **Enabled** - `enable(api)` called, hooks registered
4. **Disabled** - `disable()` called (if present), hooks unregistered (module stays loaded)

**Functions:**
- `enable(api: PluginApi)` - Required, called when plugin is enabled
- `disable()` - Optional, called when plugin is disabled (for cleanup)

**Rationale:**
- Simple and predictable
- No complex state machine
- Matches Picard 2 behavior (filtering, not unloading)
- Safer than unload/reload
- `enable()`/`disable()` names match user actions
- Optional `disable()` for flexibility

**Community Feedback:**
> **rdswift:** "I support the minimal state machine as presented."

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

**Community Feedback:**
> **rdswift:** "This may seem a bit harsh, but should we also include provision for blacklisting a GitHub account in addition to being able to blacklist specific plugins? This could perhaps be a different trust level ('blacklisted')."

**Note:** The repository pattern support (`https://github.com/badorg/*`) effectively allows blacklisting entire GitHub accounts/organizations. A separate 'blacklisted' trust level is not needed since blacklisted plugins are simply not installable.

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
def enable(api: PluginApi):
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

**Community Feedback:**
> **rdswift:** "I support the decision of using a reactive approach."

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

**Community Feedback:**
> **rdswift:** "I concur with the 'No' recommendation for the reasons outlined in the rationale provided."

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

**Community Feedback:**
> **rdswift:** "I concur with the recommendation to use a single string for the reasons outlined in the rationale provided."

**Status:** CLOSED

See [MANIFEST.md](MANIFEST.md) for field reference.

---

### Q11: Multi-lingual `name` field?

**Decision:** Use `name_i18n` and `description_i18n` tables in MANIFEST.toml

**Format:**
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

**Rationale:**
- Single source of truth
- Website extracts and includes in registry
- Simple format
- Easy to maintain

**Community Feedback:**
> **rdswift:** "I concur with the recommendation to use a single string for the name, based on the reasons outlined in the rationale provided."

**Status:** CLOSED

See [TRANSLATIONS.md](TRANSLATIONS.md) for details.

---

### Q12: Legacy plugin coexistence?

**Decision:** NO - v3 replaces v2 completely

**Approach:**
- Only v3 plugins supported
- v2 plugin system removed
- Breaking change requiring migration
- No parallel operation

**Rationale:**
- Cleaner codebase without dual systems
- Forces migration to better architecture
- Avoids maintenance burden of two systems
- Clear break for major version

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

**Community Feedback:**
> **rdswift:** "I agree with the recommendation to not allow / support dependencies between plugins. Generally speaking, I believe that plugins should be stand-alone. This could be revisited if a sufficiently compelling use case were presented, where a significant amount of code introduces functionality in one plugin that could be used in other plugins."

**Status:** OPEN - Defer to Phase 2 or 3

---

### Q14: Plugin ratings and reviews?

**Question:** Should the registry include user ratings and reviews?

**Options:**
1. No ratings (current)
2. Simple star ratings
3. Full review system (like browser extensions)

**Community Feedback:**
> **rdswift:** "This is a nice idea, but I fear that the effort required to implement and maintain such a system would exceed the value provided. Perhaps this concern is unfounded, and it might be something managed fairly easily through the use of CritiqueBrainz."

**Status:** OPEN - Defer to Phase 3 or later

---

### Q15: Plugin update notifications?

**Question:** How should users be notified of plugin updates?

**Options:**
1. Manual check via CLI (current)
2. Automatic check on startup
3. Background check with notifications
4. Update badges in GUI

**Community Feedback:**
> **rdswift:** "I agree with the recommendation to initially do manually checking only (for Phase 1) and ultimately implement automatic checking during startup (Phase 4). I suggest that there be a menu item, either from the main menu or on the 'Plugins' option page, to always allow initiation of a manual update check. I also recommend that the option setting to disable the automatic checking during startup, which exists in the current release of Picard, be retained. Another option might be to automatically perform the update check (if enabled) in the background, and display a notice (possibly right-justified on the same line as the main menu bar) indicating that an update is available. This would allow checking to take place without significantly impacting the startup UI. This is the approach that some other applications take (e.g. Calibre). I also suggest that a user setting regarding optional notification of pre-release versions could be included, similar to the setting regarding update checking for Picard itself."

**Recommendations based on feedback:**
- Phase 1: Manual check only (`picard-plugins --check-updates`)
- Phase 2: Add menu item for manual check
- Phase 4: Automatic background check on startup (with disable option)
- Consider notification area indicator (like Calibre)
- Add setting for pre-release version notifications

**Status:** OPEN - Defer to Phase 2

---

### Q16: Plugin configuration cleanup?

**Question:** What should happen to plugin configuration when uninstalling?

**Options:**
1. Always keep configuration
2. Always delete configuration
3. Prompt user during uninstall
4. Allow later cleanup via separate command

**Community Feedback:**
> **rdswift:** "I suggest a combination of options C and D. The process would allow the user to delete the configuration immediately by prompting upon uninstall, and allow for later deletion if the user changes their mind about their decision to keep the configuration during the uninstall."

**Recommendation:**
- Prompt during uninstall: "Delete plugin configuration? [y/N]"
- Add `--purge` flag to force deletion
- Add `picard-plugins --clean-config <name>` command for later cleanup
- Keep config by default for safety

**Status:** OPEN - Implement in Phase 1.7

---

### Q17: Plugin sandboxing / security?

**Question:** Should plugins be sandboxed?

**Decision:** NO - Use trust-based approach

**Rationale:** See [SECURITY.md](SECURITY.md) for detailed analysis

**Community Feedback:**
> **rdswift:** "I agree with the recommendation to use a trust-based approach, based on the rationale and security model information provided."

**Status:** CLOSED

---

### Q18: Plugin versioning in registry?

**Question:** Should the registry track plugin versions or rely on git?

**Decision:** Git-based approach only

**Rationale:**
- Git already provides version history
- Tags for releases
- Simpler registry schema
- No version sync issues

**Community Feedback:**
> **rdswift:** "I agree with the recommendation to use the Git-based approach only, and not to track versions in the registry."

**Status:** CLOSED

---

### Q19: Plugin disable vs unload?

**Question:** Should disabling a plugin unload it from memory?

**Decision:** Keep loaded, de-register hooks

**Rationale:**
- Simpler implementation
- Matches Picard 2 behavior
- Safer than unload/reload
- Module stays in memory until restart

**Community Feedback:**
> **rdswift:** "I agree with the recommendation to keep the plugin loaded (during the current session) but de-register the hooks."

**Status:** CLOSED

---

### Q20: Weblate project structure?

**Question:** How should plugins be organized in Weblate?

**Decision:** One component per plugin

**Rationale:**
- Clear separation
- Independent translation progress
- Easier management

**Community Feedback:**
> **rdswift:** "I agree with the recommendation of one component per plugin. I assume that the interaction with Weblate will be through the master branch of the plugin. Will this cause a problem of translations not being made available to a version identified via a tag (as per the versioning plan) when provided as commits by Weblate after the tag has been set on a commit in the branch? Will a new version tag need to be assigned to pick up the updated translations?"

**Note:** Translations committed by Weblate after a version tag would require a new version tag to be included in that release. This is standard practice - translations are part of the release cycle.

**Status:** CLOSED

---

### Q21: Plugin testing / CI?

**Question:** Should plugins be required to have tests?

**Decision:** Required for official plugins only, encouraged for all

**Rationale:**
- Official plugins need quality assurance
- Community plugins can opt-in
- Don't want to create barriers to contribution

**Community Feedback:**
> **rdswift:** "I agree with the recommendation that tests should be required for Picard Team plugins only. The plugin developer documentation should strongly encourage that tests be included for all plugins, and outline how the tests are to be included."

**Status:** CLOSED

---

### Q22: Plugin metrics / analytics?

**Question:** Should plugins report usage metrics?

**Options:**
1. No metrics (current)
2. Opt-in anonymous metrics
3. Mandatory metrics

**Community Feedback:**
> **rdswift:** "I agree that, if the decision at some point is to support metrics, this should be 'opt-in' and anonymous as outlined in Option B. I believe that metrics could be useful for determining priority of support requests for plugins. I have often wondered how often some of my plugins are used, and this could provide some insight. If metrics were supported, I assume that the information would be collected via an API on picard.metabrainz.org rather than sending to individual plugin APIs. How do you envision the information being presented or used? Would the information for a specific plugin be made available to the plugin author?"

**Recommendation if implemented:**
- Opt-in only (user consent required)
- Anonymous data collection
- Collected via picard.metabrainz.org API
- Basic metrics: install count, active users, version distribution
- Plugin authors can view their own plugin metrics
- Aggregate data for prioritizing support

**Status:** OPEN - Defer to Phase 3 or later

---

### Q23: Plugin rollback?

**Question:** How should users roll back to previous plugin versions?

**Decision:** Use git history

**Approach:**
```bash
# Roll back to specific commit
picard-plugins --switch-ref myplugin abc123

# Roll back to version tag
picard-plugins --switch-ref myplugin v1.0.0
```

**Community Feedback:**
> **rdswift:** "I agree with the recommendation to use the Git history. In addition to specifying a commit ID, we may want to also support specifying a version tag. This might make it easier for the average user to roll back to a previous version."

**Note:** Version tag support is already included in the `--ref` and `--switch-ref` design (see [ROADMAP.md](ROADMAP.md) Phase 1.6).

**Status:** CLOSED

---

### Q24: CLI commands with GUI running?

**Question:** How should CLI commands work when Picard GUI is running?

**Decision:** Two-mode approach

**Modes:**

1. **Standalone (Phase 1):** Commands modify config/files, require restart
2. **Remote (Phase 2):** Commands sent to running Picard via `-e` option

**Approach:**
```bash
# Phase 1: Standalone mode
picard-plugins --enable listenbrainz
# Modifies config, restart required

# Phase 2: Remote mode
picard -e "PLUGIN_ENABLE listenbrainz"
# Hot reload in running Picard
```

**Rationale:**
- Picard already has remote command infrastructure (`picard/remotecommands/`)
- Phase 1 keeps implementation simple
- Phase 2 adds hot-reload capability
- Clear separation of concerns

**Status:** CLOSED

---

## Questions for Future Consideration

### Plugin Marketplace

- Should there be a web-based plugin marketplace?
- How to handle plugin submissions?
- Review process for community plugins?

**Community Feedback:**
> **rdswift:** "My short answer to this is 'Yes', even though it may require significant curation effort depending on the extent of the plugins included. I believe that there is significant value in users being able to access a list of available plugins from a common site, especially if they can filter by category and/or plugin author, and search within the plugin descriptions.
>
> I'm not clear on the process for requesting a plugin to be included in the official registry maintained and served via the API. Is the process documented somewhere? I assume that it is based upon the submission of a plugin MANIFEST for consideration, and that all such requests need to be vetted and approved by an appropriate member of the Picard team.
>
> If the plugin browser is only displaying information for plugins in the registry, then the system can be automated to use the information provided via the registry item manifests (or a database built from the manifest information), and serve the pages based upon the results of API queries. In this case, the plugin browser could (and should) be served from the picard.musicbrainz.org domain.
>
> If the plugin browser is intended to also include plugins not included in the registry, then the complexity (and curation effort) increases significantly.
>
> A rudimentary list of plugins not included in the official plugin list is currently available on a Picard Resources page in the MusicBrainz Wiki. My recommendation is to continue using the Wiki for this purpose, curated by the users, which would allow rudimentary discovery of the 'unofficial' unregistered plugins. The full 'plugin browser' experience would be reserved for registered plugins."

**Recommendation based on feedback:**
- Web-based plugin browser for registered plugins only
- Served from picard.musicbrainz.org
- Automated from registry data
- Filter by category, trust level, author
- Search functionality
- Continue using Wiki for unregistered plugins

### Plugin Analytics

- Should plugins be able to report usage statistics?
- Privacy considerations?
- Opt-in vs opt-out?

**See Q22 above for detailed discussion.**

### Plugin Signing

- Code signing for official plugins?
- Certificate infrastructure?
- Verification process?

### Plugin Screenshots

**Community Feedback:**
> **rdswift:** "From what I see currently, most plugins provide some sort of metadata addition or manipulation and don't really have displays suitable for capturing in a screenshot. If the manifest contains a 'User Guide URL', perhaps the registry could contain a link to the user guide."

**Recommendation:** Add optional `homepage` or `documentation_url` field to MANIFEST.toml instead of screenshots.

### Plugin Changelogs

**Community Feedback:**
> **rdswift:** "Are we managing / displaying (or planning to manage / display) a changelog for each plugin? I'm as guilty as anyone for not properly maintaining a log of my changes, and I've gotten even worse since managing my work using Git. Accommodating plugin changelogs is a good idea, and if that happens it would be better to have a standardized format from which to work."

**Recommendation:**
- Optional CHANGELOG.md in plugin repository
- Standard format (Keep a Changelog)
- Displayed in plugin browser if present
- Not required, but encouraged

### Plugin Search Ranking

**Community Feedback:**
> **rdswift:** "That depends on what information is available. Perhaps something like: keywords matched, level of trust, user rating (if available), usage / installed metrics (if available)"

**Recommendation:** Ranking algorithm based on:
1. Keyword match relevance
2. Trust level (official > trusted > community)
3. Usage metrics (if available)
4. User ratings (if available)

### Plugin Recommendations

**Community Feedback:**
> **rdswift:** "Perhaps suggestions could be based on a combination of user rating and usage / installation metrics if they are available."

### Plugin Bundles

**Community Feedback:**
> **rdswift:** "Nice idea, but we would have to come up with some way to identify the bundles. Perhaps the bundles could be simple lists like a requirements.txt file, and could be curated by the users?"

**Recommendation:** Simple text file format for bundles, user-curated.

### Plugin Hot Reload

**Community Feedback:**
> **rdswift:** "Yes. I can see this being used in conjunction with option profiles."

**Note:** Hot reload is already supported via the enable/disable mechanism (see Q19). Plugins stay loaded but hooks are de-registered.

### Plugin Profiling

**Community Feedback:**
> **rdswift:** "Optimizing plugin performance ultimately helps optimize overall Picard performance, so I think this is a worthwhile idea. I'm just unsure how this would be implemented."

**Recommendation:**
- Add optional profiling mode
- Measure hook execution time
- Report slow plugins
- Help developers optimize
- Could be part of developer tools

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
