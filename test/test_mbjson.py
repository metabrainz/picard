import json
import os
from test.picardtestcase import PicardTestCase

from picard import config
from picard.album import Album
from picard.mbjson import (
    artist_to_metadata,
    country_list_from_node,
    label_info_from_node,
    media_formats_from_node,
    medium_to_metadata,
    recording_to_metadata,
    release_group_to_metadata,
    release_to_metadata,
    track_to_metadata,
)
from picard.metadata import Metadata
from picard.releasegroup import ReleaseGroup
from picard.track import Track

settings = {
    "standardize_tracks": False,
    "standardize_artists": False,
    "standardize_releases": False,
    "translate_artist_names": True,
    "standardize_instruments": True,
    "artist_locale": 'en'
}


class MBJSONTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self.init_test(self.filename)

    def init_test(self, filename):
        config.setting = settings.copy()
        self.json_doc = None
        with open(os.path.join('test', 'data', 'ws_data', filename), encoding='utf-8') as f:
            self.json_doc = json.load(f)


class ReleaseTest(MBJSONTest):

    filename = 'release.json'

    def test_release(self):
        m = Metadata()
        a = Album("1")
        release_to_metadata(self.json_doc, m, a)
        self.assertEqual(m['album'], 'The Dark Side of the Moon')
        self.assertEqual(m['albumartist'], 'Pink Floyd')
        self.assertEqual(m['albumartistsort'], 'Pink Floyd')
        self.assertEqual(m['asin'], 'b123')
        self.assertEqual(m['barcode'], '123')
        self.assertEqual(m['catalognumber'], 'SHVL 804')
        self.assertEqual(m['date'], '1973-03-24')
        self.assertEqual(m['label'], 'Harvest')
        self.assertEqual(m['musicbrainz_albumartistid'], '83d91898-7763-47d7-b03b-b92132375c47')
        self.assertEqual(m['musicbrainz_albumid'], 'b84ee12a-09ef-421b-82de-0441a926375b')
        self.assertEqual(m['releasecountry'], 'GB')
        self.assertEqual(m['releasestatus'], 'official')
        self.assertEqual(m['script'], 'Latn')
        self.assertEqual(m['~albumartists'], 'Pink Floyd')
        self.assertEqual(m['~albumartists_sort'], 'Pink Floyd')
        self.assertEqual(m['~releaselanguage'], 'eng')
        self.assertEqual(a.genres, {
            'genre1': 6, 'genre2': 3,
            'tag1': 6, 'tag2': 3 })
        for artist in a._album_artists:
            self.assertEqual(artist.genres, {
                'british': 2,
                'progressive rock': 10 })

    def test_media_formats_from_node(self):
        formats = media_formats_from_node(self.json_doc['media'])
        self.assertEqual(formats, '12" Vinyl')


class NullReleaseTest(MBJSONTest):

    filename = 'release_null.json'

    def test_release(self):
        m = Metadata()
        a = Album("1")
        release_to_metadata(self.json_doc, m, a)
        self.assertEqual(m, {})

    def test_media_formats_from_node(self):
        formats = media_formats_from_node(self.json_doc['media'])
        self.assertEqual(formats, '(unknown)')


class RecordingTest(MBJSONTest):

    filename = 'recording.json'

    def test_recording(self):
        m = Metadata()
        t = Track('1')
        recording_to_metadata(self.json_doc, m, t)
        self.assertEqual(m['artist'], 'Ed Sheeran')
        self.assertEqual(m['artists'], 'Ed Sheeran')
        self.assertEqual(m['artistsort'], 'Sheeran, Ed')
        self.assertEqual(m['isrc'], 'GBAHS1400099')
        self.assertEqual(m['language'], 'eng')
        self.assertEqual(m['musicbrainz_artistid'], 'b8a7c51f-362c-4dcb-a259-bc6e0095f0a6')
        self.assertEqual(m['musicbrainz_recordingid'], 'cb2cc207-8125-445c-9ef9-6ea44eee959a')
        self.assertEqual(m['musicbrainz_workid'], 'dc469dc8-198e-42e5-b5a7-6be2f0a95ac0')
        self.assertEqual(m['performer:'], 'Ed Sheeran')
        self.assertEqual(m['performer:lead vocals'], 'Ed Sheeran')
        self.assertEqual(m['performer:guitar family'], 'Ed Sheeran')
        self.assertEqual(m['title'], 'Thinking Out Loud')
        self.assertEqual(m['work'], 'Thinking Out Loud')
        self.assertEqual(m['writer'], 'Ed Sheeran; Amy Wadge')
        self.assertEqual(m['~artists_sort'], 'Sheeran, Ed')
        self.assertEqual(m['~length'], '4:41')
        self.assertEqual(m['~recordingtitle'], 'Thinking Out Loud')
        self.assertEqual(t.genres, {
            'blue-eyed soul': 1,
            'pop': 3 })
        for artist in t._track_artists:
            self.assertEqual(artist.genres, {
                'dance-pop': 1,
                'guitarist': 0 })

    def test_recording_instrument_credits(self):
        m = Metadata()
        t = Track('1')
        config.setting['standardize_instruments'] = False
        recording_to_metadata(self.json_doc, m, t)
        self.assertEqual(m['performer:vocals'], 'Ed Sheeran')
        self.assertEqual(m['performer:acoustic guitar'], 'Ed Sheeran')


class NullRecordingTest(MBJSONTest):

    filename = 'recording_null.json'

    def test_recording(self):
        m = Metadata()
        t = Track("1")
        recording_to_metadata(self.json_doc, m, t)
        self.assertEqual(m, {})


class RecordingCreditsTest(MBJSONTest):

    filename = 'recording_credits.json'

    def test_recording_solo_vocals(self):
        m = Metadata()
        t = Track("1")
        recording_to_metadata(self.json_doc, m, t)
        config.setting["standardize_artists"] = False
        self.assertTrue('performer:solo' not in m)
        self.assertEqual(m['performer:solo vocals'], 'Frida')

    def test_recording_standardize_artist_credits(self):
        m = Metadata()
        t = Track("1")
        config.setting["standardize_artists"] = True
        recording_to_metadata(self.json_doc, m, t)
        self.assertTrue('performer:solo' not in m)
        self.assertEqual(m['performer:solo vocals'], 'Anni-Frid Lyngstad')


class TrackTest(MBJSONTest):

    filename = 'track.json'

    def test_track(self):
        t = Track("1")
        m = t.metadata
        track_to_metadata(self.json_doc, t)
        self.assertEqual(m['title'], 'Speak to Me')
        self.assertEqual(m['musicbrainz_recordingid'], 'bef3fddb-5aca-49f5-b2fd-d56a23268d63')
        self.assertEqual(m['musicbrainz_trackid'], 'd4156411-b884-368f-a4cb-7c0101a557a2')
        self.assertEqual(m['title'], 'Speak to Me')
        self.assertEqual(m['~length'], '1:08')
        self.assertEqual(m['tracknumber'], '1')
        self.assertEqual(m['~musicbrainz_tracknumber'], 'A1')
        self.assertEqual(m['~recordingcomment'], 'original stereo mix')
        self.assertEqual(m['~recordingtitle'], 'Speak to Me')


class NullTrackTest(MBJSONTest):

    filename = 'track_null.json'

    def test_track(self):
        t = Track("1")
        m = t.metadata
        track_to_metadata(self.json_doc, t)
        self.assertEqual(m, {})


class MediaTest(MBJSONTest):

    filename = 'media.json'

    def test_track(self):
        m = Metadata()
        medium_to_metadata(self.json_doc, m)
        self.assertEqual(m['discnumber'], '1')
        self.assertEqual(m['media'], '12" Vinyl')
        self.assertEqual(m['totaltracks'], '10')


class NullMediaTest(MBJSONTest):

    filename = 'media_null.json'

    def test_track(self):
        m = Metadata()
        medium_to_metadata(self.json_doc, m)
        self.assertEqual(m, {})


class ArtistTest(MBJSONTest):

    filename = 'artist.json'

    def test_artist(self):
        m = Metadata()
        artist_to_metadata(self.json_doc, m)
        self.assertEqual(m['area'], 'United Kingdom')
        self.assertEqual(m['beginarea'], 'Hebden Bridge')
        self.assertEqual(m['begindate'], '1991-02-17')
        self.assertEqual(m['gender'], 'Male')
        self.assertEqual(m['musicbrainz_artistid'], 'b8a7c51f-362c-4dcb-a259-bc6e0095f0a6')
        self.assertEqual(m['name'], 'Ed Sheeran')
        self.assertEqual(m['type'], 'Person')


class NullArtistTest(MBJSONTest):

    filename = 'artist_null.json'

    def test_artist(self):
        m = Metadata()
        artist_to_metadata(self.json_doc, m)
        self.assertEqual(m, {})


class ReleaseGroupTest(MBJSONTest):

    filename = 'release_group.json'

    def test_release_group(self):
        m = Metadata()
        r = ReleaseGroup("1")
        release_group_to_metadata(self.json_doc, m, r)
        self.assertEqual(m['musicbrainz_releasegroupid'], 'f5093c06-23e3-404f-aeaa-40f72885ee3a')
        self.assertEqual(m['originaldate'], '1973-03-24')
        self.assertEqual(m['originalyear'], '1973')
        self.assertEqual(m['releasetype'], 'album')
        self.assertEqual(m['~primaryreleasetype'], 'album')
        self.assertEqual(m['~releasegroup'], 'The Dark Side of the Moon')
        self.assertEqual(r.genres, {'test2': 3, 'test': 6})


class NullReleaseGroupTest(MBJSONTest):

    filename = 'release_group_null.json'

    def test_release_group(self):
        m = Metadata()
        r = ReleaseGroup("1")
        release_group_to_metadata(self.json_doc, m, r)
        self.assertEqual(m, {})


class CountryListTest(MBJSONTest):

    filename = 'country.json'

    def test_country_from_node(self):
        country_list = country_list_from_node(self.json_doc)
        self.assertEqual(['GB'], country_list)


class NullCountryListTest(MBJSONTest):

    filename = 'country_null.json'

    def test_country_from_node(self):
        country_list = country_list_from_node(self.json_doc)
        self.assertEqual(country_list, [])


class LabelInfoTest(MBJSONTest):

    filename = 'label_info.json'

    def _label_info(self, n):
        return label_info_from_node(self.json_doc['releases'][n]['label-info'])

    def test_label_info_from_node_0(self):
        self.assertEqual((['naïve'], ['NJ628311']), self._label_info(0))

    def test_label_info_from_node_1(self):
        self.assertEqual((['naïve'], []), self._label_info(1))

    def test_label_info_from_node_2(self):
        self.assertEqual((['naïve'], []), self._label_info(2))

    def test_label_info_from_node_3(self):
        self.assertEqual(([], ["[None]"]), self._label_info(3))


class NullLabelInfoTest(MBJSONTest):

    filename = 'label_info_null.json'

    def test_label_info_from_node_0(self):
        label_info = label_info_from_node(self.json_doc['releases'][0]['label-info'])
        self.assertEqual(label_info, ([], []))
