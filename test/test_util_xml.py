# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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


from unittest import TestCase

from picard.util.xml import (
    XmlNode,
    parse_xml,
)


test_xml = """
<document foo="bar">
  <element>foo</element>
  <element>bar</element>
</document>
"""


class XmlNodeTest(TestCase):

    def test_append_child(self):
        node = XmlNode()
        child = node.append_child('child')
        self.assertEqual(node.children['child'][0], child)
        self.assertEqual(node.child[0], child)

    def test_append_child_from_existing_node(self):
        node = XmlNode()
        child_node = XmlNode()
        child = node.append_child('child', child_node)
        self.assertEqual(child_node, child)

    def test_repr(self):
        node = XmlNode()
        self.assertEqual(repr(node), repr(node.__dict__))

    def test_attribute_error(self):
        node = XmlNode()
        self.assertRaises(AttributeError, lambda: node.foo)


class ParseXmlTest(TestCase):

    def test_parse_xml(self):
        xml = parse_xml(test_xml)
        document = xml.document[0]
        self.assertEqual(document.attribs['foo'], 'bar')
        self.assertEqual(document.foo, 'bar')
        self.assertEqual(document.element[0].text, 'foo')
        self.assertEqual(document.element[1].text, 'bar')
