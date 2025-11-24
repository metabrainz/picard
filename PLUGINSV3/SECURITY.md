# Plugin Security Model

This document explains the security model for Plugin v3 and the rationale behind design decisions.

---

## Executive Summary

**Approach:** Trust-based system with defense in depth

**Key Points:**
- Python sandboxing is impractical and provides false security
- Plugins are trusted code with full system access
- Security through trust levels, code review, and blacklist
- Focus on preventing malicious plugins from being installed
- Similar to VSCode, Sublime Text, and other successful plugin systems

---

## Security Model

### Trust Levels

Plugin v3 uses a four-tier trust system:

1. **Official** (🛡️) - Picard team maintained, full code review
2. **Trusted** (✓) - Known authors, reputation-based trust
3. **Community** (⚠️) - Other authors, clear warnings
4. **Unregistered** (🔓) - Not in registry, strongest warnings

See [REGISTRY.md](REGISTRY.md) for detailed trust level descriptions.

### Defense in Depth

**Layer 1: Trust Levels**
- Official plugins: Full code review by Picard team
- Trusted plugins: Reputation-based trust
- Community plugins: Clear warnings to users
- Unregistered plugins: Strongest warnings

**Layer 2: Blacklist**
- Centralized blacklist on website
- Updated independently of Picard releases
- Supports repository-level patterns (block entire organizations)
- Checked on install and startup

**Layer 3: User Education**
- Clear warnings for non-official plugins
- Documentation of risks
- Explanation of plugin capabilities

**Layer 4: Rapid Response**
- Fast blacklist updates
- Community reporting
- Incident response process

**Layer 5: Code Signing (Future)**
- Sign official plugins
- Verify signature on load
- Proves authenticity (not security)

---

## Why Not Sandboxing?

### Python Sandboxing Reality

**Fundamental Problem:** Python was not designed to be sandboxed

**Failed Attempts:**
- `pysandbox` - Abandoned, author declared it impossible
- `RestrictedPython` - Only works for very limited use cases
- `PyPy sandboxing` - Abandoned, too many escape vectors

**Quote from pysandbox author:**
> "After having worked during 3 years on a pysandbox project to sandbox Python, I now reached a point where I am convinced that pysandbox is broken by design."

### Why Python Can't Be Sandboxed

1. **Introspection** - Python's powerful introspection allows bypassing restrictions
2. **C extensions** - Native code can't be sandboxed
3. **Import system** - Too many ways to import modules
4. **Bytecode manipulation** - Can modify code at runtime
5. **Object model** - Everything is an object, everything is mutable

### Example Sandbox Escapes

```python
# Escape via introspection
().__class__.__bases__[0].__subclasses__()[104].__init__.__globals__['sys'].modules['os'].system('ls')

# Escape via import
__import__('os').system('ls')

# Escape via file objects
open('/etc/passwd').read()

# Escape via subprocess
__import__('subprocess').call(['ls'])
```

**Conclusion:** Any Python sandbox can be escaped by determined attacker.

---

## Alternative Approaches Considered

### Option A: No Sandboxing (CHOSEN)

**Approach:** Trust-based system with social/organizational controls

**Pros:**
- ✅ Simple to implement
- ✅ No performance overhead
- ✅ Plugins have full capabilities
- ✅ Matches how most plugin systems work
- ✅ Proven approach (VSCode, Sublime, etc.)

**Cons:**
- ❌ Malicious plugin can do anything
- ❌ Relies on user judgment

**Mitigation:**
- Trust levels with clear warnings
- Blacklist for known malicious plugins
- Code review for official plugins
- User education

### Option B: Process Isolation

**Approach:** Run plugins in separate processes

**Pros:**
- ✅ True isolation
- ✅ Can limit capabilities via IPC

**Cons:**
- ❌ Very complex to implement
- ❌ Significant performance overhead
- ❌ Limited plugin capabilities
- ❌ Difficult IPC design
- ❌ Not suitable for UI plugins

**Verdict:** Too complex for the benefit

### Option C: Static Analysis

**Approach:** Scan plugin code for suspicious patterns

**Pros:**
- ✅ Catches obvious malicious code
- ✅ Educational for developers
- ✅ No runtime overhead

**Cons:**
- ❌ Can't catch obfuscated code
- ❌ False positives
- ❌ Only works for reviewed plugins
- ❌ Doesn't prevent runtime attacks

**Verdict:** Good complement to trust levels, not a complete solution

### Option D: Capability-Based Security

**Approach:** Plugins declare required capabilities, user approves

**Example MANIFEST.toml:**
```toml
[capabilities]
network = true           # Needs network access
filesystem_read = true   # Can read files
filesystem_write = false # Cannot write files
config_read = true       # Can read config
config_write = true      # Can write config
```

**Pros:**
- ✅ Transparency for users
- ✅ Documents plugin needs
- ✅ Can warn about excessive permissions

**Cons:**
- ❌ Can't enforce in Python (plugins can bypass)
- ❌ Users might not understand permissions
- ❌ Adds friction to installation
- ❌ Doesn't prevent malicious code if capability granted

**Verdict:** Good for transparency, not for enforcement. Could be added later.

---

## Recommended Approach: Defense in Depth

Combine multiple strategies:

### 1. Trust Levels (Primary Defense)
- Official: Full code review
- Trusted: Reputation-based trust
- Community: Clear warnings
- Unregistered: Strongest warnings

### 2. Blacklist (Rapid Response)
- Centralized on website
- Fast updates
- Repository-level patterns
- Checked on install and startup

### 3. User Education (Critical)
- Clear documentation of risks
- Warnings during installation
- Explanation of plugin capabilities
- Best practices guide

### 4. Code Review (For Official Plugins)
- Manual review by Picard team
- Security checklist
- Automated static analysis
- Regular audits

### 5. Community Reporting
- Easy reporting mechanism
- Fast response to reports
- Transparent incident handling

### 6. Code Signing (Future)
- Sign official plugins
- Verify signature on load
- Proves authenticity
- Doesn't prevent malicious code, but proves it's from Picard team

---

## Comparison with Other Systems

| System | Approach | Sandboxing |
|--------|----------|------------|
| **VSCode** | Trust-based, marketplace review | None |
| **Sublime Text** | Trust-based, package control | None |
| **Atom** | Trust-based, npm packages | None |
| **Firefox** | Code review + sandboxing (WebExtensions) | Strong (separate process) |
| **Chrome** | Code review + sandboxing (extensions) | Strong (separate process) |
| **Electron** | Node.js context isolation | Medium (can be bypassed) |
| **Python pip** | Trust-based, PyPI review | None |

**Observation:** Most successful plugin systems for desktop apps use trust-based models, not sandboxing.

---

## Security Best Practices for Plugin Developers

1. **Minimize dependencies** - Fewer dependencies = smaller attack surface
2. **Validate input** - Never trust user input or external data
3. **Use HTTPS** - Always use secure connections
4. **Handle errors** - Don't expose sensitive information in errors
5. **Avoid eval()** - Never execute arbitrary code
6. **Sanitize paths** - Prevent directory traversal
7. **Limit permissions** - Only request what you need
8. **Document capabilities** - Be transparent about what plugin does

---

## Security Best Practices for Users

1. **Only install trusted plugins** - Prefer official and trusted plugins
2. **Read warnings** - Pay attention to trust level warnings
3. **Check source code** - Review code before installing community plugins
4. **Keep plugins updated** - Updates may include security fixes
5. **Report suspicious plugins** - Help protect the community
6. **Use official sources** - Install from official registry when possible

---

## Incident Response

### If Malicious Plugin Discovered

1. **Immediate:** Add to blacklist
2. **Notify:** Alert users via website/mailing list
3. **Investigate:** Determine scope of impact
4. **Document:** Write incident report
5. **Improve:** Update security measures

### Blacklist Process

1. Report received (email, forum, GitHub issue)
2. Picard team investigates
3. If confirmed malicious:
   - Add to blacklist immediately
   - Notify users
   - Document reason
4. If false alarm:
   - Document investigation
   - Notify reporter

---

## Future Enhancements

### Phase 1 (Current)
- ✅ Trust levels
- ✅ Blacklist
- ✅ Clear warnings

### Phase 2 (Near Future)
- ⏳ Code signing for official plugins
- ⏳ Automated static analysis
- ⏳ Capability declarations (transparency only)

### Phase 3 (Long Term)
- ⏳ Community reputation system
- ⏳ Plugin ratings and reviews
- ⏳ Automated security scanning

---

## Accepting the Risk

**Key Principle:** Plugins are trusted code.

We accept that:
- Malicious plugins can do anything
- Users must make informed decisions
- Perfect security is impossible
- Trust-based approach is pragmatic

We focus on:
- Preventing malicious plugins from being installed
- Making trust levels clear
- Rapid response when issues discovered
- User education

This is the same approach used by successful plugin ecosystems like VSCode, Sublime Text, and npm.

---

## See Also

- **[REGISTRY.md](REGISTRY.md)** - Trust levels and blacklist
- **[DECISIONS.md](DECISIONS.md)** - Design decisions
- **[MANIFEST.md](MANIFEST.md)** - Plugin development guide
