# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2014 Laurent Monin
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


def printable_node(node, indent=0):
    """
    Print a XmlNode so output can used in test scripts

    Useful to debug mbxml.py mostly and to create unit tests using "real" nodes.

    Example of usage:

        from picard.util.devutil import printable_node
        from picard import log

        def _translate_artist_node(node):
            log.debug(printable_node(node))
            ...

    will output to debug log something like:

        D: 01:35:56 XmlNode(
            attribs={u'id': u'28503ab7-8bf2-4666-a7bd-2644bfc7cb1d'},
            children={
                u'name': [XmlNode(text=u'Dream Theater')],
                u'alias_list': [XmlNode(
                        attribs={u'count': u'3'},
                        children={u'alias': [
                                XmlNode(
                                    text=u'Dream Theatre',
                                    attribs={u'sort_name': u'Dream Theatre'}
                                ),
                                XmlNode(
                                    text=u'DreamTheater',
                                    attribs={u'sort_name': u'DreamTheater'}
                                ),
                                XmlNode(
                                    text=u'Majesty',
                                    attribs={u'sort_name': u'Majesty'}
                                )
                            ]}
                    )],
                u'sort_name': [XmlNode(text=u'Dream Theater')]
            }
        )
    """

    indentstr = " "*4
    def indented(front, l, back, indent):
        ind0 = indentstr*indent
        ind1 = indentstr*(indent+1)
        if not l:
            return front + back
        if len(l) > 1:
            return front + "\n" + ',\n'.join([ind1 + x for x in l]) + "\n" + ind0 + back
        else:
            return front + l[0] + back

    el = []
    if node.text:
        el.append('text=' + repr(node.text).decode('unicode-escape'))

    if node.attribs:
        l = []
        for k,v in node.attribs.items():
            l.append(repr(k).decode('unicode-escape') + ': ' + repr(v).decode('unicode-escape'))
        el.append(indented('attribs={', l, '}', indent+1))

    if node.children:
        l = []
        for k, v in node.children.items():
            l.append(
                indented(
                    repr(k).decode('unicode-escape') + ': [',
                    [printable_node(x, indent+3) for x in v],
                    ']',
                    indent+2
                )
            )
        el.append(indented('children={', l, '}', indent+1))

    return indented('XmlNode(', el, ')', indent)
