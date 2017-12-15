import unittest
from unittest.mock import patch
from urllib.parse import urlparse, parse_qs
from picard.browser.filelookup import FileLookup
from picard.util import webbrowser2


SERVER = 'musicbrainz.org'
PORT = 443
LOCAL_PORT = "8000"


class BrowserLookupTest(unittest.TestCase):

    def setUp(self):
        self.lookup = FileLookup(None, SERVER, PORT, LOCAL_PORT)

    @patch.object(webbrowser2, 'open')
    def test_entity_lookups(self, mock_open):
        lookups = {
            "recording": {'function': self.lookup.recording_lookup, 'path': 'recording'},
            "track": {'function': self.lookup.track_lookup, 'path': 'track'},
            "album": {'function': self.lookup.album_lookup, 'path': 'release'},
            "work": {'function': self.lookup.work_lookup, 'path': 'work'},
            "artist": {'function': self.lookup.artist_lookup, 'path': 'artist'},
            "albumartist": {'function': self.lookup.artist_lookup, 'path': 'artist'},
            "releasegroup": {'function': self.lookup.release_group_lookup, 'path': 'release-group'},
        }
        for i, type_ in enumerate(lookups):
            lookups[type_]['function']("123")

            url = urlparse(string_(mock_open.call_args[0][0]))
            path = url.path.split('/')[1:]
            query_args = parse_qs(url.query)

            self.assertEqual(mock_open.call_count, i + 1)
            self.assertEqual(url.netloc, "%s:%s" % (SERVER, PORT))

            self.assertEqual(lookups[type_]['path'], path[0])
            self.assertEqual("123", path[1])

            self.assertIn('tport', query_args)
            self.assertEqual(query_args['tport'][0], '8000')
