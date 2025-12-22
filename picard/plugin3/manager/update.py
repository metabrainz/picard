# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2024-2025 Philipp Wolfer
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

from typing import NamedTuple

from picard import log
from picard.git.backend import GitRefType
from picard.git.factory import git_backend
from picard.git.ops import GitOperations
from picard.plugin3 import GitReferenceError
from picard.plugin3.plugin import PluginSourceGit, PluginState, short_commit_id
from picard.plugin3.plugin_metadata import PluginMetadata
from picard.plugin3.ref_item import RefItem


class UpdateResult(NamedTuple):
    """Result of a plugin update operation."""

    old_version: str
    new_version: str
    old_commit: str
    new_commit: str
    old_ref_item: RefItem
    new_ref_item: RefItem
    commit_date: int


class UpdateCheck(NamedTuple):
    """Result of checking for plugin updates."""

    plugin_id: str
    old_commit: str
    new_commit: str
    commit_date: int
    old_ref: str
    new_ref: str


class UpdateAllResult(NamedTuple):
    """Result of updating a plugin in update_all operation."""

    plugin_id: str
    success: bool
    result: UpdateResult
    error: str


class PluginUpdater:
    """Handles plugin update operations."""

    def __init__(self, manager):
        self.manager = manager

    def _with_plugin_state_management(self, plugin, operation):
        """Execute operation with plugin enable/disable state management."""
        was_enabled = plugin.state == PluginState.ENABLED
        if was_enabled:
            self.manager.disable_plugin(plugin)

        try:
            result = operation()
            # Re-enable plugin if it was enabled before
            if was_enabled:
                self.manager.enable_plugin(plugin)
            self.manager.plugin_ref_switched.emit(plugin)
            return result
        except Exception:
            # Re-enable plugin on failure if it was enabled before
            if was_enabled:
                self.manager.enable_plugin(plugin)
            raise

    def _check_dirty_working_dir(self, plugin, discard_changes):
        """Check for uncommitted changes if not discarding."""
        if not discard_changes:
            assert plugin.local_path is not None
            changes = GitOperations.check_dirty_working_dir(plugin.local_path)
            if changes:
                from picard.plugin3.manager import PluginDirtyError

                raise PluginDirtyError(plugin.plugin_id, changes)

    def _check_commit_pinned(self, plugin, metadata):
        """Check if plugin is pinned to a specific commit."""
        old_ref = metadata.ref if metadata else None

        if old_ref:
            ref_type, _ = GitOperations.check_ref_type(plugin.local_path, old_ref)
            if ref_type == 'commit':
                from picard.plugin3.manager import PluginCommitPinnedError

                raise PluginCommitPinnedError(plugin.plugin_id, old_ref)
        else:
            # No stored ref, check current HEAD state
            ref_type, ref_name = GitOperations.check_ref_type(plugin.local_path)
            if ref_type == 'commit':
                from picard.plugin3.manager import PluginCommitPinnedError

                raise PluginCommitPinnedError(plugin.plugin_id, ref_name)

        return ref_type if old_ref else 'commit'

    def update_plugin(self, plugin, discard_changes=False):
        """Update a single plugin to latest version."""
        self.manager._ensure_plugin_url(plugin, 'update')
        uuid, metadata = self.manager._get_plugin_uuid_and_metadata(plugin)

        # Check for uncommitted changes and commit pinning
        self._check_dirty_working_dir(plugin, discard_changes)
        ref_type = self._check_commit_pinned(plugin, metadata)

        def perform_update():
            old_version = str(plugin.manifest.version) if plugin.manifest and plugin.manifest.version else None
            old_url = metadata.url
            old_uuid = metadata.uuid
            old_ref = metadata.ref

            # Check registry for redirects
            current_url, current_uuid, redirected = self.manager._metadata.check_redirects(old_url, old_uuid)

            # Check if plugin has versioning_scheme and current ref is a version tag
            new_ref = old_ref
            if ref_type == 'tag' and plugin.has_versioning(self.manager._registry, True):
                versioning_scheme = plugin.get_versioning_scheme(self.manager._registry)
                newer_tag = self.manager._find_newer_version_tag(current_url, old_ref, versioning_scheme)
                if newer_tag:
                    new_ref = newer_tag
                    log.info('Found newer version: %s -> %s', old_ref, new_ref)

            source = PluginSourceGit(current_url, new_ref)
            # Set resolved_ref_type if we updated to a newer tag
            if new_ref != old_ref and ref_type == 'tag':
                source.resolved_ref_type = 'tag'

            assert plugin.local_path is not None
            old_commit, new_commit = source.update(plugin.local_path, single_branch=True)

            # Get commit date and resolve annotated tags to actual commit
            def get_commit_info(repo):
                commit = repo.revparse_to_commit(new_commit)
                actual_commit_id = commit.id
                commit_date = repo.get_commit_date(commit.id)
                return actual_commit_id, commit_date

            new_commit, commit_date = self.manager._with_plugin_repo(plugin.local_path, get_commit_info)

            # Reload manifest to get new version
            self.manager._validate_manifest_or_rollback(plugin, old_commit, True)  # was_enabled handled by wrapper

            new_version = str(plugin.manifest.version) if plugin.manifest and plugin.manifest.version else None
            new_ref = source.ref

            # Update metadata
            original_url, original_uuid = self.manager._metadata.get_original_metadata(
                metadata, redirected, old_url, old_uuid
            )
            self.manager._metadata.save_plugin_metadata(
                PluginMetadata(
                    name=plugin.plugin_id,
                    url=current_url,
                    ref=new_ref or '',
                    commit=new_commit,
                    uuid=current_uuid,
                    original_url=original_url,
                    original_uuid=original_uuid,
                )
            )

            return UpdateResult(
                old_version or '',
                new_version or '',
                old_commit,
                new_commit,
                self._create_ref_item_from_metadata(old_ref, old_commit, ref_type),
                self._create_ref_item_from_source(source, new_commit),
                commit_date,
            )

        return self._with_plugin_state_management(plugin, perform_update)

    def _create_ref_item_from_metadata(self, ref_name, commit, ref_type):
        """Create RefItem from metadata information."""
        if not ref_name and not commit:
            return RefItem('')

        if ref_type == 'tag':
            item_ref_type = RefItem.Type.TAG
            shortname = ref_name if ref_name else commit
        elif ref_type == 'branch':
            item_ref_type = RefItem.Type.BRANCH
            shortname = ref_name if ref_name else commit
        else:  # commit
            item_ref_type = RefItem.Type.COMMIT
            shortname = commit or ref_name

        return RefItem(shortname=shortname, ref_type=item_ref_type, commit=commit)

    def _create_ref_item_from_source(self, source, commit):
        """Create RefItem from PluginSourceGit with accurate ref type information."""
        ref_name = source.ref
        ref_type_str = getattr(source, 'resolved_ref_type', None)

        if not ref_name and not commit:
            return RefItem('')

        if ref_type_str == 'tag':
            item_ref_type = RefItem.Type.TAG
            shortname = ref_name if ref_name else commit
        elif ref_type_str == 'branch':
            item_ref_type = RefItem.Type.BRANCH
            shortname = ref_name if ref_name else commit
        else:  # commit or None
            item_ref_type = RefItem.Type.COMMIT
            shortname = commit or ref_name

        return RefItem(shortname=shortname, ref_type=item_ref_type, commit=commit)

    def update_all_plugins(self):
        """Update all installed plugins."""
        results = []
        for plugin in self.manager._plugins:
            try:
                result = self.update_plugin(plugin)
                results.append(UpdateAllResult(plugin_id=plugin.plugin_id, success=True, result=result, error=None))
            except Exception as e:
                from picard.plugin3.manager import PluginCommitPinnedError

                if isinstance(e, PluginCommitPinnedError):
                    # Commit-pinned plugins are skipped, not failed
                    results.append(UpdateAllResult(plugin_id=plugin.plugin_id, success=True, result=None, error=str(e)))
                else:
                    results.append(
                        UpdateAllResult(plugin_id=plugin.plugin_id, success=False, result=None, error=str(e))
                    )
        return results

    def switch_ref(self, plugin, ref, discard_changes=False):
        """Switch plugin to a different git ref."""
        self.manager._ensure_plugin_url(plugin, 'switch ref')

        # Convert GitRef to string for GitOperations (which still expects strings)
        from picard.git.backend import GitRef

        ref_str = ref.shortname if isinstance(ref, GitRef) else ref

        def perform_switch():
            old_git_ref, new_git_ref, old_commit, new_commit = GitOperations.switch_ref(
                plugin, ref_str, discard_changes
            )

            # Validate manifest after ref switch
            self.manager._validate_manifest_or_rollback(plugin, old_commit, True)  # was_enabled handled by wrapper

            # Update metadata with new ref
            uuid, metadata = self.manager._get_plugin_uuid_and_metadata(plugin)
            if metadata:
                metadata.ref = new_git_ref.shortname
                metadata.commit = new_commit
                metadata.ref_type = new_git_ref.ref_type.value if new_git_ref.ref_type else 'commit'
                self.manager._metadata.save_plugin_metadata(metadata)

            return old_git_ref, new_git_ref, old_commit, new_commit

        return self._with_plugin_state_management(plugin, perform_switch)

    def check_updates(self, skip_fetch=False):
        """Check which plugins have updates available without installing."""
        updates = {}
        for plugin in self.manager._plugins:
            metadata = self.manager._metadata.get_plugin_metadata(plugin.uuid) if plugin.uuid else None
            if not self.manager._should_fetch_plugin_refs(plugin, metadata):
                continue

            update_check = self._check_single_plugin_update(plugin, metadata, skip_fetch)
            if update_check:
                updates[plugin.plugin_id] = update_check

        return updates

    def _check_single_plugin_update(self, plugin, metadata, skip_fetch):
        """Check update status for a single plugin."""
        try:

            def analyze_update(repo):
                current_commit = repo.get_head_target()

                # Fetch without updating (suppress progress output) - unless skipped
                if not skip_fetch:
                    backend = git_backend()
                    callbacks = backend.create_remote_callbacks()
                    for remote in repo.get_remotes():
                        # Fetch all refs including tags in a single operation
                        repo.fetch_remote_with_tags(remote, None, callbacks._callbacks)

                # Get current ref from repository instead of metadata
                old_ref, is_detached = self.manager._get_current_ref_for_updates(repo, metadata)
                ref = old_ref

                # Check if currently on a tag (check current commit, not ref)
                current_is_tag = False
                current_tag = None

                # Use stored ref_type to determine if plugin was installed from a tag
                # For existing plugins without ref_type, fall back to checking if ref matches a tag
                is_tag_installation = False
                resolved_ref_info = ""

                if metadata.ref_type == 'tag':
                    is_tag_installation = True
                    resolved_ref_info = f"tag {metadata.ref}"
                elif metadata.ref_type == 'branch':
                    resolved_ref_info = f"branch {metadata.ref}"
                elif metadata.ref_type is None and metadata.ref:
                    # Fallback for existing plugins: check what the ref actually resolves to
                    log.debug(
                        "Plugin %s: resolving ref %s to determine installation type", plugin.plugin_id, metadata.ref
                    )

                    # Check if ref matches a tag name
                    for r in repo.list_references():
                        if r.ref_type == GitRefType.TAG and (r.shortname == metadata.ref or r.name == metadata.ref):
                            is_tag_installation = True
                            resolved_ref_info = f"tag {metadata.ref}"
                            break

                    if not is_tag_installation:
                        # Check if current commit matches any tag
                        for r in repo.list_references():
                            if r.ref_type == GitRefType.TAG:
                                try:
                                    tag_commit = repo.revparse_to_commit(r.name)
                                    if tag_commit.id == current_commit:
                                        is_tag_installation = True
                                        resolved_ref_info = f"commit {metadata.ref} (resolves to tag {r.shortname})"
                                        break
                                except Exception:
                                    continue

                    if not is_tag_installation:
                        resolved_ref_info = f"commit/branch {metadata.ref}"

                # Check if plugin supports versioning before doing tag-based updates
                if is_tag_installation and not plugin.has_versioning(self.manager._registry, is_tag_installation):
                    log.debug(
                        "Plugin %s: originally installed from %s, but no versioning support - skipping tag-based updates",
                        plugin.plugin_id,
                        resolved_ref_info,
                    )
                    is_tag_installation = False

                # Check if plugin is pinned to a commit (direct hash or relative reference)
                is_commit_pin = self.manager._is_commit_pin(metadata)
                if is_commit_pin:
                    log.debug(
                        "Plugin %s: pinned to commit %s - skipping updates",
                        plugin.plugin_id,
                        metadata.ref,
                    )
                    return None

                if is_tag_installation:
                    log.debug(
                        "Plugin %s: originally installed from %s, checking if current commit matches any tag",
                        plugin.plugin_id,
                        resolved_ref_info,
                    )
                    for r in repo.list_references():
                        if r.ref_type == GitRefType.TAG:
                            try:
                                tag_commit = repo.revparse_to_commit(r.name)

                                if tag_commit.id == current_commit:
                                    current_is_tag = True
                                    current_tag = r.shortname
                                    log.debug(
                                        "Plugin %s: found matching tag %s for current commit",
                                        plugin.plugin_id,
                                        current_tag,
                                    )
                                    break
                            except Exception as e:
                                log.debug("Failed to check tag %s for commit match: %s", r.name, e)
                                continue
                else:
                    log.debug(
                        "Plugin %s: originally installed from %s, skipping tag-based updates",
                        plugin.plugin_id,
                        resolved_ref_info,
                    )

                # If on a tag, check for newer version tag
                new_ref = None
                if current_is_tag and current_tag:
                    log.debug("Plugin %s is on tag %s, checking for newer tags", plugin.plugin_id, current_tag)
                    source = PluginSourceGit(metadata.url, ref)
                    latest_tag = source._find_latest_tag(repo, current_tag)
                    if latest_tag and latest_tag != current_tag:
                        # Found newer tag - log in concise format
                        log.debug("Plugin %s: update available %s → %s", plugin.plugin_id, current_tag, latest_tag)
                        ref = latest_tag
                        new_ref = latest_tag
                    else:
                        # Already on latest tag, no update needed
                        log.debug("Plugin %s: no newer tag found, skipping", plugin.plugin_id)
                        return None

                # Resolve ref using GitRef lookup first, then fallback
                # For update checking, prefer remote branches over local ones
                try:
                    from picard.git.ref_utils import find_git_ref

                    # For branches, try origin/ version first to get latest from remote
                    git_ref = find_git_ref(repo, f'origin/{ref}')
                    if not git_ref:
                        # Fall back to local ref (for tags or local-only branches)
                        git_ref = find_git_ref(repo, ref)

                    if git_ref:
                        obj = repo.revparse_single(git_ref.name)
                    elif not ref.startswith('origin/') and not ref.startswith('refs/'):
                        # Fallback: try refs/tags/ first, then origin/ for branches
                        try:
                            obj = repo.revparse_single(f'refs/tags/{ref}')
                        except GitReferenceError:
                            # Not a tag, try origin/ prefix for branches
                            try:
                                obj = repo.revparse_single(f'origin/{ref}')
                            except GitReferenceError:
                                # Fall back to original ref (might be commit hash)
                                obj = repo.revparse_single(ref)
                    elif ref.startswith('origin/'):
                        # Handle origin/ refs - these are branches, not tags
                        obj = repo.revparse_single(ref)
                    else:
                        obj = repo.revparse_single(ref)

                    # Peel annotated tags to get the actual commit
                    commit = repo.peel_to_commit(obj)

                    latest_commit = commit.id
                    # Get commit date using backend
                    latest_commit_date = repo.get_commit_date(commit.id)
                except GitReferenceError:
                    # Ref not found, skip this plugin
                    return None

                if current_commit != latest_commit:
                    # For display: use tag names if available, otherwise commit hashes for detached HEAD
                    if current_is_tag and current_tag:
                        display_old_ref = current_tag
                    elif is_detached:
                        display_old_ref = short_commit_id(current_commit)
                    else:
                        display_old_ref = old_ref

                    display_new_ref = new_ref if new_ref else (short_commit_id(latest_commit) if is_detached else None)

                    return UpdateCheck(
                        plugin_id=plugin.plugin_id,
                        old_commit=current_commit,
                        new_commit=latest_commit,
                        commit_date=latest_commit_date,
                        old_ref=display_old_ref,
                        new_ref=display_new_ref,
                    )

                return None

            return self.manager._with_plugin_repo(plugin.local_path, analyze_update)
        except KeyError:
            # Ref not found, skip this plugin (expected for some cases)
            return None
        except Exception as e:
            # Log unexpected errors but continue with other plugins
            log.warning("Failed to check updates for plugin %s: %s", plugin.plugin_id, e, exc_info=True)
            return None
