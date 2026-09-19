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


from unittest import (
    TestCase,
    mock,
)

from picard.cli import _bootstrap


class TestCliBootstrapConfigUpgrade(TestCase):
    """The CLI bootstrap must run config upgrades non-interactively.

    Regression test for PICARD-3446: minimal_init previously loaded the config
    without calling run_config_upgrades, so an old config used via the CLI was
    never migrated. External Qt/config setup is patched out so this stays a
    fast unit test of the wiring only.
    """

    def test_minimal_init_runs_config_upgrades_non_interactively(self):
        with (
            mock.patch.object(_bootstrap.QtCore, 'QCoreApplication'),
            mock.patch.object(_bootstrap, 'init_options'),
            mock.patch.object(_bootstrap, 'setup_config'),
            mock.patch.object(_bootstrap, 'get_config', return_value=mock.sentinel.config),
            mock.patch.object(_bootstrap, 'run_config_upgrades') as run_config_upgrades,
        ):
            _bootstrap.minimal_init('some.ini')

        run_config_upgrades.assert_called_once_with(mock.sentinel.config, interactive=False)
