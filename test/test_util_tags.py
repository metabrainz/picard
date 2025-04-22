# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2020 Philipp Wolfer
# Copyright (C) 2020-2022 Laurent Monin
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 Serial
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
