# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer, Laurent Monin
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from picard.git.backend import (
    GitBackend,
    GitObject,
    GitObjectType,
    GitRef,
    GitRefType,
    GitRepository,
    GitStatusFlag,
)
from picard.git.factory import git_backend


class MockGitRepository(GitRepository):
    """Mock implementation for testing"""

    def __init__(self):
        self.status_result = {}
        self.head_target = "abc123"
        self.head_detached = False
        self.head_shorthand = "main"
        self.head_name = "refs/heads/main"
        self.references = {}

    def get_status(self):
        return self.status_result

    def get_head_target(self):
        return self.head_target

    def is_head_detached(self):
        return self.head_detached

    def get_head_shorthand(self):
        return self.head_shorthand

    def get_head_name(self):
        return self.head_name

    def revparse_single(self, ref):
        return GitObject("abc123", GitObjectType.COMMIT)

    def peel_to_commit(self, obj):
        return obj

    def reset(self, commit_id, mode):
        pass

    def checkout_tree(self, obj):
        pass

    def set_head(self, target):
        pass

    def list_references(self):
        return [
            GitRef("refs/heads/main", "abc123", GitRefType.BRANCH, is_remote=False),
            GitRef("refs/tags/v1.0", "def456", GitRefType.TAG, is_remote=False),
        ]

    def get_remotes(self):
        return {}

    def get_remote(self, name):
        return Mock()

    def create_remote(self, name, url):
        return Mock()

    def get_branches(self):
        return Mock()

    def get_commit_date(self, commit_id):
        return 1234567890  # Mock timestamp

    def fetch_remote(self, remote, refspec=None, callbacks=None):
        pass

    def fetch_remote_with_tags(self, remote, refspec=None, callbacks=None):
        pass

    def free(self):
        pass


class MockGitBackend(GitBackend):
    """Mock backend for testing"""

    def __init__(self):
        self.repo = MockGitRepository()

    def create_repository(self, path):
        return self.repo

    def init_repository(self, path, bare=False):
        return self.repo

    def clone_repository(self, url, path, **options):
        return self.repo

    def fetch_remote_refs(self, url, **options):
        # Return different refs to test repo_path usage
        repo_path = options.get('repo_path')
        if repo_path:
            return [
                GitRef("refs/heads/main", "abc123", GitRefType.BRANCH, is_remote=True),
                GitRef("refs/tags/v1.0", "def456", GitRefType.TAG, is_remote=True, is_annotated=True),
            ]
        return [
            GitRef("refs/heads/main", "abc123", GitRefType.BRANCH, is_remote=True),
            GitRef("refs/tags/v1.0", "def456", GitRefType.TAG, is_remote=True, is_annotated=False),
        ]

    def create_remote_callbacks(self):
        return Mock()

    def get_remote(self, name):
        return Mock()

    def create_commit(self, repo, message, author_name="Test", author_email="test@example.com"):
        return "abc123"

    def create_tag(self, repo, tag_name, commit_id, message="", author_name="Test", author_email="test@example.com"):
        pass

    def create_branch(self, repo, branch_name, commit_id):
        pass

    def add_and_commit_files(self, repo, message, author_name="Test", author_email="test@example.com"):
        return "abc123"

    def reset_hard(self, repo, commit_id):
        pass

    def create_reference(self, repo, ref_name, commit_id):
        pass

    def set_head_detached(self, repo, commit_id):
        pass


class TestGitBackend(unittest.TestCase):
    def test_git_status_flags(self):
        """Test git status flag enumeration"""
        self.assertEqual(GitStatusFlag.CURRENT.value, 0)
        self.assertEqual(GitStatusFlag.IGNORED.value, 1)
        self.assertEqual(GitStatusFlag.MODIFIED.value, 2)

    def test_git_object_types(self):
        """Test git object type enumeration"""
        self.assertEqual(GitObjectType.COMMIT.value, "commit")
        self.assertEqual(GitObjectType.TAG.value, "tag")

    def test_git_ref_creation(self):
        """Test GitRef object creation"""
        ref = GitRef("main", "abc123")
        self.assertEqual(ref.name, "main")
        self.assertEqual(ref.target, "abc123")

    def test_fetch_remote_refs_real_repo(self):
        """Test fetch_remote_refs with a local repository to ensure refs have proper targets"""
        import tempfile

        from picard.git.factory import has_git_backend

        if not has_git_backend():
            self.skipTest("git backend not available")

        backend = git_backend()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a local git repository with tags
            repo_path = Path(tmpdir) / "test-repo"
            from test.test_plugins3_helpers import backend_create_tag, create_git_repo_with_backend

            # Create repo with initial commit
            commit_id = create_git_repo_with_backend(
                repo_path, {'README.md': '# Test Repository', 'file.txt': 'test content'}
            )

            # Create some version tags
            backend_create_tag(repo_path, 'v1.0.0', commit_id, 'Version 1.0.0')
            backend_create_tag(repo_path, 'v1.0.1', commit_id, 'Version 1.0.1')

            # Test fetch_remote_refs on the local repository
            # Use pathlib to create proper file URL for cross-platform compatibility
            repo_url = repo_path.as_uri()
            refs = backend.fetch_remote_refs(repo_url)

            # Should get some refs
            self.assertIsNotNone(refs)
            self.assertGreater(len(refs), 0)

            # Find tag refs to test
            tag_refs = [ref for ref in refs if ref.name.startswith('refs/tags/v')]
            self.assertGreater(len(tag_refs), 0, "Repository should have version tags")

            # Check that tag refs have proper targets (commit IDs)
            for ref in tag_refs:
                self.assertIsNotNone(ref.target, f"Tag {ref.name} should have a target commit ID")
                self.assertNotEqual(ref.target, "", f"Tag {ref.name} target should not be empty")
                # Commit IDs should be 40-character hex strings
                self.assertEqual(len(ref.target), 40, f"Tag {ref.name} target should be 40-char commit ID")
                self.assertTrue(
                    all(c in '0123456789abcdef' for c in ref.target.lower()),
                    f"Tag {ref.name} target should be valid hex",
                )

    def test_git_object_creation(self):
        """Test GitObject creation"""
        obj = GitObject("abc123", GitObjectType.COMMIT)
        self.assertEqual(obj.id, "abc123")
        self.assertEqual(obj.type, GitObjectType.COMMIT)

    def test_revparse_to_commit(self):
        """Test revparse_to_commit method"""
        backend = MockGitBackend()
        repo = backend.create_repository(Path("/test"))

        # Test that revparse_to_commit returns a commit object
        commit = repo.revparse_to_commit("HEAD")
        self.assertIsInstance(commit, GitObject)
        self.assertEqual(commit.type, GitObjectType.COMMIT)

    def test_mock_backend_operations(self):
        """Test mock backend basic operations"""
        backend = MockGitBackend()

        # Test repository creation
        repo = backend.create_repository(Path("/test"))
        self.assertIsInstance(repo, MockGitRepository)

        # Test status
        status = repo.get_status()
        self.assertEqual(status, {})

        # Test head operations
        self.assertEqual(repo.get_head_target(), "abc123")
        self.assertFalse(repo.is_head_detached())
        self.assertEqual(repo.get_head_shorthand(), "main")

    def test_git_backend_exceptions(self):
        """Test that git backend raises proper exceptions"""
        from picard.plugin3 import GitReferenceError, GitRepositoryError

        backend = git_backend()

        # Test repository error
        with self.assertRaises(GitRepositoryError):
            backend.create_repository(Path('/nonexistent/path'))

        # Test reference error with a valid repo
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / "test-repo"
            repo = backend.init_repository(repo_dir)

            with self.assertRaises(GitReferenceError):
                repo.revparse_single('nonexistent-ref')

            repo.free()

    @patch('picard.git.factory.get_git_backend')
    def test_git_factory_singleton(self, mock_get_backend):
        """Test git factory returns singleton"""
        mock_backend = MockGitBackend()
        mock_get_backend.return_value = mock_backend

        # Reset singleton
        import picard.git.factory

        picard.git.factory._git_backend = None

        backend1 = git_backend()
        backend2 = git_backend()

        self.assertIs(backend1, backend2)
        mock_get_backend.assert_called_once()

    def test_fetch_remote_refs_with_repo_path(self):
        """Test fetch_remote_refs uses existing repository when repo_path provided"""
        backend = MockGitBackend()

        # Test with repo_path
        refs = backend.fetch_remote_refs("https://example.com/repo.git", repo_path="/path/to/repo")
        self.assertEqual(len(refs), 2)

        # Test without repo_path (fallback)
        refs = backend.fetch_remote_refs("https://example.com/repo.git")
        self.assertEqual(len(refs), 2)

    def test_fetch_remote_refs_invalid_repo_path(self):
        """Test fetch_remote_refs falls back when repo_path is invalid"""
        backend = MockGitBackend()

        # Test with non-existent repo_path
        refs = backend.fetch_remote_refs("https://example.com/repo.git", repo_path="/nonexistent/path")
        self.assertEqual(len(refs), 2)  # Should fallback to temporary repo

    def test_git_ref_shortname(self):
        """Test GitRef shortname extraction"""
        # Branch
        ref = GitRef("refs/heads/main", "abc123", GitRefType.BRANCH)
        self.assertEqual(ref.shortname, "main")

        # Tag
        ref = GitRef("refs/tags/v1.0", "def456", GitRefType.TAG)
        self.assertEqual(ref.shortname, "v1.0")

        # Remote branch
        ref = GitRef("refs/remotes/origin/main", "xyz789", GitRefType.BRANCH, is_remote=True)
        self.assertEqual(ref.shortname, "origin/main")

        # HEAD
        ref = GitRef("HEAD", "abc123", GitRefType.HEAD)
        self.assertEqual(ref.shortname, "HEAD")

    def test_git_ref_repr(self):
        """Test GitRef string representation"""
        # Simple ref
        ref = GitRef("refs/heads/main", "abc123", GitRefType.BRANCH)
        self.assertIn("name='refs/heads/main'", repr(ref))
        self.assertIn("target='abc123'", repr(ref))
        self.assertIn("type=branch", repr(ref))

        # Annotated remote tag
        ref = GitRef("refs/tags/v1.0", "def456", GitRefType.TAG, is_remote=True, is_annotated=True)
        self.assertIn("name='refs/tags/v1.0'", repr(ref))
        self.assertIn("remote=True", repr(ref))
        self.assertIn("annotated=True", repr(ref))


if __name__ == '__main__':
    unittest.main()
