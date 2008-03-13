# -*- coding: utf-8 -*-

PLUGIN_NAME = u"ReplayGain"
PLUGIN_AUTHOR = u"Philipp Wolfer"
PLUGIN_DESCRIPTION = """Calculate ReplayGain for selected files and albums."""
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9.0"]


from PyQt4 import QtCore
from subprocess import check_call
from picard.album import Album
from picard.track import Track
from picard.file import File
from picard.util import encode_filename, partial
from picard.ui.itemviews import (BaseAction, register_file_action,
                                 register_album_action)

# TODO: Make the paths configurable
REPLAYGAIN_COMMANDS = {"Ogg Vorbis" : ["vorbisgain", "-asf"],
                       "FLAC" : ["metaflac", "--add-replay-gain"],
                       "MPEG-1 Audio" : ["mp3gain", "-a"]
                       }

def calculate_replay_gain_for_files(files, format):
    """Calculates the replay gain for a list of files in album mode."""
    file_list = [encode_filename(f.filename) for f in files]
    
    if REPLAYGAIN_COMMANDS.has_key(format):
        check_call(REPLAYGAIN_COMMANDS[format] + file_list)
    else:
        raise Exception, 'ReplayGain: Unsupported format %s' % (format)

class ReplayGain(BaseAction):
    NAME = N_("Calculate replay gain...")
    
    def callback(self, objs):
        for obj in objs:
            if isinstance(obj, Track) and obj.linked_file:
                file = obj.linked_file
            elif isinstance(obj, File):
                file = obj
            
            if file:
                self.tagger.other_queue.put((
                    partial(self._calculate_replaygain, file),
                    partial(self._replaygain_callback, file),
                    QtCore.Qt.NormalEventPriority))
            
    def _calculate_replaygain(self, file):
        self.tagger.window.set_statusbar_message(N_('Calculating replay gain for "%s"...'), file.filename)
        try:
            calculate_replay_gain_for_files([file], file.NAME)
        except Exception, inst:
            return inst

    def _replaygain_callback(self, file, result=None, error=None):
        if not error:
            self.tagger.window.set_statusbar_message(N_('Replay gain for "%s" successfully calculated.'), file.filename)
        else:
            self.tagger.window.set_statusbar_message(N_('Could not calculate replay gain for "%s".'), file.filename)

class AlbumGain(BaseAction):
    NAME = N_("Calculate album gain...")
    
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
        filelist = [t.linked_file for t in album.tracks if t.linked_file]
        
        for format, files in self.split_files_by_type(filelist).iteritems():
            calculate_replay_gain_for_files(files, format)
    
    def _albumgain_callback(self, album, result=None, error=None):
        if not error:
            self.tagger.window.set_statusbar_message(N_('Album gain for "%s" successfully calculated.'), album.metadata["album"])
        else:
            self.tagger.window.set_statusbar_message(N_('Could not calculate album gain for "%s".'), album.metadata["album"])
            
register_file_action(ReplayGain())
register_album_action(AlbumGain())
