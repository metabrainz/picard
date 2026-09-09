# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2020, 2025-2026 Philipp Wolfer
# Copyright (C) 2020-2022, 2025 Laurent Monin
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from test.picardtestcase import PicardTestCase

from picard.const.tags import ALL_TAGS
from picard.options import get_option_title
from picard.tags import (
    create_lang_desc_tag,
    display_tag_name,
    filterable_tag_names,
    parse_lang_desc_tag,
    preserved_tag_names,
    tag_names,
)


class UtilTagsTest(PicardTestCase):
    def test_display_tag_name(self):
        # Tag with no extra parts and no description
        self.assertEqual(display_tag_name('tag'), 'tag')

        # Tag with one extra part and no description
        self.assertEqual(display_tag_name('tag:desc'), 'tag [desc]')

        # Tag with blank extra part and no description
        self.assertEqual(display_tag_name('tag:'), 'tag')

        # Tag with multiple extra parts and no description
        self.assertEqual(display_tag_name('tag:de:sc'), 'tag [de:sc]')

        # Tag with no extra parts and short description
        self.assertEqual(display_tag_name('originalyear'), 'Original Year')

        # Tag with one extra part and short description
        self.assertEqual(display_tag_name('originalyear:desc'), 'Original Year [desc]')

        # Hidden tag with no extra parts and short description
        self.assertEqual(display_tag_name('~length'), 'Length')

        # Invalid hidden tag (not in ALL_TAGS)
        self.assertEqual(display_tag_name('~lengthx'), '~lengthx')

        # Empty tag
        self.assertEqual(display_tag_name(''), '')

    def test_parse_lang_desc_tag(self):
        self.assertEqual(parse_lang_desc_tag('lyrics:eng'), ('eng', ''))
        self.assertEqual(parse_lang_desc_tag('lyrics:XXX:foo'), ('XXX', 'foo'))
        self.assertEqual(parse_lang_desc_tag('lyrics:XXX'), ('XXX', ''))
        self.assertEqual(parse_lang_desc_tag('lyrics::foo', default_language='eng'), ('eng', 'foo'))

    def test_parse_lang_desc_tag_invalid_language(self):
        self.assertEqual(parse_lang_desc_tag('lyrics:de', default_language='eng'), ('eng', 'de'))
        self.assertEqual(parse_lang_desc_tag('lyrics:toolong:foo', default_language='eng'), ('eng', 'toolong:foo'))

    def test_parse_lang_desc_tag_description_with_colon(self):
        # The description may itself contain colons and must be preserved in full.
        self.assertEqual(parse_lang_desc_tag('lyrics:eng:a:b'), ('eng', 'a:b'))
        self.assertEqual(parse_lang_desc_tag('lyrics::a:b', default_language='eng'), ('eng', 'a:b'))
        self.assertEqual(parse_lang_desc_tag('comment:deu:foo:bar:baz'), ('deu', 'foo:bar:baz'))

    def test_create_lang_desc_tag(self):
        self.assertEqual('comment', create_lang_desc_tag('comment'))
        self.assertEqual('comment:eng', create_lang_desc_tag('comment', language='eng'))
        self.assertEqual('comment::foo', create_lang_desc_tag('comment', description='foo'))
        self.assertEqual('lyrics:jpn:foo', create_lang_desc_tag('lyrics', language='jpn', description='foo'))
        self.assertEqual(
            'lyrics::foo', create_lang_desc_tag('lyrics', language='jpn', description='foo', default_language='jpn')
        )


class UtilTagsOptionsTest(PicardTestCase):
    def test_options_exist(self):
        """Ensure all related options actually exist in the option settings registry (Option.registry)
        and have a title set.
        """
        for tv in ALL_TAGS:
            if tv.related_options is None:
                continue
            for opt in tv.related_options:
                with self.subTest(tag=str(tv), option=opt):
                    title = get_option_title(opt)
                    self.assertIsNotNone(title, f"Missing related option setting '{opt}' in '{str(tv)}'")
                    self.assertFalse(
                        title.startswith('No title for setting'),
                        f"Missing title for option setting '{opt}' in '{str(tv)}'",
                    )


class UtilTagsSeeAlsoTest(PicardTestCase):
    def test_see_alsos_exist(self):
        """Ensure all `see_also` tags actually exist in the `ALL_TAGS` collection and that a tag's
        `see_also` tags do not refer to itself.
        """
        for tv in ALL_TAGS:
            if tv.see_also is None:
                continue
            for also in tv.see_also:
                with self.subTest(tag=str(tv), see_also=also):
                    name = ALL_TAGS.script_name_from_name(also)
                    self.assertIsNotNone(name, f"Invalid see_also '{also}' in '{str(tv)}' tag")
                    self.assertNotEqual(name, str(tv), f"Circular see_also reference in '{str(tv)}' tag")


class UtilTagsLinksTest(PicardTestCase):
    def test_links_completeness(self):
        """Ensure all `doc_links` entries have both a title and a link."""
        for tv in ALL_TAGS:
            if tv.doc_links is None:
                continue
            for doc_link in tv.doc_links:
                with self.subTest(tag=str(tv), link=doc_link.link):
                    title = doc_link.title.strip()
                    link = doc_link.link.strip()
                    self.assertNotEqual(title, '', f"Invalid link (missing title) in '{str(tv)}' tag")
                    self.assertNotEqual(link, '', f"Invalid link (missing URL) in '{str(tv)}' tag")


class TagsGeneratorTest(PicardTestCase):
    def test_all_tags(self):
        tags = list(tag_names())
        self.assertTrue(len(tags) > 0)

        for tag in tags:
            with self.subTest(tag=tag):
                self.assertTrue(ALL_TAGS.tagvar_from_name(tag).is_tag)

    def test_all_preserved_tags(self):
        tags = list(preserved_tag_names())
        self.assertTrue(len(tags) > 0)

        for tag in tags:
            with self.subTest(tag=tag):
                self.assertTrue(ALL_TAGS.tagvar_from_name(tag).is_preserved)

    def test_all_filterable_tags(self):
        tags = list(filterable_tag_names())
        # Guard against the loop below passing vacuously, as the sibling tests do
        self.assertTrue(len(tags) > 0)

        for tag in tags:
            with self.subTest(tag=tag):
                self.assertTrue(ALL_TAGS.tagvar_from_name(tag).is_filterable)
