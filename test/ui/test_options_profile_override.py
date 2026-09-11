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
import shutil

from test.picardtestcase import PicardTestCase

from picard.config import (
    Config,
    Option,
    ProfileConfigSection,
    TextOption,
)

from picard.ui.options.dialog import profile_option_is_override


class TestProfileOptionIsOverride(PicardTestCase):
    """The field highlighting and the page-level warning message must share a
    single definition of what counts as a profile *override* (value differs
    from base) versus merely *tracked* (present but not changing the value).

    See PICARD: the server address field was highlighted as "overridden" only
    "sometimes", contradicting the bottom-of-page warning which always claimed
    an override.
    """

    def setUp(self):
        super().setUp()
        self.tmp_directory = self.mktmpdir()
        self.configpath = os.path.join(self.tmp_directory, 'test.ini')
        shutil.copy(os.path.join('test', 'data', 'test.ini'), self.configpath)
        self.addCleanup(os.remove, self.configpath)
        self.config = Config.from_file(None, self.configpath)
        self.addCleanup(self.cleanup_config_obj)
        self.old_registry = dict(Option.registry)
        Option.registry = {}
        self.addCleanup(self.restore_registry)

        TextOption('setting', 'server_host', 'musicbrainz.org', in_profile=True)
        with self.config.setting.no_profile():
            self.config.setting['server_host'] = 'musicbrainz.org'

    def restore_registry(self):
        Option.registry = self.old_registry

    def cleanup_config_obj(self):
        self.config.sync()
        self.config = None

    def test_none_value_is_tracked_not_override(self):
        # Tracked with no value set yet is never an override.
        self.assertFalse(profile_option_is_override(self.config, 'server_host', None))

    def test_value_equal_to_base_is_tracked_not_override(self):
        # This is the "sometimes" case: the profile tracks the option but its
        # stored value equals the base value, so it must NOT count as override.
        self.assertFalse(profile_option_is_override(self.config, 'server_host', 'musicbrainz.org'))

    def test_value_differing_from_base_is_override(self):
        self.assertTrue(profile_option_is_override(self.config, 'server_host', 'beta.musicbrainz.org'))

    def test_value_type_conversion_before_compare(self):
        # A string profile value equal to the base after conversion is tracked.
        TextOption('setting', 'server_host', 'musicbrainz.org', in_profile=True)
        self.assertFalse(profile_option_is_override(self.config, 'server_host', 'musicbrainz.org'))

    def test_plugin_key_uses_stored_base_not_default(self):
        # A plugin option whose stored base value differs from its default.
        # A profile tracking it with a value equal to the stored base value
        # must be classified as tracked, NOT overridden. Regression: the base
        # value was previously read from opt.default only.
        TextOption('plugin.abc', 'greeting', 'default_value', in_profile=True)
        section = ProfileConfigSection(self.config, 'plugin.abc')
        with self.config.setting.no_profile():
            section['greeting'] = 'base_value'

        key = 'plugin.abc/greeting'
        # Equal to the stored base value -> tracked
        self.assertFalse(profile_option_is_override(self.config, key, 'base_value'))
        # Equal to the default but different from the stored base -> override
        self.assertTrue(profile_option_is_override(self.config, key, 'default_value'))
        # Different from both -> override
        self.assertTrue(profile_option_is_override(self.config, key, 'other_value'))
