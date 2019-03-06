from test.picardtestcase import PicardTestCase

from picard import config
from picard.const.sys import IS_WIN
from picard.file import File
from picard.metadata import Metadata
from picard.script import register_script_function
from picard.util.scripttofilename import script_to_filename


settings = {
    'ascii_filenames': False,
    'enabled_plugins': [],
    'windows_compatibility': False,
}


def func_has_file(parser):
    return '1' if parser.file else ''


register_script_function(lambda p: '1' if p.file else '', 'has_file')


class ScriptToFilenameTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        config.setting = settings.copy()

    def test_plain_filename(self):
        metadata = Metadata()
        filename = script_to_filename('AlbumArt', metadata)
        self.assertEqual('AlbumArt', filename)

    def test_simple_script(self):
        metadata = Metadata()
        metadata['artist'] = 'AC/DC'
        metadata['album'] = 'The Album'
        filename = script_to_filename('%album%', metadata)
        self.assertEqual('The Album', filename)
        filename = script_to_filename('%artist%/%album%', metadata)
        self.assertEqual('AC_DC/The Album', filename)

    def test_file_metadata(self):
        metadata = Metadata()
        file = File('somepath/somefile.mp3')
        self.assertEqual('', script_to_filename('$has_file()', metadata))
        self.assertEqual('1', script_to_filename('$has_file()', metadata, file=file))

    def test_ascii_filenames(self):
        metadata = Metadata()
        metadata['artist'] = 'Die Ärzte'
        settings = config.setting.copy()
        settings['ascii_filenames'] = False
        filename = script_to_filename('%artist% éöü', metadata, settings=settings)
        self.assertEqual('Die Ärzte éöü', filename)
        settings['ascii_filenames'] = True
        filename = script_to_filename('%artist% éöü', metadata, settings=settings)
        self.assertEqual('Die Arzte eou', filename)

    def test_windows_compatibility(self):
        metadata = Metadata()
        metadata['artist'] = '*:'
        settings = config.setting.copy()
        settings['windows_compatibility'] = False
        expect_orig = '*:?'
        expect_compat = '___'
        filename = script_to_filename('%artist%?', metadata, settings=settings)
        self.assertEqual(expect_compat if IS_WIN else expect_orig, filename)
        settings['windows_compatibility'] = True
        filename = script_to_filename('%artist%?', metadata, settings=settings)
        self.assertEqual(expect_compat, filename)

    def test_remove_null_chars(self):
        metadata = Metadata()
        filename = script_to_filename('a\x00b\x00', metadata)
        self.assertEqual('ab', filename)

    def test_remove_tabs_and_linebreaks_chars(self):
        metadata = Metadata()
        filename = script_to_filename('a\tb\nc', metadata)
        self.assertEqual('abc', filename)

    def test_preserve_leading_and_trailing_whitespace(self):
        metadata = Metadata()
        metadata['artist'] = 'The Artist'
        filename = script_to_filename(' %artist% ', metadata)
        self.assertEqual(' The Artist ', filename)
