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


from unittest.mock import (
    Mock,
    patch,
)

from test.picardtestcase import (
    PicardTestCase,
    subtest_cases,
)

from picard.coverart import CoverArt


class CoverArtPostCoverArtHookTest(PicardTestCase):
    """Tests for the album post cover art hook emitted by CoverArt."""

    def setUp(self):
        super().setUp()
        self.album = Mock()
        self.album.id = 'album-id'
        self.album._load_token = object()
        self.album.tagger.albums = {'album-id': self.album}
        # Run callbacks immediately, as for an already loaded album
        self.album.run_when_loaded.side_effect = lambda func, *args, **kwargs: func()
        self.coverart = CoverArt(self.album, Mock(), {})
        patcher = patch('picard.coverart.run_album_post_cover_art_processors')
        self.run_hook = patcher.start()
        self.addCleanup(patcher.stop)

    def test_finished_runs_hook(self):
        self.coverart._finished()
        self.run_hook.assert_called_once_with(self.album)

    def test_finished_waits_for_album_loaded(self):
        self.album.run_when_loaded.side_effect = None
        self.coverart._finished()
        self.run_hook.assert_not_called()
        self.album.run_when_loaded.assert_called_once()
        # Simulate the album finishing loading
        callback = self.album.run_when_loaded.call_args[0][0]
        callback()
        self.run_hook.assert_called_once_with(self.album)

    def test_finished_skipped_if_album_removed(self):
        self.album.tagger.albums.clear()
        self.coverart._finished()
        self.run_hook.assert_not_called()

    def test_finished_skipped_if_album_removed_while_loading(self):
        self.album.run_when_loaded.side_effect = None
        self.coverart._finished()
        self.album.tagger.albums.clear()
        self.album.run_when_loaded.call_args[0][0]()
        self.run_hook.assert_not_called()

    def test_finished_skipped_if_album_reloaded_while_loading(self):
        self.album.run_when_loaded.side_effect = None
        self.coverart._finished()
        self.album._load_token = object()
        self.album.run_when_loaded.call_args[0][0]()
        self.run_hook.assert_not_called()

    def test_hook_runs_when_queue_ends(self):
        self.coverart.image_processing = Mock()
        self.coverart._queue_generator = iter(())
        self.coverart.next_in_queue()
        self.coverart.image_processing.wait_for_processing.assert_called_once()
        self.run_hook.assert_called_once_with(self.album)

    def test_hook_not_run_while_queue_is_active(self):
        def waiting_generator():
            yield

        self.coverart._queue_generator = waiting_generator()
        self.coverart.next_in_queue()
        self.run_hook.assert_not_called()

    def test_hook_not_run_if_album_removed_during_queue(self):
        self.coverart.image_processing = Mock()
        self.coverart._queue_generator = iter(())
        self.album.tagger.albums.clear()
        self.coverart.next_in_queue()
        self.run_hook.assert_not_called()

    def test_hook_not_run_if_album_reloaded_during_queue(self):
        self.coverart.image_processing = Mock()
        self.coverart._queue_generator = iter(())
        # A reload started after this CoverArt was created
        self.album._load_token = object()
        self.coverart.next_in_queue()
        self.run_hook.assert_not_called()

    def test_hook_runs_for_cover_art_of_current_load(self):
        self.album._load_token = object()
        new_coverart = CoverArt(self.album, Mock(), {})
        new_coverart.image_processing = Mock()
        new_coverart._queue_generator = iter(())
        new_coverart.next_in_queue()
        self.run_hook.assert_called_once_with(self.album)

    def _requeue_with(self, provider_enabled=True, filter_result=True, instance_enabled=True):
        provider_class = Mock()
        provider_class.return_value.enabled.return_value = instance_enabled
        provider = Mock(enabled=provider_enabled, provider_class=provider_class)
        self.coverart.providers = iter([provider])
        with patch('picard.coverart.run_provider_filters', return_value=filter_result) as run_filters:
            self.coverart._requeue()
        return provider, provider_class, run_filters

    def test_requeue_uses_provider_accepted_by_filters(self):
        provider, provider_class, run_filters = self._requeue_with()
        run_filters.assert_called_once_with(self.album, provider_class)
        provider_class.return_value.queue_images.assert_called_once()

    def test_requeue_skips_provider_rejected_by_filters(self):
        _provider, provider_class, run_filters = self._requeue_with(filter_result=False)
        run_filters.assert_called_once_with(self.album, provider_class)
        provider_class.return_value.queue_images.assert_not_called()

    def test_requeue_does_not_run_filters_for_disabled_provider(self):
        _provider, provider_class, run_filters = self._requeue_with(provider_enabled=False)
        run_filters.assert_not_called()
        provider_class.return_value.queue_images.assert_not_called()

    def test_requeue_does_not_use_provider_disabled_for_the_album(self):
        _provider, provider_class, run_filters = self._requeue_with(instance_enabled=False)
        provider_class.return_value.queue_images.assert_not_called()
        run_filters.assert_not_called()

    def test_hook_runs_when_all_providers_are_skipped(self):
        self.coverart.image_processing = Mock()
        self.coverart._queue_generator = self.coverart._start_queue()
        providers = [Mock(enabled=True, provider_class=Mock()) for _ in range(3)]
        self.coverart.providers = iter(providers)
        with (
            patch('picard.coverart.run_provider_filters', return_value=False),
            patch('picard.coverart.get_config') as get_config,
        ):
            get_config.return_value.setting = {'save_images_to_tags': True, 'save_images_to_files': False}
            self.coverart.next_in_queue()
        for provider in providers:
            provider.provider_class.return_value.queue_images.assert_not_called()
        self.run_hook.assert_called_once_with(self.album)

    def test_hook_runs_when_cover_art_disabled(self):
        config = Mock()
        config.setting = {'save_images_to_tags': False, 'save_images_to_files': False}
        with patch('picard.coverart.get_config', return_value=config):
            self.coverart.retrieve()
        self.run_hook.assert_called_once_with(self.album)


class CoverArtAllImagesSatisfiedTest(PicardTestCase):
    """Tests for CoverArt._all_images_satisfied optimization."""

    def setUp(self):
        super().setUp()
        album = Mock()
        album.tagger = Mock()
        metadata = Mock()
        release = {}
        self.coverart = CoverArt(album, metadata, release)

    def _make_config(self, save_to_tags=True, embed_only_front=True, save_to_files=True, save_only_front_file=False):
        config = Mock()
        config.setting = {
            'save_images_to_tags': save_to_tags,
            'embed_only_one_front_image': embed_only_front,
            'save_images_to_files': save_to_files,
            'save_only_one_front_image': save_only_front_file,
        }
        return config

    def test_not_satisfied_when_no_front_found(self):
        """Never satisfied if no front image has been found yet."""
        self.coverart.front_image_found = False
        config = self._make_config()
        self.assertFalse(self.coverart._all_images_satisfied(config))

    @subtest_cases(
        "config_overrides,expected",
        {
            'tags want only the front, no external files': ({'save_to_files': False}, True),
            'tags want all images': ({'embed_only_front': False, 'save_to_files': False}, False),
            'files want all images': ({}, False),
            'both want only the front': ({'save_only_front_file': True}, True),
            'files want only the front, tags disabled': (
                {'save_to_tags': False, 'embed_only_front': False, 'save_only_front_file': True},
                True,
            ),
            'both destinations disabled': (
                {'save_to_tags': False, 'embed_only_front': False, 'save_to_files': False},
                True,
            ),
        },
    )
    def test_all_images_satisfied(self, config_overrides, expected):
        """A front image has been found; check each combination of destinations.

        Each case lists only the settings that differ from `_make_config()`'s
        defaults (save_to_tags=True, embed_only_front=True, save_to_files=True,
        save_only_front_file=False).
        """
        self.coverart.front_image_found = True
        config = self._make_config(**config_overrides)
        # assertTrue/assertFalse rather than assertEqual, to keep the original
        # truthiness checks rather than requiring exactly True/False
        check = self.assertTrue if expected else self.assertFalse
        check(self.coverart._all_images_satisfied(config))
