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

from picard.component import Interface

class IOptionsPage(Interface):

    def get_page_info(self):
        pass

    def get_page(self):
        pass

    def load_options(self):
        pass

    def save_options(self):
        pass

class IFileOpener(Interface):

    def get_supported_formats(self):
        pass

    def can_open_file(self, filename):
        pass

    def open_file(self, filename):
        pass

class ITaggerScript(Interface):

    def evaluate_script(self, text, context):
        pass

class IMetadataProcessor(Interface):

    def process_album_metadata(self, metadata, release):
        pass

    def process_track_metadata(self, metadata, release, track):
        pass

