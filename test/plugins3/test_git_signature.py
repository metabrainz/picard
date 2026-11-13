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
import tempfile

from test.picardtestcase import PicardTestCase

from picard.git.factory import git_backend

import pytest


try:
    from picard.git.factory import has_git_backend

    HAS_GIT_BACKEND = has_git_backend()
except ImportError:
    HAS_GIT_BACKEND = False


FAKE_SSH_SIGNATURE = '-----BEGIN SSH SIGNATURE-----\nAAAAfakesignaturebytes\n-----END SSH SIGNATURE-----\n'


@pytest.mark.skipif(not HAS_GIT_BACKEND, reason="git backend not available")
class TestGetSignature(PicardTestCase):
    """Tests for GitRepository.get_signature() signature extraction."""

    def setUp(self):
        super().setUp()
        self._tmp = tempfile.mkdtemp()
        self.repo_path = Path(self._tmp)
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        import shutil

        shutil.rmtree(self._tmp, ignore_errors=True)

    def _raw_repo(self):
        # These tests craft commits with pygit2-specific calls that are not part
        # of the backend abstraction, so reach into the raw pygit2 repository.
        backend = git_backend()
        repo = backend.init_repository(self.repo_path)
        return repo, repo._repo

    def _write_unsigned_commit(self, pygit2_repo):
        import pygit2

        sig = pygit2.Signature('Tester', 'tester@example.com')
        tree = pygit2_repo.index.write_tree()
        return pygit2_repo.create_commit('refs/heads/main', sig, sig, 'unsigned', tree, [])

    def _write_signed_commit(self, pygit2_repo, signature=FAKE_SSH_SIGNATURE):
        unsigned_id = self._write_unsigned_commit(pygit2_repo)
        payload = pygit2_repo[unsigned_id].read_raw().decode()
        signed_id = pygit2_repo.create_commit_with_signature(payload, signature)
        pygit2_repo.set_head(signed_id)
        return signed_id

    def test_unsigned_commit_returns_none(self):
        repo, pygit2_repo = self._raw_repo()
        commit_id = self._write_unsigned_commit(pygit2_repo)
        self.assertIsNone(repo.get_signature(str(commit_id)))
        repo.free()

    def test_signed_commit_returns_signature_and_payload(self):
        repo, pygit2_repo = self._raw_repo()
        commit_id = self._write_signed_commit(pygit2_repo)
        result = repo.get_signature(str(commit_id))
        self.assertIsNotNone(result)
        signature, payload = result
        self.assertIsInstance(signature, bytes)
        self.assertIsInstance(payload, bytes)
        self.assertIn(b'BEGIN SSH SIGNATURE', signature)
        # The signed payload is the commit object content (tree, author, ...).
        self.assertTrue(payload.startswith(b'tree '))

    def test_signed_commit_resolvable_via_head(self):
        repo, pygit2_repo = self._raw_repo()
        self._write_signed_commit(pygit2_repo)
        result = repo.get_signature('HEAD')
        self.assertIsNotNone(result)
        self.assertIn(b'BEGIN SSH SIGNATURE', result[0])
        repo.free()

    def test_lightweight_tag_peels_to_signed_commit(self):
        repo, pygit2_repo = self._raw_repo()
        commit_id = self._write_signed_commit(pygit2_repo)
        backend = git_backend()
        backend.create_reference(repo, 'refs/tags/v1', str(commit_id))
        result = repo.get_signature('v1')
        self.assertIsNotNone(result)
        self.assertIn(b'BEGIN SSH SIGNATURE', result[0])
        repo.free()

    def test_annotated_tag_on_signed_commit_peels_to_commit_signature(self):
        import pygit2

        repo, pygit2_repo = self._raw_repo()
        commit_id = self._write_signed_commit(pygit2_repo)
        tagger = pygit2.Signature('Tester', 'tester@example.com')
        # An annotated (but itself unsigned) tag pointing at a signed commit:
        # the signature of the pointed-at commit is returned.
        tag_id = pygit2_repo.create_tag('v2', str(commit_id), pygit2.enums.ObjectType.COMMIT, tagger, 'release')
        result = repo.get_signature(str(tag_id))
        self.assertIsNotNone(result)
        self.assertIn(b'BEGIN SSH SIGNATURE', result[0])
        repo.free()

    def test_annotated_tag_on_unsigned_commit_returns_none(self):
        import pygit2

        repo, pygit2_repo = self._raw_repo()
        commit_id = self._write_unsigned_commit(pygit2_repo)
        tagger = pygit2.Signature('Tester', 'tester@example.com')
        tag_id = pygit2_repo.create_tag('v3', str(commit_id), pygit2.enums.ObjectType.COMMIT, tagger, 'release')
        self.assertIsNone(repo.get_signature(str(tag_id)))
        repo.free()

    def test_nonexistent_rev_returns_none(self):
        repo, _ = self._raw_repo()
        self._write_unsigned_commit(_)
        self.assertIsNone(repo.get_signature('does-not-exist'))
        repo.free()
