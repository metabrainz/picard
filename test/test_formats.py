import os.path
import unittest
import shutil
from tempfile import mkstemp
import picard.formats
from PyQt4 import QtCore


class FakeTagger():
    def emit(self, *args):
        pass


class FakeConfig():
    def __init__(self):
        self.setting = {
            'enabled_plugins': '',
            'clear_existing_tags': False,
            'remove_images_from_tags': False,
            'write_id3v1': True,
            'id3v2_encoding': 'utf-8',
            'save_images_to_tags': True,
            'write_id3v23': False,
            'remove_ape_from_mp3': False,
            'remove_id3_from_flac': False
        }


class FormatsTest(unittest.TestCase):

    original = None
    tags = []

    def setUp(self):
        if not self.original:
            return
        fd, self.filename = mkstemp(suffix=os.path.splitext(self.original)[1])
        os.close(fd)
        shutil.copy(self.original, self.filename)
        QtCore.QObject.tagger = FakeTagger()
        QtCore.QObject.config = FakeConfig()

    def tearDown(self):
        if not self.original:
            return
        os.unlink(self.filename)

    def test_simple_tags(self):
        if not self.original:
            return
        for i in self.tags:
            if len(i) == 3:
                n, v, e = i
            else:
                n, v = i
                e = v
            f = picard.formats.open(self.filename)
            f._load()
            f.metadata[n] = v
            f.save()
            f = picard.formats.open(self.filename)
            f._load()
            self.assertEqual(f.metadata.getall(n), e, '%s: %r != %r' % (n, f.metadata.getall(n), e))


class FLACTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.flac')
    tags = [
        ('album', ['Foo', 'Bar']),
        ('album', ['1']),
        ('title', ['Foo']),
        ('artist', ['Foo']),
        ('albumartist', ['Foo']),
        ('date', ['2004-00-00'], ['2004']),
        ('artist', ['Foo']),
        ('composer', ['Foo']),
        ('lyricist', ['Foo']),
        ('conductor', ['Foo']),
        ('performer:guest vocal', ['Foo']),
        ('remixer', ['Foo']),
        ('engineer', ['Foo']),
        ('producer', ['Foo']),
        ('grouping', ['Foo']),
        ('subtitle', ['Foo']),
        ('discsubtitle', ['Foo']),
        ('compilation', ['1']),
        ('comment', ['Foo']),
        ('genre', ['Foo']),
        ('bpm', ['Foo']),
        ('mood', ['Foo']),
        ('isrc', ['Foo']),
        ('copyright', ['Foo']),
        ('lyrics', ['Foo']),
        ('media', ['Foo']),
        ('label', ['Foo']),
        ('catalognumber', ['Foo']),
        ('barcode', ['Foo']),
        ('encodedby', ['Foo']),
        ('albumsort', ['Foo']),
        ('albumartistsort', ['Foo']),
        ('artistsort', ['Foo']),
        ('titlesort', ['Foo']),
        ('musicbrainz_trackid', ['Foo']),
        ('musicbrainz_albumid', ['Foo']),
        ('musicbrainz_artistid', ['Foo']),
        ('musicbrainz_albumartistid', ['Foo']),
        ('musicbrainz_trmid', ['Foo']),
        ('musicbrainz_discid', ['Foo']),
        ('musicip_puid', ['Foo']),
        ('releasestatus', ['Foo']),
        ('releasetype', ['Foo']),
    ]


class MP3Test(FormatsTest):
    original = os.path.join('test', 'data', 'test.mp3')
    tags = [
        ('album', ['Foo', 'Bar']),
        ('album', ['1']),
        ('title', ['Foo']),
        ('artist', ['Foo']),
        ('albumartist', ['Foo']),
        ('date', ['2004-00-00']),
        ('artist', ['Foo']),
        ('composer', ['Foo']),
        ('lyricist', ['Foo']),
        ('conductor', ['Foo']),
        ('performer:guest vocal', ['Foo']),
        ('remixer', ['Foo']),
        ('engineer', ['Foo']),
        ('producer', ['Foo']),
        ('grouping', ['Foo']),
        ('subtitle', ['Foo']),
        ('discsubtitle', ['Foo']),
        ('compilation', ['1']),
        #('comment', ['Foo']),
        ('genre', ['Foo']),
        ('bpm', ['Foo']),
        ('mood', ['Foo']),
        ('isrc', ['Foo']),
        ('copyright', ['Foo']),
        # TODO
        ('lyrics', ['Foo'], []),
        ('media', ['Foo']),
        ('label', ['Foo']),
        ('catalognumber', ['Foo']),
        ('barcode', ['Foo']),
        ('encodedby', ['Foo']),
        ('albumsort', ['Foo']),
        ('albumartistsort', ['Foo']),
        ('artistsort', ['Foo']),
        ('titlesort', ['Foo']),
        ('musicbrainz_trackid', ['Foo']),
        ('musicbrainz_albumid', ['Foo']),
        ('musicbrainz_artistid', ['Foo']),
        ('musicbrainz_albumartistid', ['Foo']),
        ('musicbrainz_trmid', ['Foo']),
        ('musicbrainz_discid', ['Foo']),
        ('musicip_puid', ['Foo']),
        ('releasestatus', ['Foo']),
        ('releasetype', ['Foo']),
    ]


class OggVorbisTest(FormatsTest):
    original = os.path.join('test', 'data', 'test.ogg')
    tags = [
        ('album', ['Foo', 'Bar']),
        ('album', ['1']),
        ('title', ['Foo']),
        ('artist', ['Foo']),
        ('albumartist', ['Foo']),
        ('date', ['2004-00-00'], ['2004']),
        ('artist', ['Foo']),
        ('composer', ['Foo']),
        ('lyricist', ['Foo']),
        ('conductor', ['Foo']),
        ('performer:guest vocal', ['Foo']),
        ('remixer', ['Foo']),
        ('engineer', ['Foo']),
        ('producer', ['Foo']),
        ('grouping', ['Foo']),
        ('subtitle', ['Foo']),
        ('discsubtitle', ['Foo']),
        ('compilation', ['1']),
        ('comment', ['Foo']),
        ('genre', ['Foo']),
        ('bpm', ['Foo']),
        ('mood', ['Foo']),
        ('isrc', ['Foo']),
        ('copyright', ['Foo']),
        ('lyrics', ['Foo']),
        ('media', ['Foo']),
        ('label', ['Foo']),
        ('catalognumber', ['Foo']),
        ('barcode', ['Foo']),
        ('encodedby', ['Foo']),
        ('albumsort', ['Foo']),
        ('albumartistsort', ['Foo']),
        ('artistsort', ['Foo']),
        ('titlesort', ['Foo']),
        ('musicbrainz_trackid', ['Foo']),
        ('musicbrainz_albumid', ['Foo']),
        ('musicbrainz_artistid', ['Foo']),
        ('musicbrainz_albumartistid', ['Foo']),
        ('musicbrainz_trmid', ['Foo']),
        ('musicbrainz_discid', ['Foo']),
        ('musicip_puid', ['Foo']),
        ('releasestatus', ['Foo']),
        ('releasetype', ['Foo']),
    ]
