# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Laurent Monin
# Copyright (C) 2021 Gabriel Ferreira
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


SECS_IN_DAY = 86400
SECS_IN_HOUR = 3600
SECS_IN_MINUTE = 60


def euclidian_div(a, b):
    return a // b, a % b


def seconds_to_dhms(seconds):
    days, seconds = euclidian_div(seconds, SECS_IN_DAY)
    hours, seconds = euclidian_div(seconds, SECS_IN_HOUR)
    minutes, seconds = euclidian_div(seconds, SECS_IN_MINUTE)
    return days, hours, minutes, seconds


def get_timestamp(seconds):
    d, h, m, s = seconds_to_dhms(seconds)
    if d > 0:
        return _("%.2dd %.2dh") % (d, h)
    if h > 0:
        return _("%.2dh %.2dm") % (h, m)
    if m > 0:
        return _("%.2dm %.2ds") % (m, s)
    if s > 0:
        return _("%.2ds") % s
    return ''
