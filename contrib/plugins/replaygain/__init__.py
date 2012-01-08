# -*- coding: utf-8 -*-

# Changelog:
#   [2008-03-14] Initial version with support for Ogg Vorbis, FLAC and MP3

PLUGIN_NAME = u"ReplayGain"
PLUGIN_AUTHOR = u"Philipp Wolfer"
PLUGIN_DESCRIPTION = """Calculate ReplayGain for selected files and albums."""
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.10", "0.15", "0.16"]


from PyQt4 import QtCore
from subprocess import check_call
from picard.album import Album
from picard.track import Track
from picard.file import File
from picard.util import encode_filename, decode_filename, partial
from picard.ui.options import register_options_page, OptionsPage
from picard.config import TextOption
from picard.ui.itemviews import (BaseAction, register_file_action,
                                 register_album_action)
from picard.plugins.replaygain.ui_options_replaygain import Ui_ReplayGainOptionsPage

# Path to various replay gain tools. There must be a tool for every supported
# audio file format.
REPLAYGAIN_COMMANDS = {
   "Ogg Vorbis": ("replaygain_vorbisgain_command", "replaygain_vorbisgain_options"),
   "MPEG-1 Audio": ("replaygain_mp3gain_command", "replaygain_mp3gain_options"),
   "FLAC": ("replaygain_metaflac_command", "replaygain_metaflac_options"),
   "WavPack": ("replaygain_wvgain_command", "replaygain_wvgain_options"),
   }

def calculate_replay_gain_for_files(files, format, tagger):
    """Calculates the replay gain for a list of files in album mode."""
    file_list = ['%s' % encode_filename(f.filename) for f in files]

    if REPLAYGAIN_COMMANDS.has_key(format) \
        and tagger.config.setting[REPLAYGAIN_COMMANDS[format][0]]:
        command = tagger.config.setting[REPLAYGAIN_COMMANDS[format][0]]
        options = tagger.config.setting[REPLAYGAIN_COMMANDS[format][1]].split(' ')
        tagger.log.debug('%s %s %s' % (command, ' '.join(options), decode_filename(' '.join(file_list))))
        check_call([command] + options + file_list)
    else:
        raise Exception, 'ReplayGain: Unsupported format %s' % (format)

class ReplayGain(BaseAction):
    NAME = N_("Calculate replay &gain...")

    def _add_file_to_queue(self, file):
        self.tagger.other_queue.put((
            partial(self._calculate_replaygain, file),
            partial(self._replaygain_callback, file),
            QtCore.Qt.NormalEventPriority))

    def callback(self, objs):
        for obj in objs:
            if isinstance(obj, Track):
                for files in obj.linked_files:
                    self._add_file_to_queue(file)
            elif isinstance(obj, File):
                self._add_file_to_queue(obj)

    def _calculate_replaygain(self, file):
        self.tagger.window.set_statusbar_message(N_('Calculating replay gain for "%s"...'), file.filename)
        calculate_replay_gain_for_files([file], file.NAME, self.tagger)

    def _replaygain_callback(self, file, result=None, error=None):
        if not error:
            self.tagger.window.set_statusbar_message(N_('Replay gain for "%s" successfully calculated.'), file.filename)
        else:
            self.tagger.window.set_statusbar_message(N_('Could not calculate replay gain for "%s".'), file.filename)

class AlbumGain(BaseAction):
    NAME = N_("Calculate album &gain...")

    def callback(self, objs):
        albums = [o for o in objs if isinstance(o, Album)]
        for album in albums:
            self.tagger.other_queue.put((
                partial(self._calculate_albumgain, album),
                partial(self._albumgain_callback, album),
                QtCore.Qt.NormalEventPriority))

    def split_files_by_type(self, files):
        """Split the given files by filetype into separate lists."""
        files_by_format = {}

        for file in files:
            if not files_by_format.has_key(file.NAME):
                files_by_format[file.NAME] = [file]
            else:
                files_by_format[file.NAME].append(file)

        return files_by_format

    def _calculate_albumgain(self, album):
        self.tagger.window.set_statusbar_message(N_('Calculating album gain for "%s"...'), album.metadata["album"])
        filelist = [t.linked_files[0] for t in album.tracks if t.is_linked()]

        for format, files in self.split_files_by_type(filelist).iteritems():
            calculate_replay_gain_for_files(files, format, self.tagger)

    def _albumgain_callback(self, album, result=None, error=None):
        if not error:
            self.tagger.window.set_statusbar_message(N_('Album gain for "%s" successfully calculated.'), album.metadata["album"])
        else:
            self.tagger.window.set_statusbar_message(N_('Could not calculate album gain for "%s".'), album.metadata["album"])

class ReplayGainOptionsPage(OptionsPage):

    NAME = "replaygain"
    TITLE = "ReplayGain"
    PARENT = "plugins"

    options = [
        TextOption("setting", "replaygain_vorbisgain_command", "vorbisgain"),
        TextOption("setting", "replaygain_vorbisgain_options", "-asf"),
        TextOption("setting", "replaygain_mp3gain_command", "mp3gain"),
        TextOption("setting", "replaygain_mp3gain_options", "-a"),
        TextOption("setting", "replaygain_metaflac_command", "metaflac"),
        TextOption("setting", "replaygain_metaflac_options", "--add-replay-gain"),
        TextOption("setting", "replaygain_wvgain_command", "wvgain"),
        TextOption("setting", "replaygain_wvgain_options", "-a")
    ]

    def __init__(self, parent=None):
        super(ReplayGainOptionsPage, self).__init__(parent)
        self.ui = Ui_ReplayGainOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.vorbisgain_command.setText(self.config.setting["replaygain_vorbisgain_command"])
        self.ui.mp3gain_command.setText(self.config.setting["replaygain_mp3gain_command"])
        self.ui.metaflac_command.setText(self.config.setting["replaygain_metaflac_command"])
        self.ui.wvgain_command.setText(self.config.setting["replaygain_wvgain_command"])

    def save(self):
        self.config.setting["replaygain_vorbisgain_command"] = unicode(self.ui.vorbisgain_command.text())
        self.config.setting["replaygain_mp3gain_command"] = unicode(self.ui.mp3gain_command.text())
        self.config.setting["replaygain_metaflac_command"] = unicode(self.ui.metaflac_command.text())
        self.config.setting["replaygain_wvgain_command"] = unicode(self.ui.wvgain_command.text())

register_file_action(ReplayGain())
register_album_action(AlbumGain())
register_options_page(ReplayGainOptionsPage)
