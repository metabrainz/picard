# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2017 Sophist-UK
# Copyright (C) 2018 Wieland Hoffmann
# Copyright (C) 2018-2020 Laurent Monin
# Copyright (C) 2018-2020 Philipp Wolfer
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


from test.picardtestcase import (
    PicardTestCase,
    create_fake_png,
    load_test_json,
)
from test.test_coverart_image import create_image

from picard import config
from picard.cluster import Cluster
from picard.coverart.image import CoverArtImage
from picard.file import File
from picard.mbjson import (
    release_to_metadata,
    track_to_metadata,
)
from picard.metadata import (
    MULTI_VALUED_JOINER,
    Metadata,
    MultiMetadataProxy,
    weights_from_preferred_countries,
    weights_from_preferred_formats,
    weights_from_release_type_scores,
)
from picard.track import Track
from picard.util.imagelist import ImageList
from picard.util.tags import PRESERVED_TAGS


settings = {
    'write_id3v23': False,
    'id3v23_join_with': '/',
    'preferred_release_countries': [],
    'preferred_release_formats': [],
    'standardize_artists': False,
    'standardize_instruments': False,
    'translate_artist_names': False,
    'release_ars': True,
    'release_type_scores': [
        ('Album', 1.0)
    ],
}


class CommonTests:

    class CommonMetadataTestCase(PicardTestCase):

        original = None
        tags = []

        def setUp(self):
            super().setUp()
            config.setting = settings.copy()
            self.metadata = self.get_metadata_object()
            self.metadata.length = 242
            self.metadata["single1"] = "single1-value"
            self.metadata.add_unique("single2", "single2-value")
            self.metadata.add_unique("single2", "single2-value")
            self.multi1 = ["multi1-value1", "multi1-value1"]
            self.metadata.add("multi1", self.multi1[0])
            self.metadata.add("multi1", self.multi1[1])
            self.multi2 = ["multi2-value1", "multi2-value2"]
            self.metadata["multi2"] = self.multi2
            self.multi3 = ["multi3-value1", "multi3-value2"]
            self.metadata.set("multi3", self.multi3)
            self.metadata["~hidden"] = "hidden-value"

            self.metadata_d1 = Metadata({'a': 'b', 'c': 2, 'd': ['x', 'y'], 'x': ''})
            self.metadata_d2 = Metadata({'a': 'b', 'c': 2, 'd': ['x', 'y'], 'x': 'z'})
            self.metadata_d3 = Metadata({'c': 3, 'd': ['u', 'w'], 'x': 'p'})

        @staticmethod
        def get_metadata_object():
            pass

        def tearDown(self):
            pass

        def test_metadata_setitem(self):
            self.assertEqual(["single1-value"], self.metadata.getraw("single1"))
            self.assertEqual(["single2-value"], self.metadata.getraw("single2"))
            self.assertEqual(self.multi1, self.metadata.getraw("multi1"))
            self.assertEqual(self.multi2, self.metadata.getraw("multi2"))
            self.assertEqual(self.multi3, self.metadata.getraw("multi3"))
            self.assertEqual(["hidden-value"], self.metadata.getraw("~hidden"))

        def test_metadata_set_all_values_as_string(self):
            for val in (0, 2, True):
                str_val = str(val)
                self.metadata.set('val1', val)
                self.assertEqual([str_val], self.metadata.getraw("val1"))
                self.metadata['val2'] = val
                self.assertEqual([str_val], self.metadata.getraw("val2"))
                del self.metadata['val3']
                self.metadata.add('val3', val)
                self.assertEqual([str_val], self.metadata.getraw("val3"))
                del self.metadata['val4']
                self.metadata.add_unique('val4', val)
                self.assertEqual([str_val], self.metadata.getraw("val4"))

        def test_metadata_get(self):
            self.assertEqual("single1-value", self.metadata["single1"])
            self.assertEqual("single1-value", self.metadata.get("single1"))
            self.assertEqual(["single1-value"], self.metadata.getall("single1"))
            self.assertEqual(["single1-value"], self.metadata.getraw("single1"))

            self.assertEqual(MULTI_VALUED_JOINER.join(self.multi1), self.metadata["multi1"])
            self.assertEqual(MULTI_VALUED_JOINER.join(self.multi1), self.metadata.get("multi1"))
            self.assertEqual(self.multi1, self.metadata.getall("multi1"))
            self.assertEqual(self.multi1, self.metadata.getraw("multi1"))

            self.assertEqual("", self.metadata["nonexistent"])
            self.assertEqual(None, self.metadata.get("nonexistent"))
            self.assertEqual([], self.metadata.getall("nonexistent"))
            self.assertRaises(KeyError, self.metadata.getraw, "nonexistent")

            self.assertEqual(self.metadata._store.items(), self.metadata.rawitems())
            metadata_items = [(x, z) for (x, y) in self.metadata.rawitems() for z in y]
            self.assertEqual(metadata_items, list(self.metadata.items()))

        def test_metadata_unset(self):
            self.metadata.unset("single1")
            self.assertNotIn("single1", self.metadata)
            self.assertNotIn("single1", self.metadata.deleted_tags)
            self.metadata.unset('unknown_tag')

        def test_metadata_pop(self):
            self.metadata.pop("single1")
            self.assertNotIn("single1", self.metadata)
            self.assertIn("single1", self.metadata.deleted_tags)
            self.metadata.pop('unknown_tag')

        def test_metadata_delete(self):
            del self.metadata["single1"]
            self.assertNotIn("single1", self.metadata)
            self.assertIn("single1", self.metadata.deleted_tags)

        def test_metadata_legacy_delete(self):
            self.metadata.delete("single1")
            self.assertNotIn("single1", self.metadata)
            self.assertIn("single1", self.metadata.deleted_tags)

        def test_metadata_implicit_delete(self):
            self.metadata["single2"] = ""
            self.assertNotIn("single2", self.metadata)
            self.assertIn("single2", self.metadata.deleted_tags)

            self.metadata["unknown"] = ""
            self.assertNotIn("unknown", self.metadata)
            self.assertNotIn("unknown", self.metadata.deleted_tags)

        def test_metadata_undelete(self):
            self.metadata.delete("single1")
            self.assertNotIn("single1", self.metadata)
            self.assertIn("single1", self.metadata.deleted_tags)

            self.metadata["single1"] = "value1"
            self.assertIn("single1", self.metadata)
            self.assertNotIn("single1", self.metadata.deleted_tags)

        def test_normalize_tag(self):
            self.assertEqual('sometag', Metadata.normalize_tag('sometag'))
            self.assertEqual('sometag', Metadata.normalize_tag('sometag:'))
            self.assertEqual('sometag', Metadata.normalize_tag('sometag::'))
            self.assertEqual('sometag:desc', Metadata.normalize_tag('sometag:desc'))

        def test_metadata_tag_trailing_colon(self):
            self.metadata['tag:'] = 'Foo'
            self.assertIn('tag', self.metadata)
            self.assertIn('tag:', self.metadata)
            self.assertEqual('Foo', self.metadata['tag'])
            self.assertEqual('Foo', self.metadata['tag:'])
            del self.metadata['tag']
            self.assertNotIn('tag', self.metadata)
            self.assertNotIn('tag:', self.metadata)

        def test_metadata_copy(self):
            m = Metadata()
            m["old"] = "old-value"
            self.metadata.delete("single1")
            m.copy(self.metadata)
            self.assertEqual(self.metadata._store, m._store)
            self.assertEqual(self.metadata.deleted_tags, m.deleted_tags)
            self.assertEqual(self.metadata.length, m.length)
            self.assertEqual(self.metadata.images, m.images)

        def test_metadata_copy_without_images(self):
            m = Metadata()
            m.copy(self.metadata, copy_images=False)
            self.assertEqual(self.metadata._store, m._store)
            self.assertEqual(self.metadata.deleted_tags, m.deleted_tags)
            self.assertEqual(self.metadata.length, m.length)
            self.assertEqual(ImageList(), m.images)

        def test_metadata_init_with_existing_metadata(self):
            self.metadata.delete("single1")
            cover = CoverArtImage(url='file://file1', data=create_fake_png(b'a'))
            self.metadata.images.append(cover)
            m = Metadata(self.metadata)
            self.assertEqual(self.metadata.length, m.length)
            self.assertEqual(self.metadata.deleted_tags, m.deleted_tags)
            self.assertEqual(self.metadata.images, m.images)
            self.assertEqual(self.metadata._store, m._store)

        def test_metadata_update(self):
            m = Metadata()
            m["old"] = "old-value"
            self.metadata.delete("single1")
            cover = CoverArtImage(url='file://file1', data=create_fake_png(b'a'))
            self.metadata.images.append(cover)
            m.update(self.metadata)
            self.assertIn("old", m)
            self.assertNotIn("single1", m)
            self.assertIn("single1", m.deleted_tags)
            self.assertEqual("single2-value", m["single2"])
            self.assertEqual(self.metadata.length, m.length)
            self.assertEqual(self.metadata.deleted_tags, m.deleted_tags)
            self.assertEqual(self.metadata.images, m.images)
            self.metadata["old"] = "old-value"
            self.assertEqual(self.metadata._store, m._store)

        def test_metadata_diff(self):
            m1 = Metadata({
                "foo1": "bar1",
                "foo2": "bar2",
                "foo3": "bar3",
            })
            m2 = Metadata(m1)
            m1["foo1"] = "baz"
            del m1["foo2"]
            diff = m1.diff(m2)
            self.assertEqual({"foo1": "baz"}, diff)
            self.assertEqual(set(["foo2"]), diff.deleted_tags)

        def test_metadata_clear(self):
            self.metadata.clear()
            self.assertEqual(0, len(self.metadata))

        def test_metadata_clear_deleted(self):
            self.metadata.delete("single1")
            self.assertIn("single1", self.metadata.deleted_tags)
            self.metadata.clear_deleted()
            self.assertNotIn("single1", self.metadata.deleted_tags)

        def test_metadata_applyfunc(self):
            def func(x):
                return x[1:]
            self.metadata.apply_func(func)

            self.assertEqual("ingle1-value", self.metadata["single1"])
            self.assertEqual("ingle1-value", self.metadata.get("single1"))
            self.assertEqual(["ingle1-value"], self.metadata.getall("single1"))

            self.assertEqual(MULTI_VALUED_JOINER.join(map(func, self.multi1)), self.metadata["multi1"])
            self.assertEqual(MULTI_VALUED_JOINER.join(map(func, self.multi1)), self.metadata.get("multi1"))
            self.assertEqual(list(map(func, self.multi1)), self.metadata.getall("multi1"))

        def test_metadata_applyfunc_preserve_tags(self):
            self.assertTrue(len(PRESERVED_TAGS) > 0)
            m = Metadata()
            m[PRESERVED_TAGS[0]] = 'value1'
            m['not_preserved'] = 'value2'

            def func(x):
                return x[1:]
            m.apply_func(func)

            self.assertEqual("value1", m[PRESERVED_TAGS[0]])
            self.assertEqual("alue2", m['not_preserved'])

        def test_metadata_applyfunc_delete_tags(self):
            def func(x):
                return None
            metadata = Metadata(self.metadata)
            metadata.apply_func(func)
            self.assertEqual(0, len(metadata.rawitems()))
            self.assertEqual(self.metadata.keys(), metadata.deleted_tags)

        def test_length_score(self):
            results = [(20000, 0, 0.333333333333),
                       (20000, 10000, 0.666666666667),
                       (20000, 20000, 1.0),
                       (20000, 30000, 0.666666666667),
                       (20000, 40000, 0.333333333333),
                       (20000, 50000, 0.0)]
            for (a, b, expected) in results:
                actual = Metadata.length_score(a, b)
                self.assertAlmostEqual(expected, actual,
                                       msg="a={a}, b={b}".format(a=a, b=b))

        def test_compare_is_equal(self):
            m1 = Metadata()
            m1["title"] = "title1"
            m1["tracknumber"] = "2"
            m1.length = 360
            m2 = Metadata()
            m2["title"] = "title1"
            m2["tracknumber"] = "2"
            m2.length = 360
            self.assertEqual(m1.compare(m2), m2.compare(m1))
            self.assertEqual(m1.compare(m2), 1)

        def test_compare_with_ignored(self):
            m1 = Metadata()
            m1["title"] = "title1"
            m1["tracknumber"] = "2"
            m1.length = 360
            m2 = Metadata()
            m2["title"] = "title1"
            m2["tracknumber"] = "3"
            m2.length = 300
            self.assertNotEqual(m1.compare(m2), 1)
            self.assertEqual(m1.compare(m2, ignored=['tracknumber', '~length']), 1)

        def test_compare_lengths(self):
            m1 = Metadata()
            m1.length = 360
            m2 = Metadata()
            m2.length = 300
            self.assertAlmostEqual(m1.compare(m2), 0.998)

        def test_compare_tracknumber_difference(self):
            m1 = Metadata()
            m1["tracknumber"] = "1"
            m2 = Metadata()
            m2["tracknumber"] = "2"
            m3 = Metadata()
            m3["tracknumber"] = "2"
            self.assertEqual(m1.compare(m2), 0)
            self.assertEqual(m2.compare(m3), 1)

        def test_compare_discnumber_difference(self):
            m1 = Metadata()
            m1["discnumber"] = "1"
            m2 = Metadata()
            m2["discnumber"] = "2"
            m3 = Metadata()
            m3["discnumber"] = "2"
            self.assertEqual(m1.compare(m2), 0)
            self.assertEqual(m2.compare(m3), 1)

        def test_compare_deleted(self):
            m1 = Metadata()
            m1["artist"] = "TheArtist"
            m1["title"] = "title1"
            m2 = Metadata()
            m2["artist"] = "TheArtist"
            m2.delete("title")
            self.assertTrue(m1.compare(m2) < 1)

        def test_strip_whitespace(self):
            m1 = Metadata()
            m1["artist"] = "  TheArtist  "
            m1["title"] = "\t\u00A0  tit le1 \r\n"
            m1["genre"] = " \t"
            m1.strip_whitespace()
            self.assertEqual(m1["artist"], "TheArtist")
            self.assertEqual(m1["title"], "tit le1")

        def test_metadata_mapping_init(self):
            d = {'a': 'b', 'c': 2, 'd': ['x', 'y'], 'x': '', 'z': {'u', 'w'}}
            deleted_tags = set('c')
            m = Metadata(d, deleted_tags=deleted_tags, length=1234)
            self.assertIn('a', m)
            self.assertEqual(m.getraw('a'), ['b'])
            self.assertEqual(m['d'], MULTI_VALUED_JOINER.join(d['d']))
            self.assertNotIn('c', m)
            self.assertNotIn('length', m)
            self.assertIn('c', m.deleted_tags)
            self.assertEqual(m.length, 1234)

        def test_metadata_mapping_init_zero(self):
            m = Metadata(tag1='a', tag2=0, tag3='', tag4=None)
            m['tag5'] = 0
            m['tag1'] = ''
            self.assertIn('tag1', m.deleted_tags)
            self.assertEqual(m['tag2'], '0')
            self.assertNotIn('tag3', m)
            self.assertNotIn('tag4', m)
            self.assertEqual(m['tag5'], '0')

        def test_metadata_mapping_del(self):
            m = self.metadata_d1
            self.assertEqual(m.getraw('a'), ['b'])
            self.assertNotIn('a', m.deleted_tags)

            self.assertNotIn('x', m.deleted_tags)
            self.assertRaises(KeyError, m.getraw, 'x')

            del m['a']
            self.assertRaises(KeyError, m.getraw, 'a')
            self.assertIn('a', m.deleted_tags)

            # NOTE: historic behavior of Metadata.delete()
            # an attempt to delete an non-existing tag, will add it to the list
            # of deleted tags
            # so this will not raise a KeyError
            # as is it differs from dict or even defaultdict behavior
            del m['unknown']
            self.assertIn('unknown', m.deleted_tags)

        def test_metadata_mapping_iter(self):
            self.assertEqual(set(self.metadata_d1), {'a', 'c', 'd'})

        def test_metadata_mapping_keys(self):
            self.assertEqual(set(self.metadata_d1.keys()), {'a', 'c', 'd'})

        def test_metadata_mapping_values(self):
            self.assertEqual(set(self.metadata_d1.values()), {'b', '2', 'x; y'})

        def test_metadata_mapping_len(self):
            m = self.metadata_d1
            self.assertEqual(len(m), 3)
            del m['x']
            self.assertEqual(len(m), 3)
            del m['c']
            self.assertEqual(len(m), 2)

        def _check_mapping_update(self, m):
            self.assertEqual(m['a'], 'b')
            self.assertEqual(m['c'], '3')
            self.assertEqual(m.getraw('d'), ['u', 'w'])
            self.assertEqual(m['x'], '')
            self.assertIn('x', m.deleted_tags)

        def test_metadata_mapping_update(self):
            # update from Metadata
            m = self.metadata_d2
            m2 = self.metadata_d3

            del m2['x']
            m.update(m2)
            self._check_mapping_update(m)

        def test_metadata_mapping_update_dict(self):
            # update from dict
            m = self.metadata_d2

            d2 = {'c': 3, 'd': ['u', 'w'], 'x': ''}

            m.update(d2)
            self._check_mapping_update(m)

        def test_metadata_mapping_update_tuple(self):
            # update from tuple
            m = self.metadata_d2

            d2 = (('c', 3), ('d', ['u', 'w']), ('x', ''))

            m.update(d2)
            self._check_mapping_update(m)

        def test_metadata_mapping_update_dictlike(self):
            # update from kwargs
            m = self.metadata_d2

            m.update(c=3, d=['u', 'w'], x='')
            self._check_mapping_update(m)

        def test_metadata_mapping_update_noparam(self):
            # update without parameter
            m = self.metadata_d2

            self.assertRaises(TypeError, m.update)
            self.assertEqual(m['a'], 'b')

        def test_metadata_mapping_update_intparam(self):
            # update without parameter
            m = self.metadata_d2

            self.assertRaises(TypeError, m.update, 123)

        def test_metadata_mapping_update_strparam(self):
            # update without parameter
            m = self.metadata_d2

            self.assertRaises(ValueError, m.update, 'abc')

        def test_metadata_mapping_update_kw(self):
            m = Metadata(tag1='a', tag2='b')
            m.update(tag1='c')
            self.assertEqual(m['tag1'], 'c')
            self.assertEqual(m['tag2'], 'b')
            m.update(tag2='')
            self.assertIn('tag2', m.deleted_tags)

        def test_metadata_mapping_update_kw_del(self):
            m = Metadata(tag1='a', tag2='b')
            del m['tag1']

            m2 = Metadata(tag1='c', tag2='d')
            del m2['tag2']

            m.update(m2)
            self.assertEqual(m['tag1'], 'c')
            self.assertNotIn('tag2', m)
            self.assertNotIn('tag1', m.deleted_tags)
            self.assertIn('tag2', m.deleted_tags)

        def test_metadata_mapping_images(self):
            image1 = create_image(b'A', comment='A')
            image2 = create_image(b'B', comment='B')

            m1 = Metadata(a='b', length=1234, images=[image1])
            self.assertEqual(m1.images[0], image1)
            self.assertEqual(len(m1), 2)  # one tag, one image

            m1.images.append(image2)
            self.assertEqual(m1.images[1], image2)

            m1.images.pop(0)
            self.assertEqual(m1.images[0], image2)

            m2 = Metadata(a='c', length=4567, images=[image1])
            m1.update(m2)
            self.assertEqual(m1.images[0], image1)

            m1.images.pop(0)
            self.assertEqual(len(m1), 1)  # one tag, zero image
            self.assertFalse(m1.images)

        def test_metadata_mapping_iterable(self):
            m = Metadata(tag_tuple=('a', 0))
            m['tag_set'] = {'c', 'd'}
            m['tag_dict'] = {'e': 1, 'f': 2}
            m['tag_str'] = 'gh'
            self.assertIn('0', m.getraw('tag_tuple'))
            self.assertIn('c', m.getraw('tag_set'))
            self.assertIn('e', m.getraw('tag_dict'))
            self.assertIn('gh', m.getraw('tag_str'))

        def test_compare_to_release(self):
            release = load_test_json('release.json')
            metadata = Metadata()
            release_to_metadata(release, metadata)
            match = metadata.compare_to_release(release, Cluster.comparison_weights)
            self.assertEqual(1.0, match.similarity)
            self.assertEqual(release, match.release)

        def test_compare_to_release_with_score(self):
            release = load_test_json('release.json')
            metadata = Metadata()
            release_to_metadata(release, metadata)
            for score, sim in ((42, 0.42), ('42', 0.42), ('foo', 1.0), (None, 1.0)):
                release['score'] = score
                match = metadata.compare_to_release(release, Cluster.comparison_weights)
                self.assertEqual(sim, match.similarity)

        def test_weights_from_release_type_scores(self):
            release = load_test_json('release.json')
            parts = []
            weights_from_release_type_scores(parts, release, {'Album': 0.75}, 666)
            self.assertEqual(
                parts[0],
                (0.75, 666)
            )
            weights_from_release_type_scores(parts, release, {}, 666)
            self.assertEqual(
                parts[1],
                (0.5, 666)
            )
            del release['release-group']
            weights_from_release_type_scores(parts, release, {}, 777)
            self.assertEqual(
                parts[2],
                (0.0, 777)
            )

        def test_preferred_countries(self):
            release = load_test_json('release.json')
            parts = []
            weights_from_preferred_countries(parts, release, [], 666)
            self.assertFalse(parts)
            weights_from_preferred_countries(parts, release, ['FR'], 666)
            self.assertEqual(parts[0], (0.0, 666))
            weights_from_preferred_countries(parts, release, ['GB'], 666)
            self.assertEqual(parts[1], (1.0, 666))

        def test_preferred_formats(self):
            release = load_test_json('release.json')
            parts = []
            weights_from_preferred_formats(parts, release, [], 777)
            self.assertFalse(parts)
            weights_from_preferred_formats(parts, release, ['Digital Media'], 777)
            self.assertEqual(parts[0], (0.0, 777))
            weights_from_preferred_formats(parts, release, ['12" Vinyl'], 777)
            self.assertEqual(parts[1], (1.0, 777))

        def test_compare_to_track(self):
            track_json = load_test_json('track.json')
            track = Track(track_json['id'])
            track_to_metadata(track_json, track)
            match = track.metadata.compare_to_track(track_json, File.comparison_weights)
            self.assertEqual(1.0, match.similarity)
            self.assertEqual(track_json, match.track)

        def test_compare_to_track_with_score(self):
            track_json = load_test_json('track.json')
            track = Track(track_json['id'])
            track_to_metadata(track_json, track)
            for score, sim in ((42, 0.42), ('42', 0.42), ('foo', 1.0), (None, 1.0)):
                track_json['score'] = score
                match = track.metadata.compare_to_track(track_json, File.comparison_weights)
                self.assertEqual(sim, match.similarity)


class MetadataTest(CommonTests.CommonMetadataTestCase):
    @staticmethod
    def get_metadata_object():
        return Metadata()


class MultiMetadataProxyAsMetadataTest(CommonTests.CommonMetadataTestCase):
    @staticmethod
    def get_metadata_object():
        return MultiMetadataProxy(Metadata())


class MultiMetadataProxyTest(PicardTestCase):

    def setUp(self):
        super().setUp()
        self.m1 = Metadata({
            "key1": "m1.val1",
            "key2": "m1.val2",
        })
        self.m2 = Metadata({
            "key2": "m2.val2",
            "key3": "m2.val3",
        })
        self.m3 = Metadata({
            "key2": "m3.val2",
            "key4": "m3.val4",
        })

    def test_get_attribute(self):
        mp = MultiMetadataProxy(self.m1, self.m2, self.m3)
        self.assertEqual(mp.deleted_tags, self.m1.deleted_tags)

    def test_gettitem(self):
        mp = MultiMetadataProxy(self.m1, self.m2, self.m3)
        self.assertEqual("m1.val1", mp["key1"])
        self.assertEqual("m1.val2", mp["key2"])
        self.assertEqual("m2.val3", mp["key3"])
        self.assertEqual("m3.val4", mp["key4"])

    def test_settitem(self):
        orig_m2 = Metadata(self.m2)
        mp = MultiMetadataProxy(self.m1, self.m2, self.m3)
        mp["key1"] = "foo1"
        mp["key2"] = "foo2"
        mp["key3"] = "foo3"
        mp["key4"] = "foo4"
        mp["key5"] = "foo5"
        self.assertEqual("foo1", self.m1["key1"])
        self.assertEqual("foo2", self.m1["key2"])
        self.assertEqual("foo3", self.m1["key3"])
        self.assertEqual("foo4", self.m1["key4"])
        self.assertEqual("foo5", self.m1["key5"])
        self.assertEqual(orig_m2, self.m2)

    def test_delitem(self):
        orig_m2 = Metadata(self.m2)
        mp = MultiMetadataProxy(self.m1, self.m2, self.m3)
        del mp["key2"]
        del mp["key3"]
        self.assertIn("key2", self.m1.deleted_tags)
        self.assertIn("key3", self.m1.deleted_tags)
        self.assertEqual(orig_m2, self.m2)
