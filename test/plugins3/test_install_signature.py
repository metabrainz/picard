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
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.plugin3.manager.errors import PluginSignatureError
from picard.plugin3.manager.install import PluginInstaller
from picard.plugin3.signature import VerifyResult


def _registry_plugin(signing_keys=None, require_signature=False):
    rp = Mock()
    rp.signing_keys = signing_keys or []
    rp.require_signature = require_signature
    return rp


class TestInstallerSignatureEnforcement(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.manager = Mock()
        self.registry = Mock()
        self.manager._registry = self.registry
        self.installer = PluginInstaller(self.manager)
        self.temp_path = Path('/tmp/does-not-matter')

    def _run(self, verify_result=None, extracted=(b'sig', b'payload'), allow_unverified=False):
        """Call _verify_signature with get_signature/verify patched."""
        fake_repo = MagicMock()
        fake_repo.get_signature.return_value = extracted
        fake_backend = MagicMock()
        fake_backend.create_repository.return_value.__enter__.return_value = fake_repo

        with (
            patch('picard.plugin3.manager.install.git_backend', return_value=fake_backend),
            patch('picard.plugin3.manager.install.verify_signature', return_value=verify_result) as mock_verify,
        ):
            self.installer._verify_signature(
                self.temp_path, 'deadbeef', 'https://example/p.git', 'uuid-1', allow_unverified=allow_unverified
            )
        return mock_verify

    def test_no_registry_entry_is_noop(self):
        self.registry.find_plugin.return_value = None
        # Should not raise and should not attempt verification.
        self._run(verify_result=VerifyResult.NO_MATCH)

    def test_no_signing_keys_is_noop(self):
        self.registry.find_plugin.return_value = _registry_plugin(signing_keys=[])
        self._run(verify_result=VerifyResult.NO_MATCH)

    def test_verified_passes(self):
        self.registry.find_plugin.return_value = _registry_plugin(
            signing_keys=['ssh-ed25519 AAAA'], require_signature=True
        )
        self._run(verify_result=VerifyResult.VERIFIED)  # no raise

    def test_not_required_warns_but_allows_on_no_match(self):
        self.registry.find_plugin.return_value = _registry_plugin(
            signing_keys=['ssh-ed25519 AAAA'], require_signature=False
        )
        self._run(verify_result=VerifyResult.NO_MATCH)  # no raise

    def test_not_required_warns_but_allows_on_unsigned(self):
        self.registry.find_plugin.return_value = _registry_plugin(
            signing_keys=['ssh-ed25519 AAAA'], require_signature=False
        )
        self._run(verify_result=VerifyResult.UNSIGNED, extracted=None)  # no raise

    def test_required_refuses_on_no_match(self):
        self.registry.find_plugin.return_value = _registry_plugin(
            signing_keys=['ssh-ed25519 AAAA'], require_signature=True
        )
        with self.assertRaises(PluginSignatureError) as ctx:
            self._run(verify_result=VerifyResult.NO_MATCH)
        self.assertEqual(ctx.exception.reason, 'no_match')

    def test_required_refuses_on_unsigned(self):
        self.registry.find_plugin.return_value = _registry_plugin(
            signing_keys=['ssh-ed25519 AAAA'], require_signature=True
        )
        with self.assertRaises(PluginSignatureError) as ctx:
            self._run(verify_result=VerifyResult.UNSIGNED, extracted=None)
        self.assertEqual(ctx.exception.reason, 'unsigned')

    def test_required_refuses_on_unverifiable_without_override(self):
        self.registry.find_plugin.return_value = _registry_plugin(
            signing_keys=['ssh-ed25519 AAAA'], require_signature=True
        )
        with self.assertRaises(PluginSignatureError) as ctx:
            self._run(verify_result=VerifyResult.UNVERIFIABLE)
        self.assertEqual(ctx.exception.reason, 'unverifiable')

    def test_required_allows_unverifiable_with_override(self):
        self.registry.find_plugin.return_value = _registry_plugin(
            signing_keys=['ssh-ed25519 AAAA'], require_signature=True
        )
        # allow_unverified only bypasses the 'unverifiable' case: no raise.
        self._run(verify_result=VerifyResult.UNVERIFIABLE, allow_unverified=True)

    def test_override_does_not_bypass_no_match(self):
        self.registry.find_plugin.return_value = _registry_plugin(
            signing_keys=['ssh-ed25519 AAAA'], require_signature=True
        )
        # Even with the override, a wrong/missing signature is never allowed.
        with self.assertRaises(PluginSignatureError):
            self._run(verify_result=VerifyResult.NO_MATCH, allow_unverified=True)

    def test_lookup_falls_back_to_url(self):
        # find_plugin(uuid=...) returns None, find_plugin(url=...) returns entry.
        entry = _registry_plugin(signing_keys=['ssh-ed25519 AAAA'], require_signature=True)
        self.registry.find_plugin.side_effect = lambda uuid=None, url=None: entry if url else None
        with self.assertRaises(PluginSignatureError):
            self._run(verify_result=VerifyResult.NO_MATCH)
