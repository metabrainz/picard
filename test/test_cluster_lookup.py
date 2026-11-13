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

from unittest.mock import MagicMock

from test.picardtestcase import PicardTestCase

from picard.cluster import Cluster


class ClusterLookupCallbackTest(PicardTestCase):
    """A custom lookup callback must not leave the cluster's lookup pending."""

    def setUp(self):
        super().setUp()
        self.patch_tagger_instance('picard.item')
        self.set_config_values(setting={'query_limit': 25})
        self.tagger.mb_api = MagicMock()
        self.callbacks = []

        def fake_find_releases(callback, **kwargs):
            # Asynchronous like the real web service: the callback runs later.
            self.callbacks.append(callback)
            return MagicMock()  # a task handle

        self.tagger.mb_api.find_releases.side_effect = fake_find_releases

    def test_custom_callback_releases_pending_lookup(self):
        cluster = Cluster('Greatest Hits', 'The Artist')
        received = []

        def capture(document, http, error):
            received.append(document)

        cluster.lookup_metadata(callback=capture)
        self.assertEqual(1, len(self.callbacks))
        self.callbacks[0]({'releases': []}, None, None)
        self.assertEqual([{'releases': []}], received)

        # The request completed, so a new lookup must send a new request.
        cluster.lookup_metadata(callback=capture)
        self.assertEqual(2, len(self.callbacks))

    def test_pending_lookup_is_not_duplicated(self):
        cluster = Cluster('Greatest Hits', 'The Artist')
        cluster.lookup_metadata(callback=lambda *args: None)
        cluster.lookup_metadata(callback=lambda *args: None)
        self.assertEqual(1, len(self.callbacks))
