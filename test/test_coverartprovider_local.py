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

import os
import re
from unittest.mock import (
    MagicMock,
    patch,
)

from test.picardtestcase import PicardTestCase

from picard.config import get_config

# Importing the providers package registers the built-in local cover art modes.
import picard.coverart.providers  # noqa: F401
from picard.coverart.providers.local import (
    REGEX_MODE_ID,
    CoverArtProviderLocal,
    _queue_images_regex,
    _regex_playground_matcher,
)
from picard.extension_points.local_cover_art_modes import (
    LocalCoverArtMode,
    ext_point_local_cover_art_modes,
    get_local_cover_art_mode,
    local_cover_art_modes,
    register_local_cover_art_mode,
)


class LocalCoverArtTestBase(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.provider = CoverArtProviderLocal.__new__(CoverArtProviderLocal)
        self.provider._default_types = ['front']
        self.provider._types_split_re = CoverArtProviderLocal._types_split_re
        self.provider._known_types = CoverArtProviderLocal._known_types
        self.tmpdir = self.mktmpdir()

    def _create_files(self, filenames):
        for name in filenames:
            path = os.path.join(self.tmpdir, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'w').close()

    def _filenames(self, results):
        return sorted(os.path.basename(r.url.toLocalFile()) for r in results)


class FindLocalImagesRegexTest(LocalCoverArtTestBase):
    def _find(self, regex):
        match_re = re.compile(regex, re.IGNORECASE)
        return list(self.provider.find_local_images(self.tmpdir, match_re))

    def test_simple_match(self):
        self._create_files(['cover.jpg', 'back.jpg'])
        results = self._find(r'cover')
        self.assertEqual(['cover.jpg'], self._filenames(results))

    def test_case_insensitive(self):
        self._create_files(['Cover.JPG', 'FRONT.png'])
        results = self._find(r'front')
        self.assertEqual(['FRONT.png'], self._filenames(results))

    def test_no_match(self):
        self._create_files(['song.mp3', 'notes.txt'])
        results = self._find(r'cover')
        self.assertEqual([], self._filenames(results))

    def test_type_extraction_from_group(self):
        self._create_files(['front.jpg'])
        results = self._find(r'(front)\.jpg')
        self.assertEqual(['front.jpg'], self._filenames(results))
        self.assertIn('front', results[0].types)

    def test_type_extraction_back(self):
        self._create_files(['back.png'])
        results = self._find(r'(back)\.')
        self.assertEqual(['back.png'], self._filenames(results))
        self.assertIn('back', results[0].types)

    def test_no_group_uses_default_types(self):
        self._create_files(['cover.jpg'])
        results = self._find(r'cover\.jpg')
        self.assertEqual(['cover.jpg'], self._filenames(results))
        self.assertEqual(['front'], results[0].types)

    def test_multiple_matches(self):
        self._create_files(['cover.jpg', 'cover.png', 'back.jpg'])
        results = self._find(r'cover\.')
        self.assertEqual(['cover.jpg', 'cover.png'], self._filenames(results))

    def test_match_in_subdirectory(self):
        self._create_files([os.path.join('sub', 'cover.jpg')])
        results = self._find(r'cover')
        self.assertEqual(['cover.jpg'], self._filenames(results))
        self.assertTrue(os.path.exists(results[0].url.toLocalFile()))

    def test_match_with_relative_start_dir(self):
        # Regression: os.walk(current_dir) yields a root that already includes
        # current_dir. The returned filepath must be os.path.join(root,
        # filename); joining current_dir + root + filename double-prepends the
        # base directory when current_dir is relative, producing a path that
        # never exists (so the image is silently dropped).
        self._create_files([os.path.join('sub', 'cover.jpg')])
        match_re = re.compile(r'cover', re.IGNORECASE)
        cwd = os.getcwd()
        try:
            os.chdir(self.tmpdir)
            results = list(self.provider.find_local_images('sub', match_re))
        finally:
            os.chdir(cwd)
        self.assertEqual(['cover.jpg'], self._filenames(results))
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, results[0].url.toLocalFile())))


class DefaultTypesTest(PicardTestCase):
    def test_default_types_is_single_front(self):
        # Regression: _default_types must be the single-element tuple
        # ('front',), not tuple('front') which explodes into
        # ('f', 'r', 'o', 'n', 't').
        self.assertEqual(('front',), CoverArtProviderLocal._default_types)


class RegexModeRegistrationTest(PicardTestCase):
    def test_regex_mode_is_registered(self):
        mode = get_local_cover_art_mode(REGEX_MODE_ID)
        self.assertIsNotNone(mode)
        self.assertEqual(REGEX_MODE_ID, mode.id)
        self.assertTrue(mode.playground)
        self.assertIsNotNone(mode.make_matcher)

    def test_regex_mode_value_roundtrip(self):
        self.set_config_values(setting={'local_cover_regex': ''})
        mode = get_local_cover_art_mode(REGEX_MODE_ID)
        mode.set_value(r'^cover\.jpg$')
        self.assertEqual(r'^cover\.jpg$', mode.get_value())


class RegexPlaygroundMatcherTest(PicardTestCase):
    def test_empty_value_returns_no_matcher(self):
        errors = []
        self.assertIsNone(_regex_playground_matcher('', errors.append))
        self.assertEqual([], errors)

    def test_valid_pattern_matches(self):
        matcher = _regex_playground_matcher(r'cover', lambda e: None)
        self.assertTrue(matcher('cover.jpg'))
        self.assertFalse(matcher('back.jpg'))

    def test_invalid_pattern_reports_error(self):
        errors = []
        self.assertIsNone(_regex_playground_matcher(r'(', errors.append))
        self.assertEqual(1, len(errors))


class QueueImagesDispatchTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.provider = CoverArtProviderLocal.__new__(CoverArtProviderLocal)
        self.provider.album = MagicMock()
        self.provider.queue_put = MagicMock()

    def test_active_mode_queue_images_is_called(self):
        self.set_config_values(
            setting={
                'local_cover_match_mode': REGEX_MODE_ID,
                'local_cover_regex': r'cover',
            }
        )
        with patch.object(CoverArtProviderLocal, 'find_local_images', return_value=iter([])) as mock_find:
            state = self.provider.queue_images()
        # The regex mode's queue handler walks the album's files.
        self.provider.album.iterfiles.assert_called()
        self.assertEqual(CoverArtProviderLocal.QueueState.FINISHED, state)
        del mock_find

    def test_empty_value_skips_mode(self):
        self.set_config_values(
            setting={
                'local_cover_match_mode': REGEX_MODE_ID,
                'local_cover_regex': '',
            }
        )
        self.provider.queue_images()
        # No value -> the mode's queue_images is never invoked, so files are
        # never iterated.
        self.provider.album.iterfiles.assert_not_called()

    def test_unknown_mode_queues_nothing(self):
        # If the configured mode is not registered (e.g. its plugin was
        # uninstalled), nothing is queued — no silent fallback to another mode.
        self.set_config_values(
            setting={
                'local_cover_match_mode': 'does-not-exist',
                'local_cover_regex': r'cover',
            }
        )
        state = self.provider.queue_images()
        self.provider.album.iterfiles.assert_not_called()
        self.assertEqual(CoverArtProviderLocal.QueueState.FINISHED, state)


class RegexQueueHandlerTest(LocalCoverArtTestBase):
    def test_walks_each_dir_once(self):
        files = []
        for i in range(3):
            f = MagicMock()
            f.filename = f'/music/track{i}.mp3'
            files.append(f)
        self.provider.album = MagicMock()
        self.provider.album.iterfiles.return_value = files
        self.provider.queue_put = MagicMock()
        with patch.object(self.provider, 'find_local_images', return_value=[]) as mock_find:
            _queue_images_regex(self.provider, r'cover')
        mock_find.assert_called_once()


class RegisteredModesTest(PicardTestCase):
    def test_at_least_regex_mode_available(self):
        ids = {m.id for m in local_cover_art_modes()}
        self.assertIn(REGEX_MODE_ID, ids)


def _noop_queue(provider, value):
    pass


class ProviderOptionsLocalPageTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.ui.options')
        self.set_config_values(
            setting={
                'local_cover_regex': r'^cover\.jpg$',
                'local_cover_match_mode': REGEX_MODE_ID,
            }
        )
        self._extra_modes = []

    def tearDown(self):
        for mode in self._extra_modes:
            ext_point_local_cover_art_modes.unregister(mode.queue_images.__module__, lambda m, _id=mode.id: m.id == _id)
        super().tearDown()

    def _register_extra_mode(self, mode_id):
        store = {'value': ''}
        mode = LocalCoverArtMode(
            id=mode_id,
            title=mode_id,
            description=f"{mode_id} description",
            note=f"{mode_id} note",
            queue_images=_noop_queue,
            get_value=lambda: store['value'],
            set_value=lambda v: store.update(value=v),
        )
        register_local_cover_art_mode(mode)
        self._extra_modes.append(mode)
        return mode

    def test_load_applies_regex_mode(self):
        from picard.coverart.providers.local import ProviderOptionsLocal

        page = ProviderOptionsLocal()
        page.load()
        # Field shows the stored regex value and the regex mode's description.
        self.assertEqual(r'^cover\.jpg$', page.ui.local_cover_regex_edit.text())
        self.assertIn('regular expression', page.ui.local_cover_regex_label.text().lower())
        # A single registered mode hides the selector.
        self.assertTrue(page._mode_selector.isHidden())

    def test_save_roundtrips_value(self):
        from picard.coverart.providers.local import ProviderOptionsLocal

        page = ProviderOptionsLocal()
        page.load()
        page.ui.local_cover_regex_edit.setText(r'^folder\.png$')
        page.save()
        self.assertEqual(r'^folder\.png$', get_local_cover_art_mode(REGEX_MODE_ID).get_value())
        self.assertEqual(REGEX_MODE_ID, get_config().setting['local_cover_match_mode'])

    def test_selector_lists_multiple_modes(self):
        from picard.coverart.providers.local import ProviderOptionsLocal

        self._register_extra_mode('zzz-test-mode')
        page = ProviderOptionsLocal()
        page.load()
        # More than one mode -> selector is shown and lists both. Use
        # isHidden() rather than isVisible() since the page itself is not shown.
        self.assertFalse(page._mode_selector.isHidden())
        ids = {page._mode_selector.itemData(i) for i in range(page._mode_selector.count())}
        self.assertIn(REGEX_MODE_ID, ids)
        self.assertIn('zzz-test-mode', ids)


class ModeLifecycleTest(PicardTestCase):
    """Walks the full lifecycle: default regex -> select a plugin-provided mode
    -> the mode is used -> the plugin is removed -> nothing is queued."""

    def setUp(self):
        super().setUp()
        self.set_config_values(
            setting={
                'local_cover_regex': r'^cover\.jpg$',
                'local_cover_match_mode': REGEX_MODE_ID,
            }
        )
        self.provider = CoverArtProviderLocal.__new__(CoverArtProviderLocal)
        self.provider.album = MagicMock()
        self.provider.album.iterfiles.return_value = []
        self.provider.queue_put = MagicMock()
        self._plugin_mode = None
        self.plugin_calls = []

    def tearDown(self):
        self._remove_plugin_mode()
        super().tearDown()

    def _install_plugin_mode(self):
        store = {'value': '%album%.*'}

        def queue_images(provider, value):
            self.plugin_calls.append(value)

        self._plugin_mode = LocalCoverArtMode(
            id='script.mode',
            title='Script',
            description='script',
            note='script',
            queue_images=queue_images,
            get_value=lambda: store['value'],
            set_value=lambda v: store.update(value=v),
        )
        register_local_cover_art_mode(self._plugin_mode)

    def _remove_plugin_mode(self):
        if self._plugin_mode is not None:
            ext_point_local_cover_art_modes.unregister(
                self._plugin_mode.queue_images.__module__,
                lambda m: m.id == 'script.mode',
            )
            self._plugin_mode = None

    def test_full_lifecycle(self):
        # 1. Fresh start: default regex mode is active and used.
        with patch.object(CoverArtProviderLocal, 'find_local_images', return_value=iter([])):
            self.provider.queue_images()
        self.provider.album.iterfiles.assert_called()  # regex handler ran

        # 2. Install the plugin, which registers the script mode.
        self._install_plugin_mode()

        # 3. Select the script mode and save it (as the options page would).
        get_config().setting['local_cover_match_mode'] = 'script.mode'

        # 4. The script mode is now effectively used by queue_images.
        self.provider.queue_images()
        self.assertEqual(['%album%.*'], self.plugin_calls)

        # 5. Remove the plugin while the script mode is still the active setting.
        self._remove_plugin_mode()

        # 6. queue_images now finds no registered mode -> queues nothing (no
        #    silent fallback to regex).
        self.provider.album.iterfiles.reset_mock()
        state = self.provider.queue_images()
        self.provider.album.iterfiles.assert_not_called()
        self.assertEqual(CoverArtProviderLocal.QueueState.FINISHED, state)
