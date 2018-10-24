import json
import os
from test.picardtestcase import PicardTestCase

from picard import config
from picard.acoustid.json_helpers import parse_recording
from picard.mbjson import recording_to_metadata
from picard.metadata import Metadata
from picard.track import Track

settings = {
    "standardize_tracks": False,
    "standardize_artists": False,
    "standardize_releases": False,
    "translate_artist_names": True,
    "artist_locale": 'en'
}


class AcoustIDTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.init_test(self.filename)

    def init_test(self, filename):
        config.setting = settings.copy()
        self.json_doc = None
        with open(os.path.join('test', 'data', 'ws_data', filename), encoding='utf-8') as f:
            self.json_doc = json.load(f)


class RecordingTest(AcoustIDTest):
    filename = 'acoustid.json'

    def test_recording(self):
        parsed_recording = parse_recording(self.json_doc)
        release = parsed_recording['releases'][0]
        artist_credit = parsed_recording['artist-credit'][0]
        self.assertEqual(parsed_recording['id'], '017830c1-d1cf-46f3-8801-aaaa0a930223')
        self.assertEqual(parsed_recording['length'], 225000)
        self.assertEqual(parsed_recording['title'], 'Nina')
        self.assertEqual(release['media'], [{'track': {}, 'format': 'CD', 'track-count': 12}])
        self.assertEqual(release['title'], 'x')
        self.assertEqual(release['id'], 'a2b25883-306f-4a53-809a-a234737c209d')
        self.assertEqual(release['release-group'], {'id': 'c24e5416-cd2e-4cff-851b-5faa78db98a2'})
        self.assertEqual(release['country'], 'XE')
        self.assertEqual(artist_credit['artist'], {'sort-name': 'Ed Sheeran',
                                                   'name': 'Ed Sheeran',
                                                   'id': 'b8a7c51f-362c-4dcb-a259-bc6e0095f0a6'})
        self.assertEqual(artist_credit['name'], 'Ed Sheeran')


class NullRecordingTest(AcoustIDTest):
    filename = 'acoustid_null.json'

    def test_recording(self):
        m = Metadata()
        t = Track("1")
        parsed_recording = parse_recording(self.json_doc)
        recording_to_metadata(parsed_recording, m, t)
        self.assertEqual(m, {})
