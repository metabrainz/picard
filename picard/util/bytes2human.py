# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2013 Laurent Monin
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

import locale

"""
Helper class to convert bytes to human-readable form
It supports i18n through gettext, decimal and binary units.

>>> n = 1572864
>>> [binary(n), decimal(n)]
['1.5 MiB', '1.6 MB']
"""

# used to force gettextization
_BYTES_STRINGS_I18N = (
    N_('%s B'),
    N_('%s kB'),
    N_('%s KiB'),
    N_('%s MB'),
    N_('%s MiB'),
    N_('%s GB'),
    N_('%s GiB'),
    N_('%s TB'),
    N_('%s TiB'),
    N_('%s PB'),
    N_('%s PiB'),
)


def decimal(number, scale=1):
    """
    Convert bytes to short human-readable string, decimal mode

    >>> [decimal(n) for n in [1000, 1024, 15500]]
    ['1 kB', '1 kB', '15.5 kB']
    """
    return short_string(int(number), 1000, scale)


def binary(number, scale=1):
    """
    Convert bytes to short human-readable string, binary mode
    >>> [binary(n) for n in [1000, 1024, 15500]]
    ['1000 B', '1 KiB', '15.1 KiB']
    """
    return short_string(int(number), 1024, scale)


def short_string(number, multiple, scale=1):
    """
    Returns short human-readable string for `number` bytes
    >>> [short_string(n, 1024, 2) for n in [1000, 1100, 15500]]
    ['1000 B', '1.07 KiB', '15.14 KiB']
    >>> [short_string(n, 1000, 1) for n in [10000, 11000, 1550000]]
    ['10 kB', '11 kB', '1.6 MB']
    """
    num, unit = calc_unit(number, multiple)
    n = int(num)
    nr = round(num, scale)
    if n == nr or unit == 'B':
        fmt = '%d'
        num = n
    else:
        fmt = '%%0.%df' % scale
        num = nr
    fmtnum = locale.format(fmt, num)
    return _("%s " + unit) % fmtnum


def calc_unit(number, multiple=1000):
    """
    Calculate rounded number of multiple * bytes, finding best unit

    >>> calc_unit(12456, 1024)
    (12.1640625, 'KiB')
    >>> calc_unit(-12456, 1000)
    (-12.456, 'kB')
    >>> calc_unit(0, 1001)
    Traceback (most recent call last):
        ...
    ValueError: multiple parameter has to be 1000 or 1024
    """
    if number < 0:
        sign = -1
        number = -number
    else:
        sign = 1
    n = float(number)
    if multiple == 1000:
        k, b = 'k', 'B'
    elif multiple == 1024:
        k, b = 'K', 'iB'
    else:
        raise ValueError('multiple parameter has to be 1000 or 1024')

    suffixes = ["B"] + [i + b for i in k + "MGTP"]
    for suffix in suffixes:
        if n < multiple or suffix == suffixes[-1]:
            return (sign * n, suffix)
        else:
            n /= multiple
