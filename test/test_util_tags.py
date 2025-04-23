# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2020 Philipp Wolfer
# Copyright (C) 2020-2022 Laurent Monin
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Serial
# Copyright (C) 2025 Bob Swift
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


import unittest.mock as mock

from test.picardtestcase import PicardTestCase

from picard.util.tags import (
    TagVar,
    TagVars,
    display_tag_name,
    display_tag_tooltip,
    markdown,
    parse_comment_tag,
    parse_subtag,
    script_variable_tag_names,
)


class TagVarsTest(PicardTestCase):

    def setUp(self):
        self.tagvar_only_sd = TagVar('only_sd', shortdesc='only_sd_shortdesc')
        self.tagvar_sd_ld = TagVar('sd_ld', shortdesc='sd_ld_shortdesc', longdesc='sd_ld_longdesc')
        self.tagvar_hidden = TagVar('hidden', is_hidden=True)
        self.tagvar_hidden_sd = TagVar('hidden_sd', is_hidden=True, shortdesc='hidden_sd_shortdesc')
        self.tagvar_notag = TagVar('notag', is_tag=False)
        self.tagvar_nodesc = TagVar('nodesc')
        self.tagvar_notes1 = TagVar('notes1', shortdesc='notes1_sd', longdesc='notes1_ld', is_preserved=True, is_calculated=True,
                                   is_file_info=True, is_hidden=True, not_script_variable=True)
        self.tagvar_notes2 = TagVar('notes2', shortdesc='notes2_sd', longdesc='notes2_ld', is_file_info=True, not_from_mb=True)
        self.tagvar_notes3 = TagVar('notes3', shortdesc='notes3_sd', longdesc='notes3_ld', not_from_mb=True)

    def test_invalid_tagvar(self):
        with self.assertRaises(TypeError):
            TagVars('not_a_tag_var')

    def test_tagvars_len(self):
        tagvars = TagVars(
            self.tagvar_only_sd,
            self.tagvar_sd_ld,
        )
        self.assertEqual(len(tagvars), 2)

    def test_tagvars_append(self):
        tagvars = TagVars()
        tagvar = TagVar('extra')
        tagvars.append(tagvar)
        self.assertEqual(tagvars[-1], tagvar)

    def test_tagvars_pop(self):
        tagvars = TagVars(
            self.tagvar_only_sd,
            self.tagvar_sd_ld,
        )
        self.assertEqual(self.tagvar_sd_ld, tagvars.pop(1))
        self.assertEqual(self.tagvar_only_sd, tagvars.pop())
        self.assertEqual(len(tagvars), 0)

    def test_tagvars_extend(self):
        tagvars = TagVars(self.tagvar_only_sd)
        tagvars.extend(TagVars(self.tagvar_sd_ld))
        self.assertEqual(self.tagvar_only_sd, tagvars[0])
        self.assertEqual(self.tagvar_sd_ld, tagvars[1])
        self.assertEqual(len(tagvars), 2)

    def test_tagvars_del(self):
        tagvars = TagVars(self.tagvar_only_sd)
        self.assertEqual(len(tagvars), 1)
        del tagvars[0]
        self.assertEqual(len(tagvars), 0)

    def test_tagvars_dupe(self):
        tagvars = TagVars(self.tagvar_only_sd)
        with self.assertRaises(ValueError):
            tagvars.append(self.tagvar_only_sd)

    def test_tagvars_names(self):
        tagvars = TagVars(
            self.tagvar_only_sd,
            self.tagvar_sd_ld,
            self.tagvar_hidden,
            self.tagvar_notag,
        )
        names = tuple(tagvars.names())
        self.assertEqual(names, ('only_sd', 'sd_ld', '~hidden', 'notag'))

    def test_tagvars_script_names(self):
        tagvars = TagVars(
            self.tagvar_only_sd,
            self.tagvar_hidden,
        )
        script_names = tuple(tagvar.script_name() for tagvar in tagvars)
        self.assertEqual(script_names, ('only_sd', '_hidden'))

    def test_tagvars_names_selector(self):
        tagvars = TagVars(
            self.tagvar_only_sd,
            self.tagvar_sd_ld,
            self.tagvar_hidden,
            self.tagvar_notag,
        )
        names = tuple(tagvars.names(selector=lambda tv: tv.is_tag))
        self.assertEqual(names, ('only_sd', 'sd_ld', '~hidden'))

        names = tuple(tagvars.names(selector=lambda tv: tv.is_tag and not tv.is_hidden))
        self.assertEqual(names, ('only_sd', 'sd_ld'))

    def test_tagvars_desc(self):
        tagvars = TagVars(
            self.tagvar_nodesc,
            self.tagvar_only_sd,
            self.tagvar_sd_ld,
        )
        shortdescs = [tv.shortdesc for tv in tagvars]
        self.assertEqual(shortdescs, ['nodesc', 'only_sd_shortdesc', 'sd_ld_shortdesc'])
        longdescs = [tv.longdesc for tv in tagvars]
        self.assertEqual(longdescs, ['nodesc', 'only_sd_shortdesc', 'sd_ld_longdesc'])

    def test_tagvars_display_name(self):
        tagvars = TagVars(
            self.tagvar_nodesc,
            self.tagvar_hidden,
            self.tagvar_hidden_sd,
            self.tagvar_only_sd,
            self.tagvar_sd_ld,
        )
        self.assertEqual(tagvars.display_name('unknown'), 'unknown')

        self.assertEqual(tagvars.display_name('~hidden'), '~hidden')
        self.assertEqual(tagvars.display_name('~hidden:xxx'), '~hidden [xxx]')

        self.assertEqual(tagvars.display_name('~hidden_sd'), 'hidden_sd_shortdesc')
        self.assertEqual(tagvars.display_name('~hidden_sd:xxx'), 'hidden_sd_shortdesc [xxx]')

        self.assertEqual(tagvars.display_name('nodesc'), 'nodesc')
        self.assertEqual(tagvars.display_name('nodesc:'), 'nodesc')
        self.assertEqual(tagvars.display_name('nodesc:xxx'), 'nodesc [xxx]')

        self.assertEqual(tagvars.display_name('only_sd'), 'only_sd_shortdesc')
        self.assertEqual(tagvars.display_name('only_sd:'), 'only_sd_shortdesc')
        self.assertEqual(tagvars.display_name('only_sd:xxx'), 'only_sd_shortdesc [xxx]')

        with mock.patch("picard.util.tags._", return_value='translated'):
            self.assertEqual(tagvars.display_name('only_sd'), 'translated')

    def test_script_variable_tag_names(self):
        tagvars = TagVars(
            self.tagvar_nodesc,
            self.tagvar_hidden,
            self.tagvar_hidden_sd,
            self.tagvar_only_sd,
            self.tagvar_sd_ld,
        )
        self.tagvar_sd_ld.not_script_variable = True

        with mock.patch('picard.util.tags.ALL_TAGS', tagvars):
            self.assertEqual(
                tuple(script_variable_tag_names()),
                ('nodesc', '_hidden', '_hidden_sd', 'only_sd'),
            )

    def test_tagvars_display_tooltip(self):
        tagvars = TagVars(
            self.tagvar_nodesc,
            self.tagvar_only_sd,
            self.tagvar_notes1,
            self.tagvar_notes2,
            self.tagvar_notes3,
        )
        self.assertEqual(tagvars.display_tooltip('unknown'), '<p><em>%unknown%</em></p><p>No description available.</p>')

        self.assertEqual(tagvars.display_tooltip('nodesc'), '<p><em>%nodesc%</em></p><p>nodesc</p>')

        self.assertEqual(tagvars.display_tooltip('only_sd'), '<p><em>%only_sd%</em></p><p>only_sd_shortdesc</p>')

        result = (
            '<p><em>%_notes1%</em></p><p>notes1_ld</p>\n'
            '<p><strong>Notes:</strong> preserved read-only; not for use in scripts; calculated; info from audio file.</p>'
        ) if markdown is not None else (
            '<p><em>%_notes1%</em></p><p>notes1_ld'
            '<br /><br />'
            '**Notes:** preserved read-only; not for use in scripts; calculated; info from audio file.</p>'
        )
        self.assertEqual(tagvars.display_tooltip('_notes1'), result)
        self.assertEqual(tagvars.display_tooltip('~notes1'), result)

        result = (
            '<p><em>%notes2%</em></p><p>notes2_ld</p>\n'
            '<p><strong>Notes:</strong> info from audio file; not provided from MusicBrainz data.</p>'
        ) if markdown is not None else (
            '<p><em>%notes2%</em></p><p>notes2_ld'
            '<br /><br />'
            '**Notes:** info from audio file; not provided from MusicBrainz data.</p>'
        )
        self.assertEqual(tagvars.display_tooltip('notes2'), result)

        result = (
            '<p><em>%notes3%</em></p><p>notes3_ld</p>\n'
            '<p><strong>Notes:</strong> not provided from MusicBrainz data.</p>'
        ) if markdown is not None else (
            '<p><em>%notes3%</em></p><p>notes3_ld'
            '<br /><br />'
            '**Notes:** not provided from MusicBrainz data.</p>'
        )
        self.assertEqual(tagvars.display_tooltip('notes3'), result)


class UtilTagsTest(PicardTestCase):
    def test_display_tag_name(self):
        self.assertEqual('Artist', display_tag_name('artist'))
        self.assertEqual('Lyrics', display_tag_name('lyrics:'))
        self.assertEqual('Comment [Foo]', display_tag_name('comment:Foo'))

    def test_parse_comment_tag(self):
        self.assertEqual(('XXX', 'foo'), parse_comment_tag('comment:XXX:foo'))
        self.assertEqual(('eng', 'foo'), parse_comment_tag('comment:foo'))
        self.assertEqual(('XXX', ''), parse_comment_tag('comment:XXX'))
        self.assertEqual(('eng', ''), parse_comment_tag('comment'))

    def test_parse_lyrics_tag(self):
        self.assertEqual(('eng', ''), parse_subtag('lyrics'))
        self.assertEqual(('XXX', 'foo'), parse_subtag('lyrics:XXX:foo'))
        self.assertEqual(('XXX', ''), parse_subtag('lyrics:XXX'))
        self.assertEqual(('eng', 'foo'), parse_subtag('lyrics::foo'))

    def test_display_tag_tooltip(self):
        self.assertEqual(
            display_tag_tooltip('unknown_test_variable'),
            '<p><em>%unknown_test_variable%</em></p><p>No description available.</p>'
        )

        self.assertEqual(
            display_tag_tooltip('album'),
            '<p><em>%album%</em></p><p>The title of the release.</p>'
        )

        self.assertEqual(
            display_tag_tooltip('_albumartists_sort'),
            "<p><em>%_albumartists_sort%</em></p><p>A multi-value variable containing the sort names of the album's artists.</p>"
        )

        result = (
            '<p><em>%albumsort%</em></p><p>The sort name of the title of the release.</p>\n'
            '<p><strong>Notes:</strong> not provided from MusicBrainz data.</p>'
        ) if markdown is not None else (
            '<p><em>%albumsort%</em></p><p>The sort name of the title of the release.'
            '<br /><br />'
            '**Notes:** not provided from MusicBrainz data.</p>'
        )
        self.assertEqual(display_tag_tooltip('albumsort'), result)

        result = (
            '<p><em>%_bitrate%</em></p><p>Approximate bitrate in kbps.</p>\n'
            '<p><strong>Notes:</strong> preserved read-only; info from audio file; not provided from MusicBrainz data.</p>'
        ) if markdown is not None else (
            '<p><em>%_bitrate%</em></p><p>Approximate bitrate in kbps.'
            '<br /><br />'
            '**Notes:** preserved read-only; info from audio file; not provided from MusicBrainz data.</p>'
        )
        self.assertEqual(display_tag_tooltip('_bitrate'), result)
        self.assertEqual(display_tag_tooltip('~bitrate'), result)
