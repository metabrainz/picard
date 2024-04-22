# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021, 2023 Philipp Wolfer
# Copyright (C) 2021, 2024 Laurent Monin
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


from collections import namedtuple

from picard.i18n import gettext as _


SECS_IN_DAY = 86400
SECS_IN_HOUR = 3600
SECS_IN_MINUTE = 60


Duration = namedtuple('Duration', 'days hours minutes seconds')


def euclidian_div(a, b):
    return a // b, a % b


def seconds_to_dhms(seconds):
    days, seconds = euclidian_div(seconds, SECS_IN_DAY)
    hours, seconds = euclidian_div(seconds, SECS_IN_HOUR)
    minutes, seconds = euclidian_div(seconds, SECS_IN_MINUTE)
    return Duration(days=days, hours=hours, minutes=minutes, seconds=seconds)


def get_timestamp(seconds):
    time = seconds_to_dhms(seconds)
    if time.days > 0:
        return _("%(days).2dd %(hours).2dh") % time._asdict()
    if time.hours > 0:
        return _("%(hours).2dh %(minutes).2dm") % time._asdict()
    if time.minutes > 0:
        return _("%(minutes).2dm %(seconds).2ds") % time._asdict()
    if time.seconds > 0:
        return _("%(seconds).2ds") % time._asdict()
    return ''
