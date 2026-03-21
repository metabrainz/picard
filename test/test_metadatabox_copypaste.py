# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
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

import json
from unittest.mock import MagicMock

from PyQt6 import QtCore

from test.picardtestcase import PicardTestCase

from picard.metadata import MULTI_VALUED_JOINER

from picard.ui.metadatabox import MetadataBox
from picard.ui.metadatabox.mimedatahelper import MimeDataHelper
from picard.ui.metadatabox.tagdiff import TagDiff


class FakeMetadataBox:
    """Minimal stand-in for MetadataBox avoiding QTableWidget instantiation."""

    MIMETYPE_PICARD_TAGS = MetadataBox.MIMETYPE_PICARD_TAGS
    MIMETYPE_TSV = MetadataBox.MIMETYPE_TSV
    MIMETYPE_TEXT = MetadataBox.MIMETYPE_TEXT
    COLUMN_TAG = MetadataBox.COLUMN_TAG
    COLUMN_ORIG = MetadataBox.COLUMN_ORIG
    COLUMN_NEW = MetadataBox.COLUMN_NEW

    def __init__(self, tagger):
        self.tagger = tagger
        self.tag_diff = None
        self.objects = set()
        self.tracks = set()
        self.files = set()
        self._current_item = None
        self._selected_items = []

        self.mimedata_helper = MimeDataHelper()
        self.mimedata_helper.register(
            self.MIMETYPE_PICARD_TAGS,
            encode_func=lambda td: td.to_json().encode('utf-8'),
            decode_func=lambda target, md: target._paste_from_json(md),
        )
        self.mimedata_helper.register(
            self.MIMETYPE_TSV,
            encode_func=lambda td: td.to_tsv().encode('utf-8'),
            decode_func=None,
        )
        self.mimedata_helper.register(
            self.MIMETYPE_TEXT,
            encode_func=lambda td: td.to_tsv().encode('utf-8'),
            decode_func=lambda target, md: target._paste_from_text(md),
        )

    def currentItem(self):
        return self._current_item

    def selectedItems(self):
        return self._selected_items

    def set_current(self, row, column):
        item = MagicMock()
        item.row.return_value = row
        item.column.return_value = column
        self._current_item = item

    def set_selected(self, row_col_pairs):
        self._selected_items = []
        for row, col in row_col_pairs:
            item = MagicMock()
            item.row.return_value = row
            item.column.return_value = col
            self._selected_items.append(item)

    def update(self, drop_album_caches=False):
        pass

    # Bind real MetadataBox methods
    _can_paste = MetadataBox._can_paste
    _paste_from_json = MetadataBox._paste_from_json
    _paste_from_text = MetadataBox._paste_from_text
    _paste_value = MetadataBox._paste_value
    _can_copy = MetadataBox._can_copy
    _copy_value = MetadataBox._copy_value
    _tag_is_editable = MetadataBox._tag_is_editable
    _tag_is_removable = MetadataBox._tag_is_removable
    _set_tag_values_delayed_updates = MetadataBox._set_tag_values_delayed_updates
    _update_objects = MetadataBox._update_objects
    _set_tag_values = MetadataBox._set_tag_values
    get_selected_tags = MetadataBox.get_selected_tags
    _get_row_info = MetadataBox._get_row_info


class MetadataBoxCopyPasteTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        self._clipboard_data = QtCore.QMimeData()
        clipboard = MagicMock()
        clipboard.mimeData.return_value = self._clipboard_data
        clipboard.setText = MagicMock(side_effect=self._set_clipboard_text)
        clipboard.setMimeData = MagicMock(side_effect=self._set_clipboard_mimedata)
        self.tagger.clipboard = MagicMock(return_value=clipboard)
        self.box = FakeMetadataBox(self.tagger)

    def _set_clipboard_text(self, text):
        self._clipboard_data = QtCore.QMimeData()
        self._clipboard_data.setText(text)
        self.tagger.clipboard().mimeData.return_value = self._clipboard_data

    def _set_clipboard_mimedata(self, mimedata):
        self._clipboard_data = mimedata
        self.tagger.clipboard().mimeData.return_value = mimedata

    def _add_tags(self, *tags):
        """Set up tag_diff. tags: (name, old, new) or (name, old, new, readonly)."""
        td = TagDiff()
        for entry in tags:
            td.add(entry[0], old=entry[1], new=entry[2], readonly=entry[3] if len(entry) > 3 else False)
        td.objects += 1
        td.update_tag_names()
        self.box.tag_diff = td

    def _row(self, tag):
        return self.box.tag_diff.tag_names.index(tag)

    def _make_obj(self):
        obj = MagicMock()
        obj.metadata = {}
        self.box.objects.add(obj)
        return obj

    def _json_mimedata(self, data):
        md = QtCore.QMimeData()
        md.setData(MetadataBox.MIMETYPE_PICARD_TAGS, json.dumps(data).encode('utf-8'))
        return md

    def _text_mimedata(self, text):
        md = QtCore.QMimeData()
        md.setText(text)
        return md

    def _select_tag(self, tag, column=MetadataBox.COLUMN_NEW):
        """Point current item and selection at a single tag."""
        row = self._row(tag)
        self.box.set_current(row, column)
        self.box.set_selected([(row, column)])

    # ── _can_paste ──

    def test_can_paste_json(self):
        data = json.dumps({'artist': {'new': ['X']}}).encode('utf-8')
        self._clipboard_data.setData(MetadataBox.MIMETYPE_PICARD_TAGS, data)
        self.assertTrue(self.box._can_paste())

    def test_can_paste_text(self):
        self._clipboard_data.setText("text")
        self.assertTrue(self.box._can_paste())

    def test_cannot_paste_empty(self):
        self.assertFalse(self.box._can_paste())

    def test_cannot_paste_tsv_only(self):
        """TSV has no decode_func registered, so it's not pasteable."""
        self._clipboard_data.setData(MetadataBox.MIMETYPE_TSV, b"x\ty\tz")
        self.assertFalse(self.box._can_paste())

    def test_can_paste_with_multiple_tracks_picard_3238(self):
        """Regression: PICARD-3238 — paste must work with multiple tracks."""
        self._clipboard_data.setText("text")
        self.box.tracks = {MagicMock(), MagicMock(), MagicMock()}
        self.box.files = {MagicMock(), MagicMock()}
        self.assertTrue(self.box._can_paste())

    # ── _paste_from_text ──

    def test_paste_text(self):
        self._add_tags(('artist', ['Old'], ['Cur']))
        self._select_tag('artist')
        obj = self._make_obj()
        list(self.box._paste_from_text(self._text_mimedata('Pasted')))
        self.assertEqual(obj.metadata['artist'], ['Pasted'])

    def test_paste_text_noop_on_orig_column(self):
        self._add_tags(('artist', ['Old'], ['Cur']))
        self._select_tag('artist', MetadataBox.COLUMN_ORIG)
        obj = self._make_obj()
        list(self.box._paste_from_text(self._text_mimedata('X')))
        self.assertNotIn('artist', obj.metadata)

    def test_paste_text_noop_on_readonly(self):
        self._add_tags(('artist', ['Old'], ['Cur'], True))
        self._select_tag('artist')
        obj = self._make_obj()
        list(self.box._paste_from_text(self._text_mimedata('X')))
        self.assertNotIn('artist', obj.metadata)

    def test_paste_text_noop_on_empty(self):
        self._add_tags(('artist', ['Old'], ['Cur']))
        self._select_tag('artist')
        obj = self._make_obj()
        list(self.box._paste_from_text(self._text_mimedata('')))
        self.assertNotIn('artist', obj.metadata)

    def test_paste_text_multi_valued(self):
        self._add_tags(('artist', ['Old'], ['Cur']))
        self._select_tag('artist')
        obj = self._make_obj()
        text = MULTI_VALUED_JOINER.join(['A1', 'A2'])
        list(self.box._paste_from_text(self._text_mimedata(text)))
        self.assertEqual(obj.metadata['artist'], ['A1', 'A2'])

    def test_paste_text_multiple_objects_picard_3238(self):
        """Regression: PICARD-3238 — paste applies to all objects."""
        self._add_tags(('artist', ['Old'], ['Cur']))
        self._select_tag('artist')
        obj1, obj2 = self._make_obj(), self._make_obj()
        list(self.box._paste_from_text(self._text_mimedata('Shared')))
        self.assertEqual(obj1.metadata['artist'], ['Shared'])
        self.assertEqual(obj2.metadata['artist'], ['Shared'])

    # ── _paste_from_json ──

    def test_paste_json(self):
        self._add_tags(('artist', ['O'], ['C']), ('title', ['O'], ['C']))
        obj = self._make_obj()
        data = {'artist': {'new': ['A']}, 'title': {'new': ['T']}}
        list(self.box._paste_from_json(self._json_mimedata(data)))
        self.assertEqual(obj.metadata['artist'], ['A'])
        self.assertEqual(obj.metadata['title'], ['T'])

    def test_paste_json_prefers_new_over_old(self):
        self._add_tags(('artist', ['O'], ['C']))
        obj = self._make_obj()
        list(self.box._paste_from_json(self._json_mimedata({'artist': {'new': ['N'], 'old': ['O']}})))
        self.assertEqual(obj.metadata['artist'], ['N'])

    def test_paste_json_falls_back_to_old(self):
        self._add_tags(('artist', ['O'], ['C']))
        obj = self._make_obj()
        list(self.box._paste_from_json(self._json_mimedata({'artist': {'old': ['Fallback']}})))
        self.assertEqual(obj.metadata['artist'], ['Fallback'])

    def test_paste_json_skips_readonly(self):
        self._add_tags(('artist', ['O'], ['C'], True))
        obj = self._make_obj()
        list(self.box._paste_from_json(self._json_mimedata({'artist': {'new': ['X']}})))
        self.assertNotIn('artist', obj.metadata)

    def test_paste_json_skips_empty_value(self):
        self._add_tags(('artist', ['O'], ['C']))
        obj = self._make_obj()
        list(self.box._paste_from_json(self._json_mimedata({'artist': {}})))
        self.assertNotIn('artist', obj.metadata)

    def test_paste_json_allows_unknown_tags(self):
        self._add_tags(('artist', ['O'], ['C']))
        obj = self._make_obj()
        list(self.box._paste_from_json(self._json_mimedata({'genre': {'new': ['Rock']}})))
        self.assertEqual(obj.metadata['genre'], ['Rock'])

    def test_paste_json_invalid_data(self):
        md = QtCore.QMimeData()
        md.setData(MetadataBox.MIMETYPE_PICARD_TAGS, b'not json')
        self.assertEqual(list(self.box._paste_from_json(md)), [])

    def test_paste_json_multiple_objects_picard_3238(self):
        """Regression: PICARD-3238 — JSON paste applies to all objects."""
        self._add_tags(('artist', ['O'], ['C']))
        obj1, obj2 = self._make_obj(), self._make_obj()
        list(self.box._paste_from_json(self._json_mimedata({'artist': {'new': ['S']}})))
        self.assertEqual(obj1.metadata['artist'], ['S'])
        self.assertEqual(obj2.metadata['artist'], ['S'])

    # ── _paste_value dispatch ──

    def test_paste_value_prefers_json_over_text(self):
        self._add_tags(('artist', ['O'], ['C']))
        self._select_tag('artist')
        obj = self._make_obj()
        obj.update = MagicMock()
        md = QtCore.QMimeData()
        md.setData(MetadataBox.MIMETYPE_PICARD_TAGS, json.dumps({'artist': {'new': ['JSON']}}).encode('utf-8'))
        md.setText('Text')
        self._set_clipboard_mimedata(md)
        self.box._paste_value()
        self.assertEqual(obj.metadata['artist'], ['JSON'])

    def test_paste_value_falls_back_to_text(self):
        self._add_tags(('artist', ['O'], ['C']))
        self._select_tag('artist')
        obj = self._make_obj()
        obj.update = MagicMock()
        self._set_clipboard_text('Text')
        self.box._paste_value()
        self.assertEqual(obj.metadata['artist'], ['Text'])

    def test_paste_value_empty_clipboard_shows_message(self):
        self._add_tags(('artist', ['O'], ['C']))
        self.box._paste_value()
        self.tagger.window.set_statusbar_message.assert_called_once()

    # ── _copy_value ──

    def test_copy_single_value(self):
        self._add_tags(('artist', ['Old'], ['New']))
        for column, expected in (
            (MetadataBox.COLUMN_NEW, 'New'),
            (MetadataBox.COLUMN_ORIG, 'Old'),
            (MetadataBox.COLUMN_TAG, 'artist'),
        ):
            self._select_tag('artist', column)
            self.box._copy_value()
            self.tagger.clipboard().setText.assert_called_with(expected)

    def test_copy_multi_valued(self):
        self._add_tags(('artist', ['A1', 'A2'], ['A1', 'A2']))
        self._select_tag('artist')
        self.box._copy_value()
        self.tagger.clipboard().setText.assert_called_with(MULTI_VALUED_JOINER.join(['A1', 'A2']))

    def test_copy_multiple_tags(self):
        self._add_tags(('artist', ['OA'], ['NA']), ('title', ['OT'], ['NT']))
        self.box.set_selected(
            [
                (self._row('artist'), MetadataBox.COLUMN_NEW),
                (self._row('title'), MetadataBox.COLUMN_NEW),
            ]
        )
        self.box._copy_value()
        self.tagger.clipboard().setMimeData.assert_called_once()
        md = self.tagger.clipboard().setMimeData.call_args[0][0]
        # All 3 MIME types present
        for fmt in (MetadataBox.MIMETYPE_PICARD_TAGS, MetadataBox.MIMETYPE_TSV, MetadataBox.MIMETYPE_TEXT):
            self.assertTrue(md.hasFormat(fmt))
        # JSON content correct
        data = json.loads(md.data(MetadataBox.MIMETYPE_PICARD_TAGS).data())
        self.assertEqual(data['artist']['new'], ['NA'])
        self.assertEqual(data['title']['new'], ['NT'])
