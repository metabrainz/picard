# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
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

from picard.ui.infodialogcommon import *

class InfoDialog(InfoDialogCommon):

    def __init__(self, file, parent=None):
        InfoDialogCommon.__init__(self, file, parent)
        self.file = file
        self.setWindowTitle(_("Info") + " - " + file.base_filename)
        self.load_info()

    def load_info(self):
        file = self.file
        info = []
        info.append((_('Filename:'), file.filename))
        if '~format' in file.orig_metadata:
            info.append((_('Format:'), file.orig_metadata['~format']))
        try:
            size = os.path.getsize(encode_filename(file.filename))
            if size < 1024:
                size = '%d B' % size
            elif size < 1024 * 1024:
                size = '%0.1f kB' % (size / 1024.0)
            else:
                size = '%0.1f MB' % (size / 1024.0 / 1024.0)
            info.append((_('Size:'), size))
        except:
            pass
        if file.orig_metadata.length:
            info.append((_('Length:'), format_time(file.orig_metadata.length)))
        if '~bitrate' in file.orig_metadata:
            info.append((_('Bitrate:'), '%s kbps' % file.orig_metadata['~bitrate']))
        if '~sample_rate' in file.orig_metadata:
            info.append((_('Sample rate:'), '%s Hz' % file.orig_metadata['~sample_rate']))
        if '~bits_per_sample' in file.orig_metadata:
            info.append((_('Bits per sample:'), str(file.orig_metadata['~bits_per_sample'])))
        if '~channels' in file.orig_metadata:
            ch = file.orig_metadata['~channels']
            if ch == 1: ch = _('Mono')
            elif ch == 2: ch = _('Stereo')
            else: ch = str(ch)
            info.append((_('Channels:'), ch))
        text = '<br/>'.join(map(lambda i: '<b>%s</b><br/>%s' % i, info))
        self.ui.info.setText(text)

        self.display_images()
