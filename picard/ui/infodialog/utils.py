# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2011-2014 Michael Wiencek
# Copyright (C) 2012-2014, 2017, 2019 Wieland Hoffmann
# Copyright (C) 2013-2014, 2018-2025 Laurent Monin
# Copyright (C) 2014, 2017, 2020 Sophist-UK
# Copyright (C) 2016 Rahul Raturi
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017-2019 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2018-2024 Philipp Wolfer
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Suryansh Shakya
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

from collections import (
    defaultdict,
    namedtuple,
)
from html import escape
import re

from picard.album import Album
from picard.i18n import gettext as _
from picard.util import (
    bytes2human,
    format_time,
)


def format_file_info(file_):
    info = []
    info.append((_("Filename:"), file_.filename))
    if '~format' in file_.orig_metadata:
        info.append((_("Format:"), file_.orig_metadata['~format']))
    if '~filesize' in file_.orig_metadata:
        size = file_.orig_metadata['~filesize']
        try:
            sizestr = "%s (%s)" % (bytes2human.decimal(size), bytes2human.binary(size))
        except ValueError:
            sizestr = _("unknown")
        info.append((_("Size:"), sizestr))
    if file_.orig_metadata.length:
        info.append((_("Length:"), format_time(file_.orig_metadata.length)))
    if '~bitrate' in file_.orig_metadata:
        info.append((_("Bitrate:"), "%s kbps" % file_.orig_metadata['~bitrate']))
    if '~sample_rate' in file_.orig_metadata:
        info.append((_("Sample rate:"), "%s Hz" % file_.orig_metadata['~sample_rate']))
    if '~bits_per_sample' in file_.orig_metadata:
        info.append((_("Bits per sample:"), str(file_.orig_metadata['~bits_per_sample'])))
    if '~channels' in file_.orig_metadata:
        ch = file_.orig_metadata['~channels']
        if ch == '1':
            ch = _("Mono")
        elif ch == '2':
            ch = _("Stereo")
        info.append((_("Channels:"), ch))
    return '<br/>'.join(map(lambda i: '<b>%s</b> %s' %
                            (escape(i[0]), escape(i[1])), info))


def format_tracklist(cluster):
    info = []
    info.append('<b>%s</b> %s' % (_("Album:"), escape(cluster.metadata['album'])))
    info.append('<b>%s</b> %s' % (_("Artist:"), escape(cluster.metadata['albumartist'])))
    info.append("")
    TrackListItem = namedtuple('TrackListItem', 'number, title, artist, length')
    tracklists = defaultdict(list)
    if isinstance(cluster, Album):
        objlist = cluster.tracks
    else:
        objlist = cluster.iterfiles(False)
    for obj_ in objlist:
        m = obj_.metadata
        artist = m['artist'] or m['albumartist'] or cluster.metadata['albumartist']
        track = TrackListItem(m['tracknumber'], m['title'], artist,
                              m['~length'])
        tracklists[obj_.discnumber].append(track)

    def sorttracknum(track):
        try:
            return int(track.number)
        except ValueError:
            try:
                # This allows to parse values like '3' but also '3/10'
                m = re.search(r'^\d+', track.number)
                return int(m.group(0))
            except AttributeError:
                return 0

    ndiscs = len(tracklists)
    for discnumber in sorted(tracklists):
        tracklist = tracklists[discnumber]
        if ndiscs > 1:
            info.append('<b>%s</b>' % (_("Disc %d") % discnumber))
        lines = ['%s %s - %s (%s)' % item for item in sorted(tracklist, key=sorttracknum)]
        info.append('<b>%s</b><br />%s<br />' % (_("Tracklist:"),
                    '<br />'.join(escape(s).replace(' ', '&nbsp;') for s in lines)))
    return '<br/>'.join(info)


def text_as_html(text):
    return '<br />'.join(escape(str(text))
        .replace('\t', ' ')
        .replace(' ', '&nbsp;')
        .splitlines())
