# Picard Plugin v3 Documentation

This directory contains comprehensive documentation for Picard's Plugin v3 system.

---

## Documents

### Core Documentation

- **[ROADMAP.md](ROADMAP.md)** - Development roadmap with phases, tasks, and timeline
- **[MANIFEST.md](MANIFEST.md)** - MANIFEST.toml specification and plugin development guide
- **[CLI.md](CLI.md)** - Complete CLI commands reference

### System Design

- **[REGISTRY.md](REGISTRY.md)** - Registry JSON schema, trust levels, and blacklist system
- **[WEBSITE.md](WEBSITE.md)** - Website implementation for registry generation
- **[TRANSLATIONS.md](TRANSLATIONS.md)** - Translation system for plugins and registry
- **[SECURITY.md](SECURITY.md)** - Security model and rationale

### Reference

- **[DECISIONS.md](DECISIONS.md)** - Design decisions and Q&A
- **[MIGRATION.md](MIGRATION.md)** - Migration guide from Plugin v2 to v3

---

## Quick Start

### For Plugin Developers

1. Read [MANIFEST.md](MANIFEST.md) to understand plugin structure
2. See [MIGRATION.md](MIGRATION.md) if migrating from v2
3. Check [TRANSLATIONS.md](TRANSLATIONS.md) for localization
4. Review [SECURITY.md](SECURITY.md) for best practices

### For Users

1. See [CLI.md](CLI.md) for command reference
2. Understand [REGISTRY.md](REGISTRY.md) trust levels
3. Check [SECURITY.md](SECURITY.md) for safety information

### For Contributors

1. Review [ROADMAP.md](ROADMAP.md) for development phases
2. Check [DECISIONS.md](DECISIONS.md) for design rationale
3. See [WEBSITE.md](WEBSITE.md) for registry implementation

---

## Key Features

### Git-Based Distribution
- Plugins distributed via git repositories
- Easy updates and version control
- Support for branches, tags, and commits

### Trust Levels
- **Official** (🛡️) - Picard team maintained
- **Trusted** (✓) - Known authors
- **Community** (⚠️) - Other authors
- **Unregistered** (🔓) - Not in registry

### Centralized Registry
- Official plugin list on website
- Blacklist for malicious plugins
- Easy plugin discovery
- Automatic updates

### Modern Stack
- TOML manifests
- JSON translations
- PyQt6 support
- Python 3.9+

---

## Development Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | 🚧 In Progress | Functional CLI-only system |
| Phase 2 | 📋 Planned | Polish & robustness |
| Phase 3 | 📋 Planned | Official plugin repository |
| Phase 4 | 📋 Planned | GUI integration |

See [ROADMAP.md](ROADMAP.md) for detailed timeline.

---

## Document Organization

### By Audience

**Plugin Developers:**
- [MANIFEST.md](MANIFEST.md) - How to create plugins
- [TRANSLATIONS.md](TRANSLATIONS.md) - How to add translations
- [MIGRATION.md](MIGRATION.md) - How to migrate from v2
- [SECURITY.md](SECURITY.md) - Security best practices

**End Users:**
- [CLI.md](CLI.md) - How to manage plugins
- [REGISTRY.md](REGISTRY.md) - Understanding trust levels
- [SECURITY.md](SECURITY.md) - Staying safe

**Picard Contributors:**
- [ROADMAP.md](ROADMAP.md) - What to implement
- [DECISIONS.md](DECISIONS.md) - Why decisions were made
- [WEBSITE.md](WEBSITE.md) - How to implement registry

### By Topic

**Getting Started:**
1. [ROADMAP.md](ROADMAP.md) - Overview
2. [MANIFEST.md](MANIFEST.md) - Plugin basics
3. [CLI.md](CLI.md) - Using plugins

**Advanced Topics:**
1. [REGISTRY.md](REGISTRY.md) - Registry system
2. [TRANSLATIONS.md](TRANSLATIONS.md) - Localization
3. [SECURITY.md](SECURITY.md) - Security model

**Reference:**
1. [DECISIONS.md](DECISIONS.md) - Design rationale
2. [MIGRATION.md](MIGRATION.md) - v2 to v3 changes
3. [WEBSITE.md](WEBSITE.md) - Server implementation

---

## Contributing

To contribute to Plugin v3:

1. Read [ROADMAP.md](ROADMAP.md) to understand current status
2. Check [DECISIONS.md](DECISIONS.md) for design decisions
3. Pick a task from Phase 1 or 2
4. Submit PR to `phw/plugins-v3` branch

---

## Links

- **Picard Website:** https://picard.musicbrainz.org/
- **Documentation:** https://picard-docs.musicbrainz.org/
- **GitHub:** https://github.com/metabrainz/picard
- **Forum:** https://community.metabrainz.org/c/picard
- **IRC:** #musicbrainz-picard on Libera.Chat

---

## Document History

- **2025-11-24:** Initial split from monolithic PLUGINS_ROADMAP.md
- Documents organized by topic for easier navigation
- Cross-references added between related documents
