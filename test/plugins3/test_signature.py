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


from pathlib import Path
import subprocess
import tempfile

from test.picardtestcase import PicardTestCase

from picard.plugin3.signature import (
    VerifyResult,
    detect_armor,
    verify,
)
from picard.util import find_executable

import pytest


HAS_SSH_KEYGEN = find_executable('ssh-keygen') is not None


def _ssh_keygen(*args, input_bytes=None):
    subprocess.run(
        ['ssh-keygen', *args],
        check=True,
        capture_output=True,
        input=input_bytes,
    )


class TestDetectArmor(PicardTestCase):
    def test_ssh(self):
        self.assertEqual(detect_armor(b'-----BEGIN SSH SIGNATURE-----\nAAAA\n'), 'ssh')

    def test_openpgp(self):
        self.assertEqual(detect_armor(b'-----BEGIN PGP SIGNATURE-----\n'), 'openpgp')

    def test_x509(self):
        self.assertEqual(detect_armor(b'-----BEGIN SIGNED MESSAGE-----\n'), 'x509')

    def test_leading_whitespace_tolerated(self):
        self.assertEqual(detect_armor(b'\n  -----BEGIN SSH SIGNATURE-----\n'), 'ssh')

    def test_unknown(self):
        self.assertIsNone(detect_armor(b'not a signature'))

    def test_empty(self):
        self.assertIsNone(detect_armor(b''))


class TestVerifyDispatch(PicardTestCase):
    def test_unsigned_when_no_signature(self):
        self.assertEqual(verify(None, b'payload', ['ssh-ed25519 AAAA']), VerifyResult.UNSIGNED)

    def test_unsigned_when_no_payload(self):
        self.assertEqual(verify(b'-----BEGIN SSH SIGNATURE-----\n', None, []), VerifyResult.UNSIGNED)

    def test_unknown_type_unverifiable(self):
        self.assertEqual(verify(b'garbage signature', b'payload', []), VerifyResult.UNVERIFIABLE)

    def test_openpgp_unverifiable_for_now(self):
        # OpenPGP backend is not implemented yet: reports unverifiable.
        self.assertEqual(verify(b'-----BEGIN PGP SIGNATURE-----\nx\n', b'payload', []), VerifyResult.UNVERIFIABLE)


@pytest.mark.skipif(not HAS_SSH_KEYGEN, reason="ssh-keygen not available")
class TestSshVerification(PicardTestCase):
    def setUp(self):
        super().setUp()
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(self._cleanup)
        self.d = Path(self._tmp)
        self.payload = b'commit object bytes to be signed'
        # Generate a signing key and sign the payload (namespace 'git').
        self.key = self.d / 'key'
        _ssh_keygen('-q', '-t', 'ed25519', '-f', str(self.key), '-N', '', '-C', 'author@example')
        self.pub = (self.d / 'key.pub').read_text().strip()
        data_file = self.d / 'data'
        data_file.write_bytes(self.payload)
        _ssh_keygen('-Y', 'sign', '-f', str(self.key), '-n', 'git', str(data_file))
        self.signature = (self.d / 'data.sig').read_bytes()

    def _cleanup(self):
        import shutil

        shutil.rmtree(self._tmp, ignore_errors=True)

    def _other_pubkey(self):
        other = self.d / 'other'
        _ssh_keygen('-q', '-t', 'ed25519', '-f', str(other), '-N', '', '-C', 'other@example')
        return (self.d / 'other.pub').read_text().strip()

    def test_verified_with_trusted_key(self):
        result = verify(self.signature, self.payload, [self.pub])
        self.assertEqual(result, VerifyResult.VERIFIED)

    def test_verified_among_multiple_keys(self):
        result = verify(self.signature, self.payload, [self._other_pubkey(), self.pub])
        self.assertEqual(result, VerifyResult.VERIFIED)

    def test_no_match_when_key_not_trusted(self):
        result = verify(self.signature, self.payload, [self._other_pubkey()])
        self.assertEqual(result, VerifyResult.NO_MATCH)

    def test_no_match_when_payload_tampered(self):
        result = verify(self.signature, self.payload + b'tampered', [self.pub])
        self.assertEqual(result, VerifyResult.NO_MATCH)

    def test_no_match_when_no_ssh_keys_provided(self):
        # Only an OpenPGP entry provided for an SSH signature.
        result = verify(self.signature, self.payload, ['openpgp:' + 'a' * 40])
        self.assertEqual(result, VerifyResult.NO_MATCH)
