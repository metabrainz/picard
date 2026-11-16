# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.


"""Verify plugin commit/tag signatures against registry-provided keys.

Signatures are extracted from git by the backend (see
:meth:`picard.git.backend.GitRepository.get_signature`); this module performs
the actual cryptographic verification.

Verification is delegated to tools already present on the host (e.g.
``ssh-keygen``). No crypto library is bundled. A signature type whose verifier
is unavailable yields :attr:`VerifyResult.UNVERIFIABLE` rather than failing
hard, so the install policy can decide what to do (warn, or refuse only when a
signature is required).

The trust anchor is always the caller-supplied ``allowed_keys`` (the keys the
registry vouches for). Verification must never consult the user's ambient
keyring.

Adding support for another signature type (e.g. OpenPGP via the system ``gpg``)
means adding a :class:`SignatureBackend` to ``_BACKENDS``; nothing else here or
in the install policy needs to change.
"""

from abc import (
    ABC,
    abstractmethod,
)
from enum import Enum
from pathlib import Path
import tempfile

from picard import log
from picard.plugin3.validator import OPENPGP_KEY_PREFIX
from picard.util import (
    find_executable,
    run_executable,
)


# git uses this namespace for SSH signatures (git config gpg.ssh.namespace).
_SSH_NAMESPACE = 'git'

# We trust the key itself, not an email identity: the allowed_signers file maps
# a wildcard principal to each trusted key, and we pass a matching -I so any
# listed key verifies regardless of the signer identity recorded in the key.
_SSH_ALLOWED_PRINCIPAL = '*'
_SSH_VERIFY_PRINCIPAL = 'picard-plugin'

_VERIFY_TIMEOUT_SECONDS = 15

# Signature type -> armor header that identifies it.
_ARMOR_HEADERS = {
    'ssh': b'-----BEGIN SSH SIGNATURE-----',
    'openpgp': b'-----BEGIN PGP SIGNATURE-----',
    'x509': b'-----BEGIN SIGNED MESSAGE-----',
}


class VerifyResult(Enum):
    """Outcome of a signature verification attempt."""

    VERIFIED = 'verified'  # Signed by one of the trusted keys.
    NO_MATCH = 'no_match'  # Signed, but not by a trusted key, or bad signature.
    UNSIGNED = 'unsigned'  # No signature present.
    UNVERIFIABLE = 'unverifiable'  # Cannot verify (verifier/type unavailable).


def detect_armor(signature: bytes) -> str | None:
    """Return the signature type ('ssh', 'openpgp', 'x509') from its armor
    header, or None if unrecognised."""
    if not signature:
        return None
    head = signature.lstrip()
    for kind, header in _ARMOR_HEADERS.items():
        if head.startswith(header):
            return kind
    return None


class SignatureBackend(ABC):
    """A verifier for one signature type."""

    @abstractmethod
    def available(self) -> bool:
        """Whether the verifier tool is present on the host."""

    @abstractmethod
    def verify(self, signature: bytes, payload: bytes, allowed_keys: list[str]) -> VerifyResult:
        """Verify ``payload`` against ``signature`` using ``allowed_keys``."""


class SshSignatureBackend(SignatureBackend):
    """Verify SSH signatures using ``ssh-keygen -Y verify``."""

    def _tool(self) -> str | None:
        return find_executable('ssh-keygen')

    def available(self) -> bool:
        return self._tool() is not None

    def verify(self, signature: bytes, payload: bytes, allowed_keys: list[str]) -> VerifyResult:
        ssh_keygen = self._tool()
        if not ssh_keygen:
            return VerifyResult.UNVERIFIABLE

        # Only SSH-form keys can verify an SSH signature (drop OpenPGP entries).
        ssh_keys = [
            k.strip() for k in allowed_keys if k.strip() and not k.strip().lower().startswith(OPENPGP_KEY_PREFIX)
        ]
        if not ssh_keys:
            return VerifyResult.NO_MATCH

        with tempfile.TemporaryDirectory(prefix='picard-sigverify-') as tmpdir:
            signers_path = Path(tmpdir) / 'allowed_signers'
            sig_path = Path(tmpdir) / 'signature.sig'
            signers_path.write_text(''.join(f'{_SSH_ALLOWED_PRINCIPAL} {key}\n' for key in ssh_keys), encoding='utf-8')
            sig_path.write_bytes(signature)

            try:
                rc, _out, err = run_executable(
                    ssh_keygen,
                    '-Y',
                    'verify',
                    '-f',
                    str(signers_path),
                    '-I',
                    _SSH_VERIFY_PRINCIPAL,
                    '-n',
                    _SSH_NAMESPACE,
                    '-s',
                    str(sig_path),
                    timeout=_VERIFY_TIMEOUT_SECONDS,
                    input=payload,
                )
            except Exception as e:
                log.warning("SSH signature verification could not run: %s", e)
                return VerifyResult.UNVERIFIABLE

        if rc == 0:
            return VerifyResult.VERIFIED
        # ssh-keygen returns non-zero both for "not a trusted key" and for a
        # bad/corrupt signature; both mean the signature is not trusted.
        log.debug("SSH signature not verified (rc=%s): %s", rc, err.strip())
        return VerifyResult.NO_MATCH


# Verifier per signature type. Types recognised by detect_armor() but absent
# here (e.g. 'openpgp', 'x509') have no verifier yet and resolve to
# UNVERIFIABLE, which the install policy treats as a warning unless a signature
# is required.
_BACKENDS: dict[str, SignatureBackend] = {
    'ssh': SshSignatureBackend(),
}


def verify(signature: bytes | None, payload: bytes | None, allowed_keys: list[str]) -> VerifyResult:
    """Verify a signature against the registry-provided trusted keys.

    Args:
        signature: Armored signature block, or None if the object is unsigned.
        payload: Exact bytes that were signed.
        allowed_keys: Trusted signing keys from the registry.

    Returns:
        VerifyResult describing the outcome.
    """
    if not signature or not payload:
        return VerifyResult.UNSIGNED

    backend = _BACKENDS.get(detect_armor(signature) or '')
    if backend is None or not backend.available():
        return VerifyResult.UNVERIFIABLE

    try:
        return backend.verify(signature, payload, allowed_keys)
    except Exception as e:
        log.warning("Signature verification raised an error: %s", e)
        return VerifyResult.UNVERIFIABLE
