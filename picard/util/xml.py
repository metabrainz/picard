# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2017 Sambhav Kothari
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

import re

from PyQt5.QtCore import QXmlStreamReader

_node_name_re = re.compile('[^a-zA-Z0-9]')


class XmlNode(object):

    def __init__(self):
        self.text = ''
        self.children = {}
        self.attribs = {}

    def __repr__(self):
        return repr(self.__dict__)

    def append_child(self, name, node=None):
        if node is None:
            node = XmlNode()
        self.children.setdefault(name, []).append(node)
        return node

    def __getattr__(self, name):
        try:
            return self.children[name]
        except KeyError:
            try:
                return self.attribs[name]
            except KeyError:
                raise AttributeError(name)


def _node_name(n):
    return _node_name_re.sub('_', n)


def parse_xml(response):
    stream = QXmlStreamReader(response)
    document = XmlNode()
    current_node = document
    path = []

    while not stream.atEnd():
        stream.readNext()

        if stream.isStartElement():
            node = XmlNode()
            attrs = stream.attributes()

            for i in range(attrs.count()):
                attr = attrs.at(i)
                node.attribs[_node_name(attr.name())] = attr.value()

            current_node.append_child(_node_name(stream.name()), node)
            path.append(current_node)
            current_node = node

        elif stream.isEndElement():
            current_node = path.pop()

        elif stream.isCharacters():
            current_node.text += stream.text()
    return document
