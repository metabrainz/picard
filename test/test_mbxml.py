# -*- coding: utf-8 -*-

import unittest
import picard
from picard import config
from picard.metadata import Metadata
from picard.mbxml import (
    track_to_metadata,
    release_to_metadata,
    artist_credit_from_node
)


settings = {
    "standardize_tracks": False,
    "standardize_artists": False,
    "standardize_releases": False,
    "translate_artist_names": False
}


class XmlNode(object):

    def __init__(self, text=u'', children={}, attribs={}):
        self.text = text
        self.children = children
        self.attribs = attribs

    def __repr__(self):
        return repr(self.__dict__)

    def __getattr__(self, name):
        try:
            return self.children[name]
        except KeyError:
            try:
                return self.attribs[name]
            except KeyError:
                raise
                #raise AttributeError, name


class TrackTest(unittest.TestCase):

    def test_1(self):
        config.setting = settings

        class Track:
            pass

        node = XmlNode(attribs={'id': u'321'}, children={
            'title': [XmlNode(text=u'Foo')],
            'length': [XmlNode(text=u'180000')],
            'position': [XmlNode(text=u'1')],
            'recording': [XmlNode(attribs={'id': u'123'}, children={
                'relation_list': [XmlNode(attribs={'target_type': u'work'}, children={
                    'relation': [XmlNode(attribs={'type': u'performance'}, children={
                        'work': [XmlNode(attribs={'id': u'workid123'}, children={
                            'title': [XmlNode(text=u'Bar')],
                            'language': [XmlNode(text=u'eng')]
                        })]
                    })]
                })]
            })],
            'artist_credit': [XmlNode(children={
                'name_credit': [XmlNode(attribs={'joinphrase': u' & '}, children={
                    'artist': [XmlNode(attribs={'id': u'456'}, children={
                        'name': [XmlNode(text=u'Foo Bar')],
                        'sort_name': [XmlNode(text=u'Bar, Foo')]
                    })]
                }), XmlNode(children={
                    'artist': [XmlNode(attribs={'id': u'789'}, children={
                        'name': [XmlNode(text=u'Baz')],
                        'sort_name': [XmlNode(text=u'Baz')]
                    })]
                })]
            })]
        })
        track = Track()
        m = track.metadata = Metadata()
        track_to_metadata(node, track)
        self.assertEqual(u'123', m['musicbrainz_recordingid'])
        self.assertEqual(u'321', m['musicbrainz_trackid'])
        self.assertEqual(u'456; 789', m['musicbrainz_artistid'])
        self.assertEqual(u'Foo', m['title'])
        self.assertEqual(u'Foo Bar & Baz', m['artist'])
        self.assertEqual(u'Bar, Foo & Baz', m['artistsort'])
        self.assertEqual(u'workid123', m['musicbrainz_workid'])
        self.assertEqual(u'Bar', m['work'])
        self.assertEqual(u'eng', m['language'])


class ReleaseTest(unittest.TestCase):

    def test_1(self):
        config.setting = settings
        release = XmlNode(attribs={'id': u'123'}, children={
            'title': [XmlNode(text=u'Foo')],
            'status': [XmlNode(text=u'Official')],
            'text_representation': [XmlNode(children={
                'language': [XmlNode(text=u'eng')],
                'script': [XmlNode(text=u'Latn')]
            })],
            'artist_credit': [XmlNode(children={
                'name_credit': [XmlNode(attribs={'joinphrase': u' & '}, children={
                    'artist': [XmlNode(attribs={'id': u'456'}, children={
                        'name': [XmlNode(text=u'Foo Bar')],
                        'sort_name': [XmlNode(text=u'Bar, Foo')]
                    })]
                }), XmlNode(children={
                    'artist': [XmlNode(attribs={'id': u'789'}, children={
                        'name': [XmlNode(text=u'Baz')],
                        'sort_name': [XmlNode(text=u'Baz')]
                    })]
                })]
            })],
            'date': [XmlNode(text=u'2009-08-07')],
            'country': [XmlNode(text=u'GB')],
            'barcode': [XmlNode(text=u'012345678929')],
            'asin': [XmlNode(text=u'B123456789')],
            'label_info_list': [XmlNode(attribs={'count': u'1'}, children={
                'label_info': [XmlNode(children={
                    'catalog_number': [XmlNode(text=u'ABC 123')],
                    'label': [XmlNode(children={
                        'name': [XmlNode(text=u'ABC')]
                    })]
                })]
            })]
        })
        m = Metadata()
        release_to_metadata(release, m)
        self.assertEqual(u'123', m['musicbrainz_albumid'])
        self.assertEqual(u'456; 789', m['musicbrainz_albumartistid'])
        self.assertEqual(u'Foo', m['album'])
        self.assertEqual(u'official', m['releasestatus'])
        self.assertEqual(u'eng', m['~releaselanguage'])
        self.assertEqual(u'Latn', m['script'])
        self.assertEqual(u'Foo Bar & Baz', m['albumartist'])
        self.assertEqual(u'Bar, Foo & Baz', m['albumartistsort'])
        self.assertEqual(u'2009-08-07', m['date'])
        self.assertEqual(u'GB', m['releasecountry'])
        self.assertEqual(u'012345678929', m['barcode'])
        self.assertEqual(u'B123456789', m['asin'])
        self.assertEqual(u'ABC', m['label'])
        self.assertEqual(u'ABC 123', m['catalognumber'])


class ArtistTest(unittest.TestCase):

    def test_1(self):
        config.setting = settings
        node = XmlNode(children={
            'name_credit': [XmlNode(attribs={'joinphrase': u' & '}, children={
                'artist': [XmlNode(attribs={'id': u'456'}, children={
                    'name': [XmlNode(text=u'Foo Bar')],
                    'sort_name': [XmlNode(text=u'Bar, Foo')]
                })]
            }), XmlNode(children={
                'artist': [XmlNode(attribs={'id': u'789'}, children={
                    'name': [XmlNode(text=u'Baz')],
                    'sort_name': [XmlNode(text=u'Baz')]
                })]
            })]
        })
        artist, artist_sort, artists, artists_sort = artist_credit_from_node(node)
        self.assertEqual(u'Foo Bar & Baz', artist)
        self.assertEqual([u'Foo Bar', u'Baz'], artists)
        self.assertEqual(u'Bar, Foo & Baz', artist_sort)
        self.assertEqual([u'Bar, Foo', u'Baz'], artists_sort)
