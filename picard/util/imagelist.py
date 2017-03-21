# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2017 Antonio Larrosa <alarrosa@suse.com>
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


def get_image_type(image):
    return image.types_as_string()


class ImageList(list):

    def __init__(self):
        super(ImageList, self).__init__()

    def __eq__(self, other):
        return sorted(self, key=get_image_type) == sorted(other, key=get_image_type)

    def __getslice__(self, i, j):
        i = max(0, min(i, len(self)))
        j = max(0, min(j, len(self)))
        r = ImageList()
        r[:] = [self[it] for it in range(i, j)]
        return r
