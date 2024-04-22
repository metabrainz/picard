# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sambhav Kothari
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018, 2020-2021, 2023 Laurent Monin
# Copyright (C) 2019-2023 Philipp Wolfer
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


from unittest.mock import MagicMock

from PySide6.QtCore import QUrl

from test.picardtestcase import PicardTestCase

from picard.acoustid.manager import Submission
from picard.metadata import Metadata
from picard.webservice import WebService
from picard.webservice.api_helpers import (
    AcoustIdAPIHelper,
    APIHelper,
    MBAPIHelper,
    build_lucene_query,
    escape_lucene_query,
)


class APITest(PicardTestCase):

    def setUp(self):
        super().setUp()
        base_url = "http://abc.com/v1"
        self.path = "/test/more/test"
        self.complete_url = QUrl(base_url + self.path)
        self.ws = MagicMock(auto_spec=WebService)
        self.api = APIHelper(self.ws, base_url=base_url)

    def _test_ws_function_args(self, ws_function):
        self.assertGreater(ws_function.call_count, 0)
        self.assertEqual(ws_function.call_args[1]['url'], self.complete_url)

    def test_get(self):
        self.api.get(self.path, None)
        self._test_ws_function_args(self.ws.get_url)

    def test_post(self):
        self.api.post(self.path, None, None)
        self._test_ws_function_args(self.ws.post_url)

    def test_put(self):
        self.api.put(self.path, None, None)
        self._test_ws_function_args(self.ws.put_url)

    def test_delete(self):
        self.api.delete(self.path, None)
        self._test_ws_function_args(self.ws.delete_url)


class MBAPITest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.config = {'server_host': "mb.org", "server_port": 443}
        self.set_config_values(self.config)
        self.ws = MagicMock(auto_spec=WebService)
        self.api = MBAPIHelper(self.ws)

    def _test_ws_function_args(self, ws_function):
        self.assertGreater(ws_function.call_count, 0)
        url = ws_function.call_args[1]['url']
        self.assertTrue(url.toString().startswith("https://mb.org/"))
        self.assertTrue(url.path().startswith("/ws/2/"))

    def assertInPath(self, ws_function, path):
        self.assertIn(path, ws_function.call_args[1]['url'].path())

    def assertNotInPath(self, ws_function, path):
        self.assertNotIn(path, ws_function.call_args[1]['url'].path())

    def assertInQuery(self, ws_function, argname, value=None):
        unencoded_query_args = ws_function.call_args[1]['unencoded_queryargs']
        self.assertIn(argname, unencoded_query_args)
        self.assertEqual(value, unencoded_query_args[argname])

    def _test_inc_args(self, ws_function, arg_list):
        self.assertInQuery(self.ws.get_url, 'inc', self.api._make_inc_arg(arg_list))

    def test_get_release(self):
        inc_args_list = ['test']
        self.api.get_release_by_id("1", None, inc=inc_args_list)
        self._test_ws_function_args(self.ws.get_url)
        self.assertInPath(self.ws.get_url, "/release/1")
        self._test_inc_args(self.ws.get_url, inc_args_list)

    def test_get_track(self):
        inc_args_list = ['test']
        self.api.get_track_by_id("1", None, inc=inc_args_list)
        self._test_ws_function_args(self.ws.get_url)
        self.assertInPath(self.ws.get_url, "/recording/1")
        self._test_inc_args(self.ws.get_url, inc_args_list)

    def test_get_collection(self):
        inc_args_list = ["releases", "artist-credits", "media"]
        self.api.get_collection("1", None)
        self._test_ws_function_args(self.ws.get_url)
        self.assertInPath(self.ws.get_url, "collection")
        self.assertInPath(self.ws.get_url, "1/releases")
        self._test_inc_args(self.ws.get_url, inc_args_list)

    def test_get_collection_list(self):
        self.api.get_collection_list(None)
        self._test_ws_function_args(self.ws.get_url)
        self.assertInPath(self.ws.get_url, "collection")
        self.assertNotInPath(self.ws.get_url, "releases")

    def test_put_collection(self):
        self.api.put_to_collection("1", ["1", "2", "3"], None)
        self._test_ws_function_args(self.ws.put_url)
        self.assertInPath(self.ws.put_url, "collection/1/releases/1;2;3")

    def test_delete_collection(self):
        self.api.delete_from_collection("1", ["1", "2", "3", "4"] * 200, None)
        collection_string = ";".join(["1", "2", "3", "4"] * 100)
        self._test_ws_function_args(self.ws.delete_url)
        self.assertInPath(self.ws.delete_url, "collection/1/releases/" + collection_string)
        self.assertNotInPath(self.ws.delete_url, collection_string + ";" + collection_string)
        self.assertEqual(self.ws.delete_url.call_count, 2)

    def test_xml_ratings_empty(self):
        ratings = dict()
        xmldata = self.api._xml_ratings(ratings)
        self.assertEqual(
            xmldata,
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<metadata xmlns="http://musicbrainz.org/ns/mmd-2.0#">'
            '<recording-list></recording-list>'
            '</metadata>'
        )

    def test_xml_ratings_one(self):
        ratings = {("recording", 'a'): 1}
        xmldata = self.api._xml_ratings(ratings)
        self.assertEqual(
            xmldata,
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<metadata xmlns="http://musicbrainz.org/ns/mmd-2.0#">'
            '<recording-list>'
            '<recording id="a"><user-rating>20</user-rating></recording>'
            '</recording-list>'
            '</metadata>'
        )

    def test_xml_ratings_multiple(self):
        ratings = {
            ("recording", 'a'): 1,
            ("recording", 'b'): 2,
            ("nonrecording", 'c'): 3,
        }
        xmldata = self.api._xml_ratings(ratings)
        self.assertEqual(
            xmldata,
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<metadata xmlns="http://musicbrainz.org/ns/mmd-2.0#">'
            '<recording-list>'
            '<recording id="a"><user-rating>20</user-rating></recording>'
            '<recording id="b"><user-rating>40</user-rating></recording>'
            '</recording-list>'
            '</metadata>'
        )

    def test_xml_ratings_encode(self):
        ratings = {("recording", '<a&"\'>'): 0}
        xmldata = self.api._xml_ratings(ratings)
        self.assertEqual(
            xmldata,
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<metadata xmlns="http://musicbrainz.org/ns/mmd-2.0#">'
            '<recording-list>'
            '<recording id="&lt;a&amp;&quot;\'&gt;"><user-rating>0</user-rating></recording>'
            '</recording-list>'
            '</metadata>'
        )

    def test_xml_ratings_raises_value_error(self):
        ratings = {("recording", 'a'): 'foo'}
        self.assertRaises(ValueError, self.api._xml_ratings, ratings)

    def test_collection_request(self):
        releases = tuple("r"+str(i) for i in range(13))
        generator = self.api._collection_request("test", releases, batchsize=5)
        batch = next(generator)
        self.assertEqual(batch, '/collection/test/releases/r0;r1;r2;r3;r4')
        batch = next(generator)
        self.assertEqual(batch, '/collection/test/releases/r5;r6;r7;r8;r9')
        batch = next(generator)
        self.assertEqual(batch, '/collection/test/releases/r10;r11;r12')
        with self.assertRaises(StopIteration):
            next(generator)

    def test_make_inc_arg(self):
        result = self.api._make_inc_arg(['b', 'a', '', 1, (), 0])
        expected = '1+a+b'
        self.assertEqual(result, expected)


class AcoustdIdAPITest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.config = {'acoustid_apikey': "apikey"}
        self.set_config_values(self.config)
        self.ws = MagicMock(auto_spec=WebService)
        self.api = AcoustIdAPIHelper(self.ws)
        self.api.acoustid_host = 'acoustid_host'
        self.api.acoustid_port = 443
        self.api.client_key = "key"
        self.api.client_version = "ver"

    def test_encode_acoustid_args_static(self):
        args = {'a': '1', 'b': 'v a l'}
        result = self.api._encode_acoustid_args(args)
        expected = 'a=1&b=v%20a%20l&client=key&clientversion=ver&format=json'
        self.assertEqual(result, expected)

    def test_encode_acoustid_args_static_empty(self):
        args = dict()
        result = self.api._encode_acoustid_args(args)
        expected = 'client=key&clientversion=ver&format=json'
        self.assertEqual(result, expected)

    def test_submissions_to_args(self):
        submissions = [
            Submission('f1', 1, recordingid='or1', metadata=Metadata(musicip_puid='p1')),
            Submission('f2', 2, recordingid='or2', metadata=Metadata(musicip_puid='p2')),
        ]
        submissions[0].recordingid = 'r1'
        submissions[1].recordingid = 'r2'
        result = self.api._submissions_to_args(submissions)
        expected = {
            'user': 'apikey',
            'fingerprint.0': 'f1', 'duration.0': '1', 'mbid.0': 'r1', 'puid.0': 'p1',
            'fingerprint.1': 'f2', 'duration.1': '2', 'mbid.1': 'r2', 'puid.1': 'p2'
        }
        self.assertEqual(result, expected)

    def test_submissions_to_args_invalid_duration(self):
        metadata1 = Metadata({
            'title': 'The Track',
            'artist': 'The Artist',
            'album': 'The Album',
            'albumartist': 'The Album Artist',
            'tracknumber': '4',
            'discnumber': '2',
        }, length=100000)
        metadata2 = Metadata({
            'year': '2022'
        }, length=100000)
        metadata3 = Metadata({
            'date': '1980-08-30'
        }, length=100000)
        metadata4 = Metadata({
            'date': '08-30'
        }, length=100000)
        submissions = [
            Submission('f1', 500000, recordingid='or1', metadata=metadata1),
            Submission('f2', 500000, recordingid='or2', metadata=metadata2),
            Submission('f3', 500000, recordingid='or3', metadata=metadata3),
            Submission('f4', 500000, recordingid='or4', metadata=metadata4),
        ]
        submissions[0].recordingid = 'r1'
        submissions[1].recordingid = 'r2'
        submissions[1].recordingid = 'r3'
        submissions[1].recordingid = 'r4'
        result = self.api._submissions_to_args(submissions)
        expected = {
            'user': 'apikey',
            'fingerprint.0': 'f1',
            'duration.0': '500000',
            'track.0': metadata1['title'],
            'artist.0': metadata1['artist'],
            'album.0': metadata1['album'],
            'albumartist.0': metadata1['albumartist'],
            'trackno.0': metadata1['tracknumber'],
            'discno.0': metadata1['discnumber'],
            'fingerprint.1': 'f2',
            'duration.1': '500000',
            'year.1': '2022',
            'fingerprint.2': 'f3',
            'duration.2': '500000',
            'year.2': '1980',
            'fingerprint.3': 'f4',
            'duration.3': '500000',
        }
        self.assertEqual(result, expected)


class LuceneHelpersTest(PicardTestCase):

    def test_escape_lucene_query(self):
        self.assertEqual('', escape_lucene_query(''))
        self.assertEqual(
            '\\+\\-\\&\\|\\!\\(\\)\\{\\}\\[\\]\\^\\"\\~\\*\\?\\:\\\\\\/',
            escape_lucene_query('+-&|!(){}[]^"~*?:\\/'))

    def test_build_lucene_query(self):
        args = {
            'title': 'test',
            'artist': 'foo:bar',
            'tnum': '3'
        }
        query = build_lucene_query(args)
        self.assertEqual('title:(test) artist:(foo\\:bar) tnum:(3)', query)
