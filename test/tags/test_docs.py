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

from picard.options import Option
from picard.tags import tagvar
from picard.tags.docs import (
    display_tag_full_description,
    display_tag_tooltip,
)
from picard.tags.tagvar import (
    DocumentLink,
    TagVar,
)


class UtilTagsDocsTest(PicardTestCase):
    def test_display_tag_tooltip(self):
        # Unknown tag
        self.assertEqual(
            display_tag_tooltip('unknown_test_variable'),
            '<p><em>%unknown_test_variable%</em></p><p>No description available.</p>',
        )

        # Normal tag without notes.
        self.assertEqual(display_tag_tooltip('album'), '<p><em>%album%</em></p><p>The title of the release.</p>')

        # Normal tag without notes.
        self.assertEqual(
            display_tag_tooltip('_albumartists_sort'),
            (
                '<p><em>%_albumartists_sort%</em></p><p>The sort names of the album&#x27;s artists.</p><p><strong>Notes:'
                '</strong> multi-value variable.</p>'
            ),
        )

        # Normal tag with notes.
        result = (
            '<p><em>%albumsort%</em></p><p>The sort name of the title of the release.</p>'
            '<p><strong>Notes:</strong> not provided from MusicBrainz data.</p>'
        )
        self.assertEqual(display_tag_tooltip('albumsort'), result)

        # Hidden tag with notes, testing both prefixes '~' and '_'.
        result = (
            '<p><em>%_bitrate%</em></p><p>Approximate bitrate in kbps.</p>'
            '<p><strong>Notes:</strong> read-only; preserved; info from audio file; not provided from MusicBrainz data.</p>'
        )
        self.assertEqual(display_tag_tooltip('_bitrate'), result)
        self.assertEqual(display_tag_tooltip('~bitrate'), result)

        result = (
            (
                '<p><em>%performer%</em></p><p>The names of the performers for the specified type. These types include:</p>\n'
                '<ul>\n'
                '<li>vocals or instruments for the associated release or recording, where &quot;type&quot; can be &quot;<em>vocal</em>&quot;, '
                '&quot;<em>guest guitar</em>&quot;, &quot;<em>solo violin</em>&quot;, etc.</li>\n'
                '<li>the orchestra for the associated release or recording, where &quot;type&quot; is &quot;<em>orchestra</em>&quot;</li>\n'
                '<li>the concert master for the associated release or recording, where &quot;type&quot; is &quot;<em>concertmaster</em>&quot;</li>\n'
                '</ul><p><strong>Notes:</strong> multi-value variable.</p>'
            )
            if tagvar.Markdown is not None
            else (
                '<p><em>%performer%</em></p><p>The names of the performers for the specified type. These types include:'
                '<br /><br />'
                '- vocals or instruments for the associated release or recording, where &quot;type&quot; can be &quot;*vocal*&quot;, &quot;*guest '
                'guitar*&quot;, &quot;*solo violin*&quot;, etc.<br />'
                '- the orchestra for the associated release or recording, where &quot;type&quot; is &quot;*orchestra*&quot;<br />'
                '- the concert master for the associated release or recording, where &quot;type&quot; is &quot;*concertmaster*&quot;</p>'
                '<p><strong>Notes:</strong> multi-value variable.</p>'
            )
        )
        self.assertEqual(display_tag_tooltip('performer'), result)

    def test_display_tag_full_description(self):
        item = TagVar(name='my_var', longdesc='The tag description.')

        # Tag with description only
        expected = "<p>The tag description.</p>"
        self.assertEqual(display_tag_full_description(item), expected)

        # Multi-value tag with description only
        item.is_multi_value = True
        expected = "<p>The tag description.</p><p><strong>Notes:</strong> multi-value variable.</p>"
        self.assertEqual(display_tag_full_description(item), expected)
        item.is_multi_value = False

        # Tag with option setting only
        Option('setting', 'my_script_var_opt', None, title='Option description')
        item.related_options = ('my_script_var_opt',)
        expected = "<p>The tag description.</p><p><strong>Option Settings:</strong> Option description.</p>"
        self.assertEqual(display_tag_full_description(item), expected)
        item.related_options = None

        # Tag with plugin info
        item.plugin_name = "My Plugin"
        expected = "<p>The tag description.</p><p><strong>Plugin:</strong> My Plugin.</p>"
        self.assertEqual(display_tag_full_description(item), expected)
        item.plugin_name = None

        # Tag with doc links
        item.doc_links = (
            DocumentLink('Link 1', 'https://example.com'),
            DocumentLink('Link 2', 'https://example.com/foo'),
        )
        expected = "<p>The tag description.</p><p><strong>Links:</strong> <a href='https://example.com'>Link 1</a>; <a href='https://example.com/foo'>Link 2</a>.</p>"
        self.assertEqual(display_tag_full_description(item), expected)
        item.doc_links = None

        # Tag with see also references
        item.see_also = ('artist', 'albumartist')
        expected = '<p>The tag description.</p><p><strong>See Also:</strong> <a href="#artist">%artist%</a>; <a href="#albumartist">%albumartist%</a>.</p>'
        self.assertEqual(display_tag_full_description(item), expected)
        item.see_also = None

        # Tag with complex markdown (list items) and notes.
        item.is_hidden = True
        item.is_multi_value = True
        item._longdesc = """Description of **My Var**:

- Foo
- Bar
        """
        result = (
            (
                '<p>Description of <strong>My Var</strong>:</p>\n'
                '<ul>\n'
                '<li>Foo</li>\n'
                '<li>Bar</li>\n'
                '</ul><p><strong>Notes:</strong> multi-value variable.</p>'
            )
            if tagvar.Markdown is not None
            else (
                '<p>Description of **My Var**:<br /><br />'
                '- Foo<br />'
                '- Bar</p>'
                '<p><strong>Notes:</strong> multi-value variable.</p>'
            )
        )
        self.assertEqual(display_tag_full_description(item), result)
        item.is_hidden = False
        item.is_multi_value = False

        # Tag with no description
        item._longdesc = None
        expected = '<p>my_var</p>'
        self.assertEqual(display_tag_full_description(item), expected)


class TagTooltipCachingTest(PicardTestCase):
    def setUp(self):
        super().setUp()
        # Isolate the module-level cache between tests.
        display_tag_tooltip.cache_clear()

    def tearDown(self):
        display_tag_tooltip.cache_clear()
        super().tearDown()

    def test_display_tag_tooltip_is_cached(self):
        # The tooltip for a given tag is deterministic and should be memoized:
        # a second call must return the identical cached object.
        first = display_tag_tooltip('album')
        info_before = display_tag_tooltip.cache_info()
        second = display_tag_tooltip('album')
        info_after = display_tag_tooltip.cache_info()

        self.assertIs(first, second)
        # The second call is a cache hit (hits increased, misses did not).
        self.assertEqual(info_after.hits, info_before.hits + 1)
        self.assertEqual(info_after.misses, info_before.misses)

    def test_distinct_tags_are_cached_separately(self):
        album = display_tag_tooltip('album')
        albumsort = display_tag_tooltip('albumsort')
        self.assertNotEqual(album, albumsort)
        self.assertEqual(display_tag_tooltip.cache_info().currsize, 2)


class MarkdownReuseTest(PicardTestCase):
    def test_markdown_reuses_single_instance(self):
        # _markdown must not build a new Markdown object on every call.
        if tagvar._md_instance is None:
            self.skipTest("markdown library not installed")
        before = tagvar._md_instance
        tagvar._markdown("some **text**")
        tagvar._markdown("other _text_")
        self.assertIs(tagvar._md_instance, before)

    def test_markdown_output_stable_across_calls(self):
        # Reusing the instance (with reset()) must give identical output when
        # rendering the same input repeatedly.
        text = "A **bold** thing with a list:\n\n- one\n- two"
        self.assertEqual(tagvar._markdown(text), tagvar._markdown(text))
