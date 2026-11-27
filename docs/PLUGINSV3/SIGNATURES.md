# Plugin Signature Verification

This document specifies optional cryptographic signature verification for
Plugin v3. It fleshes out the "Code Signing" layer referenced in
[SECURITY.md](SECURITY.md).

---

## Overview

Signature verification lets the registry vouch that a plugin's code was
published by a specific signer, and verifies that claim before the plugin's
code is executed.

- Signatures are **optional**. When a plugin has no signatures and no registry
  keys, no verification runs and installation is unaffected.
- The **registry is the trust anchor**. Trusted signing keys are published per
  plugin in the registry (served over HTTPS, already cached by Picard), not
  taken from the user's local keyring.
- Verification proves **provenance, not safety**. A signed plugin still runs
  with full privileges. It raises the bar against supply-chain tampering (e.g.
  a compromised repository hosting account), the realistic threat for a
  git-based plugin system. It is **not** a sandbox; see [SECURITY.md](SECURITY.md).
- No new runtime dependencies are bundled: signatures are extracted with the
  already-required `pygit2`, and verification is delegated to tools present on
  the host (e.g. `ssh-keygen`, `gpg`).

---

## Threat Model

**In scope:** An attacker who can push commits to a plugin's git repository
(stolen hosting credentials, maintainer-account takeover, MITM on an
unauthenticated transport) and thereby ship malicious code to users who already
trust that plugin. If the registry lists a signing key the attacker cannot sign
with, the tampered commit fails verification and (when required) installation is
refused.

**Out of scope:**

- A malicious but *correctly signed* plugin — handled by trust levels, code
  review, and the blacklist.
- Sandboxing / runtime containment of plugin code — see [SECURITY.md](SECURITY.md).
- Compromise of the registry itself — it is the root of trust, served over HTTPS.

---

## Architecture

Verification is a two-step pipeline: **extract**, then **verify**.

### Extraction

`pygit2` exposes `Commit.gpg_signature`, returning a
`(signature, signed_payload)` tuple for a signed commit or annotated tag, or
`(None, None)` when unsigned. This is the single, backend-agnostic extraction
point regardless of signature type. A new primitive is added to the git backend
abstraction (`picard/git/backend.py`, implemented in
`picard/git/backends/pygit2.py`):

```python
def get_signature(self, rev: str) -> tuple[bytes, bytes] | None:
    """Return (armored_signature, signed_payload) for the commit or annotated
    tag at `rev`, or None if it carries no signature."""
```

### Verification

The signature's armor header identifies its type, and a dispatch layer routes
to the matching backend:

| Armor header                      | Type    | Verifier (delegated)      |
|-----------------------------------|---------|---------------------------|
| `-----BEGIN SSH SIGNATURE-----`   | SSH     | `ssh-keygen -Y verify`    |
| `-----BEGIN PGP SIGNATURE-----`   | OpenPGP | system `gpg` (if present) |
| `-----BEGIN SIGNED MESSAGE-----`  | X.509   | future                    |

```python
# picard/plugin3/signature.py (sketch)
def verify(signature: bytes, payload: bytes, allowed_keys: list[str]) -> VerifyResult:
    kind = detect_armor(signature)  # 'ssh' | 'openpgp' | 'x509' | None
    backend = BACKENDS.get(kind)
    if backend is None or not backend.available():
        return VerifyResult.UNVERIFIABLE  # tooling missing / unknown type
    return backend.verify(signature, payload, allowed_keys)
```

Each backend is probed at runtime (`available()`), following the existing
`HAS_PYGIT2` soft-import pattern. Adding a signature type is a new backend
module; it does not change the registry schema or the install policy.

Registry verification checks the signature against the **registry-provided
key(s)** only. It must never fall back to keys from the user's local keyring —
that would let an attacker's own key satisfy the check.

---

## Registry Schema

Two optional fields are added to each plugin entry in the registry
(`plugins.toml`), set via the registry CLI:

```toml
[[plugins]]
id = "example-plugin"
uuid = "..."
git_url = "https://example.org/user/example-plugin.git"
trust_level = "trusted"
signing_keys = [
  "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... maintainer@example",
  # "openpgp:4AC0A7FE37970823F5F4ABDDD859F01B646C07A7",
]
require_signature = true
```

- `signing_keys` — list of trusted keys. Presence enables verification. Entries
  are type-tagged (SSH keys are self-describing; OpenPGP entries use an
  `openpgp:` prefix with a fingerprint).
- `require_signature` — optional boolean, default `false`. Escalates a
  verification failure from a warning to a hard refusal.

The two fields are orthogonal: `signing_keys` decides *whether verification
runs*; `require_signature` decides *whether failure is fatal*.

Format validation for these fields is authored in Picard's
`picard/plugin3/validator.py` and synced one-way into the registry tooling
(`registry_lib/picard/`); it must not be edited directly in the registry repo.

---

## Verification Policy (registry plugins)

For a plugin installed/updated from the registry, after the target commit/tag is
resolved but **before** it is checked out and loaded:

| `signing_keys` | `require_signature` | Repository signature state            | Outcome                   |
|----------------|---------------------|---------------------------------------|---------------------------|
| absent         | —                   | not checked                           | **Install** (silent)      |
| present        | false (default)     | valid signature by a listed key       | **Install** (verified)    |
| present        | false               | no signature                          | **Warn**, allow           |
| present        | false               | signed, but key does not match        | **Warn**, allow           |
| present        | false               | signed, but verifier tool unavailable | **Warn**, allow           |
| present        | **true**            | valid signature by a listed key       | **Install** (verified)    |
| present        | **true**            | no signature                          | **Refuse** (no override)  |
| present        | **true**            | signed, but key does not match        | **Refuse** (no override)  |
| present        | **true**            | signed, but verifier tool unavailable | **Refuse**, overridable   |

### "Cannot verify" vs "verified bad"

- **Verified bad** — the signature is missing, or present but signed by a key
  other than the trusted one. Detecting this needs no crypto (a presence check
  and a key-id comparison), so it works even with no verifier installed. Under
  `require_signature` this is a **hard refusal with no override**.
- **Cannot verify** — the signature claims the right key but the verifier tool
  is not available to confirm it cryptographically. Under `require_signature`
  this is refused **by default**, with an explicit, logged, user-initiated
  override. The override is never offered for "verified bad".

### Updates preserve the installed version

When an update fails verification under `require_signature`, Picard refuses the
update and keeps the currently installed version untouched. Verification runs on
the freshly synced copy in a temporary directory, before it is moved into place
or loaded, so the installed plugin is left as-is on failure.

### Registry unavailable

If the registry cannot be loaded, there are no `signing_keys` to read, so
verification does not run and installation proceeds — consistent with the
existing `get_trust_level()` and `is_blacklisted()`, which also fail open. An
attacker who can block the registry fetch therefore downgrades to
no-verification; this is mitigated (not eliminated) by the registry cache
retaining the last-known-good keys and by HTTPS transport.

---

## Unregistered / URL / Local Plugins

Plugins installed from a URL or local path have no registry-provided key to
anchor against, so signature verification does not apply to them and their
behaviour is unchanged.

Signature verification is deliberately a **registry-only** feature. Meaningful
verification needs an authority that enumerates the set of keys trusted to sign
a plugin — that authority is the registry. Without it there is no way to tell a
legitimate new signer from an attacker's key:

- A plugin repository may legitimately be signed by **several** keys (multiple
  maintainers, a CI/bot release key, key rotation). The registry models this
  directly: `signing_keys` is a list, and a commit signed by *any* listed key
  verifies.
- A trust-on-first-use scheme (pin the first key seen, warn on change) cannot
  make that distinction. On a multi-maintainer repo it would cry wolf every
  time a different-but-legitimate maintainer signs a release; and once a user
  accepts a "new key", an attacker's key would be trusted just the same. The
  warning would carry no reliable signal.

So an author who wants verified, multi-key trust should get the plugin listed
in the registry, where the trusted key set is explicit and curated.

---

## Rollout

Because signatures are optional and per plugin, enforcement is adopted
incrementally. A plugin can only be subject to `require_signature` once it
publishes a stable signing key, so strict enforcement is enabled per plugin
rather than globally:

1. **Publish keys** — a maintainer adds `signing_keys` for a plugin.
   Verification then runs in warn mode without blocking installs.
2. **Prefer self-contained verifiers** — SSH signatures
   (`ssh-keygen -Y verify`) are verifiable without extra tooling on typical
   hosts, so the "cannot verify" case rarely arises. OpenPGP (delegated to a
   system `gpg`) is supported as an optional backend.
3. **Enable `require_signature`** for a plugin once its signing key is stable
   and it is signed consistently.

This lets individual plugins move from unsigned → signed (warn) → required at
their own pace without affecting other plugins or changing the behavior for
plugins that remain unsigned.

---

## Implementation Checklist

Ordered so the schema is agreed before either side enforces it:

1. **Shared validator** — add `signing_keys` / `require_signature` format
   validation to `picard/plugin3/validator.py`; sync to the registry repo.
2. **Registry CLI** — accept and serialize the new fields; tests.
3. **Backend primitive** — `get_signature()` on the git backend ABC +
   `pygit2` implementation; tests with a signed fixture.
4. **Verifier** — `picard/plugin3/signature.py` with armor detection, the
   dispatch layer, and the SSH backend. OpenPGP as a soft-probed backend.
5. **Enforcement** — verify the resolved commit during installation (in the
   plugin installer, on the freshly synced copy before it is moved into place
   or loaded), gated by the per-plugin policy table; surface results and the
   scoped override in the CLI and the install dialog. Policy is driven entirely
   by the registry fields (`signing_keys`, `require_signature`); no global
   setting is introduced.

---

## See Also

- **[SECURITY.md](SECURITY.md)** — overall security model and trust levels
- **[REGISTRY.md](REGISTRY.md)** — registry schema, trust levels, blacklist
- **[MANIFEST.md](MANIFEST.md)** — plugin development
- **[DECISIONS.md](DECISIONS.md)** — design rationale
