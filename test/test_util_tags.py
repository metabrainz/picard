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

from picard.const import PICARD_URLS
from picard.options import (
    Option,
    get_option_title,
)
from picard.profile import profile_groups_add_setting
from picard.util.tags import (
    ALL_TAGS,
    DocumentLink,
    TagVar,
    TagVars,
    display_tag_full_description,
    display_tag_name,
    display_tag_tooltip,
    markdown,
    parse_comment_tag,
    parse_subtag,
    script_variable_tag_names,
)


class TagVarTest(PicardTestCase):
    def test_basic_properties(self):
        tv = TagVar('name')

        # native properties
        self.assertEqual(tv._name, 'name')
        self.assertIsNone(tv._shortdesc)
        self.assertIsNone(tv._longdesc)
        self.assertIsNone(tv._additionaldesc)
        self.assertFalse(tv.is_preserved)
        self.assertFalse(tv.is_hidden)
        self.assertTrue(tv.is_script_variable)
        self.assertTrue(tv.is_tag)
        self.assertFalse(tv.is_calculated)
        self.assertFalse(tv.is_file_info)
        self.assertTrue(tv.is_from_mb)
        self.assertTrue(tv.is_populated_by_picard)
        self.assertFalse(tv.is_multi_value)
        self.assertIsNone(tv.see_also)
        self.assertIsNone(tv.related_options)
        self.assertIsNone(tv.doc_links)

        # derived properties
        self.assertEqual(tv.shortdesc, 'name')
        self.assertEqual(tv.longdesc, 'name')
        self.assertEqual(tv.additionaldesc, '')

        self.assertFalse(tv.not_from_mb)
        self.assertFalse(tv.not_script_variable)
        self.assertFalse(tv.not_populated_by_picard)

        # basic methods
        self.assertEqual(tv.script_name(), 'name')
        self.assertEqual(str(tv), 'name')

    def test_basic_hidden_script_name(self):
        tv = TagVar('name', is_hidden=True)
        self.assertEqual(tv.script_name(), '_name')

    def test_basic_notes(self):
        see_also = ('a', 'b',)
        related_options = ('o1', 'o2',)
        doc_links = (
            DocumentLink('L1', 'U1'),
            DocumentLink('L2', 'U2'),
        )

        tv = TagVar(
            'name',
            see_also=see_also,
            related_options=related_options,
            doc_links=doc_links,
        )

        self.assertEqual(tv.see_also, see_also)
        self.assertEqual(tv.related_options, related_options)
        self.assertEqual(tv.doc_links, doc_links)


class TagVarsTest(PicardTestCase):

    def setUp(self):
        self.old_registry = dict(Option.registry)
        self.tagvar_only_sd = TagVar('only_sd', shortdesc='only_sd_shortdesc')
        self.tagvar_sd_ld = TagVar('sd_ld', shortdesc='sd_ld_shortdesc', longdesc='sd_ld_longdesc')
        self.tagvar_hidden = TagVar('hidden', is_hidden=True)
        self.tagvar_hidden_sd = TagVar('hidden_sd', is_hidden=True, shortdesc='hidden_sd_shortdesc')
        self.tagvar_notag = TagVar('notag', is_tag=False)
        self.tagvar_nodesc = TagVar('nodesc')
        self.tagvar_notes1 = TagVar('notes1', shortdesc='notes1_sd', longdesc='notes1_ld', is_preserved=True, is_calculated=True,
                                   is_file_info=True, is_hidden=True, is_script_variable=False)
        self.tagvar_notes2 = TagVar('notes2', shortdesc='notes2_sd', longdesc='notes2_ld', is_file_info=True, is_from_mb=False)
        self.tagvar_notes3 = TagVar('notes3', shortdesc='notes3_sd', longdesc='notes3_ld', is_from_mb=False)
        self.tagvar_everything = TagVar('everything', shortdesc='everything sd', longdesc='everything ld.',
                                        additionaldesc='Test additional description.', is_preserved=True,
                                        is_script_variable=False, is_tag=False, is_calculated=True, is_file_info=True, is_from_mb=False,
                                        is_populated_by_picard=False, is_multi_value=True,
                                        see_also=('artist', 'title'),
                                        related_options=('everything_test', 'not_a_valid_option_setting'),
                                        doc_links=(DocumentLink('Test link', PICARD_URLS['mb_doc'] + 'test'),))
        if ('setting', 'everything_test') not in Option.registry:
            Option('setting', 'everything_test', None, title='Everything test setting')

    def tearDown(self):
        Option.registry = self.old_registry

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
        self.tagvar_sd_ld.is_script_variable = False

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
            '<p><em>%_notes1%</em></p><p>notes1_ld</p>'
            '<p><strong>Notes:</strong> preserved read-only; not for use in scripts; calculated; info from audio file.</p>'
        )
        self.assertEqual(tagvars.display_tooltip('_notes1'), result)
        self.assertEqual(tagvars.display_tooltip('~notes1'), result)

        result = (
            '<p><em>%notes2%</em></p><p>notes2_ld</p>'
            '<p><strong>Notes:</strong> info from audio file; not provided from MusicBrainz data.</p>'
        )
        self.assertEqual(tagvars.display_tooltip('notes2'), result)

        result = (
            '<p><em>%notes3%</em></p><p>notes3_ld</p>'
            '<p><strong>Notes:</strong> not provided from MusicBrainz data.</p>'
        )
        self.assertEqual(tagvars.display_tooltip('notes3'), result)

    def test_tagvars_full_description(self):
        tagvars = TagVars(
            self.tagvar_everything,
        )
        profile_groups_add_setting('junk', 'everything_test', None, 'Everything test option setting')
        result = (
            '<p><em>%everything%</em></p><p>everything ld.</p>'
            '<p>Test additional description.</p>'
            '<p><strong>Notes:</strong> multi-value variable; preserved read-only; not for use in scripts; '
            'calculated; info from audio file; not provided from MusicBrainz data; not populated by stock '
            'Picard.</p>'
            '<p><strong>Option Settings:</strong> Everything test setting.</p>'
            "<p><strong>Links:</strong> <a href='https://musicbrainz.org/doc/test'>Test link</a>.</p>"
            '<p><strong>See Also:</strong> %artist%; %title%.</p>'
        )
        self.assertEqual(tagvars.display_full_description('everything'), result)


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
            "<p><em>%_albumartists_sort%</em></p><p>The sort names of the album's artists.</p><p><strong>Notes:</strong> multi-value variable.</p>"
        )

        result = (
            '<p><em>%albumsort%</em></p><p>The sort name of the title of the release.</p>'
            '<p><strong>Notes:</strong> not provided from MusicBrainz data.</p>'
        )
        self.assertEqual(display_tag_tooltip('albumsort'), result)

        result = (
            '<p><em>%_bitrate%</em></p><p>Approximate bitrate in kbps.</p>'
            '<p><strong>Notes:</strong> preserved read-only; info from audio file; not provided from MusicBrainz data.</p>'
        )
        self.assertEqual(display_tag_tooltip('_bitrate'), result)
        self.assertEqual(display_tag_tooltip('~bitrate'), result)

        result = (
            '<p><em>%performer%</em></p><p>The names of the performers for the specified type. These types include:</p>\n'
            '<ul>\n'
            '<li>vocals or instruments for the associated release or recording, where "type" can be "<em>vocal</em>", '
            '"<em>guest guitar</em>", "<em>solo violin</em>", etc.</li>\n'
            '<li>the orchestra for the associated release or recording, where "type" is "<em>orchestra</em>"</li>\n'
            '<li>the concert master for the associated release or recording, where "type" is "<em>concertmaster</em>"</li>\n'
            '</ul><p><strong>Notes:</strong> multi-value variable.</p>'
        ) if markdown is not None else (
            '<p><em>%performer%</em></p><p>The names of the performers for the specified type. These types include:'
            '<br /><br />'
            '- vocals or instruments for the associated release or recording, where "type" can be "*vocal*", "*guest guitar*", "*solo violin*", etc.<br />'
            '- the orchestra for the associated release or recording, where "type" is "*orchestra*"<br />'
            '- the concert master for the associated release or recording, where "type" is "*concertmaster*"</p>'
            '<p><strong>Notes:</strong> multi-value variable.</p>'
        )
        self.assertEqual(display_tag_tooltip('performer'), result)

    def test_display_tag_full_description(self):
        if ('setting', 'use_genres') not in Option.registry:
            Option('setting', 'use_genres', None, title='Use genres from MusicBrainz')
        result = (
            '<p><em>%genre%</em></p><p>The specified genre information from MusicBrainz.</p><p><strong>Notes:</strong> multi-value '
            'variable.</p><p><strong>Option Settings:</strong> Use genres from MusicBrainz.</p>'
        )
        self.assertEqual(display_tag_full_description('genre'), result)

        result = (
            '<p><em>%barcode%</em></p><p>The barcode assigned to the release.</p>'
            "<p><strong>Links:</strong> <a href='https://musicbrainz.org/doc/Barcode'>Barcode in MusicBrainz documentation</a>; "
            "<a href='https://picard-docs.musicbrainz.org/en/appendices/tag_mapping.html#id6'>Barcode mapping in Picard documentation</a>.</p>"
        )
        self.assertEqual(display_tag_full_description('barcode'), result)

        result = (
            '<p><em>%_sample_rate%</em></p><p>The sample rate of the audio file.</p>'
            '<p><strong>Notes:</strong> preserved read-only; info from audio file; not provided from MusicBrainz data.</p>'
        )
        self.assertEqual(display_tag_full_description('_sample_rate'), result)

        result = (
            '<p><em>%performer%</em></p><p>The names of the performers for the specified type. These types include:</p>\n'
            '<ul>\n'
            '<li>vocals or instruments for the associated release or recording, where "type" can be "<em>vocal</em>", '
            '"<em>guest guitar</em>", "<em>solo violin</em>", etc.</li>\n'
            '<li>the orchestra for the associated release or recording, where "type" is "<em>orchestra</em>"</li>\n'
            '<li>the concert master for the associated release or recording, where "type" is "<em>concertmaster</em>"</li>\n'
            '</ul>'
            '<p><strong>Notes:</strong> multi-value variable.</p>'
        ) if markdown is not None else (
            '<p><em>%performer%</em></p><p>The names of the performers for the specified type. These types include:'
            '<br /><br />'
            '- vocals or instruments for the associated release or recording, where "type" can be "*vocal*", "*guest guitar*", "*solo violin*", etc.<br />'
            '- the orchestra for the associated release or recording, where "type" is "*orchestra*"<br />'
            '- the concert master for the associated release or recording, where "type" is "*concertmaster*"</p>'
            '<p><strong>Notes:</strong> multi-value variable.</p>'
        )
        self.assertEqual(display_tag_full_description('performer'), result)


class UtilTagsOptionsTest(PicardTestCase):
    def test_options_exist(self):
        """Ensure all related options actually exist in the option settings registry (Option.registry)
        and have a title set.
        """
        for tv in ALL_TAGS:
            if tv.related_options is None:
                continue
            for opt in tv.related_options:
                title = get_option_title(opt)
                self.assertIsNotNone(title, f"Missing related option setting '{opt}'")
            self.assertFalse(title.startswith('No title for setting'), f"Missing title for option setting '{opt}'")
