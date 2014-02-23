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

        node = XmlNode(attribs={'id': '321'}, children={
            'title': [XmlNode(text='Foo')],
            'length': [XmlNode(text='180000')],
            'position': [XmlNode(text='1')],
            'recording': [XmlNode(attribs={'id': '123'}, children={
                'relation_list': [XmlNode(attribs={'target_type': 'work'}, children={
                    'relation': [XmlNode(attribs={'type': 'performance'}, children={
                        'work': [XmlNode(attribs={'id': 'workid123'}, children={
                            'title': [XmlNode(text='Bar')],
                            'language': [XmlNode(text='eng')]
                        })]
                    })]
                })]
            })],
            'artist_credit': [XmlNode(children={
                'name_credit': [XmlNode(attribs={'joinphrase': ' & '}, children={
                    'artist': [XmlNode(attribs={'id': '456'}, children={
                        'name': [XmlNode(text='Foo Bar')],
                        'sort_name': [XmlNode(text='Bar, Foo')]
                    })]
                }), XmlNode(children={
                    'artist': [XmlNode(attribs={'id': '789'}, children={
                        'name': [XmlNode(text='Baz')],
                        'sort_name': [XmlNode(text='Baz')]
                    })]
                })]
            })]
        })
        track = Track()
        m = track.metadata = Metadata()
        track_to_metadata(node, track)
        self.assertEqual('123', m['musicbrainz_recordingid'])
        self.assertEqual('321', m['musicbrainz_trackid'])
        self.assertEqual('456; 789', m['musicbrainz_artistid'])
        self.assertEqual('Foo', m['title'])
        self.assertEqual('Foo Bar & Baz', m['artist'])
        self.assertEqual('Bar, Foo & Baz', m['artistsort'])
        self.assertEqual('workid123', m['musicbrainz_workid'])
        self.assertEqual('Bar', m['work'])
        self.assertEqual('eng', m['language'])


class ReleaseTest(unittest.TestCase):

    def test_1(self):
        config.setting = settings
        release = XmlNode(attribs={'id': '123'}, children={
            'title': [XmlNode(text='Foo')],
            'status': [XmlNode(text='Official')],
            'text_representation': [XmlNode(children={
                'language': [XmlNode(text='eng')],
                'script': [XmlNode(text='Latn')]
            })],
            'artist_credit': [XmlNode(children={
                'name_credit': [XmlNode(attribs={'joinphrase': ' & '}, children={
                    'artist': [XmlNode(attribs={'id': '456'}, children={
                        'name': [XmlNode(text='Foo Bar')],
                        'sort_name': [XmlNode(text='Bar, Foo')]
                    })]
                }), XmlNode(children={
                    'artist': [XmlNode(attribs={'id': '789'}, children={
                        'name': [XmlNode(text='Baz')],
                        'sort_name': [XmlNode(text='Baz')]
                    })]
                })]
            })],
            'date': [XmlNode(text='2009-08-07')],
            'country': [XmlNode(text='GB')],
            'barcode': [XmlNode(text='012345678929')],
            'asin': [XmlNode(text='B123456789')],
            'label_info_list': [XmlNode(attribs={'count': '1'}, children={
                'label_info': [XmlNode(children={
                    'catalog_number': [XmlNode(text='ABC 123')],
                    'label': [XmlNode(children={
                        'name': [XmlNode(text='ABC')]
                    })]
                })]
            })]
        })
        m = Metadata()
        release_to_metadata(release, m)
        self.assertEqual('123', m['musicbrainz_albumid'])
        self.assertEqual('456; 789', m['musicbrainz_albumartistid'])
        self.assertEqual('Foo', m['album'])
        self.assertEqual('official', m['releasestatus'])
        self.assertEqual('eng', m['~releaselanguage'])
        self.assertEqual('Latn', m['script'])
        self.assertEqual('Foo Bar & Baz', m['albumartist'])
        self.assertEqual('Bar, Foo & Baz', m['albumartistsort'])
        self.assertEqual('2009-08-07', m['date'])
        self.assertEqual('GB', m['releasecountry'])
        self.assertEqual('012345678929', m['barcode'])
        self.assertEqual('B123456789', m['asin'])
        self.assertEqual('ABC', m['label'])
        self.assertEqual('ABC 123', m['catalognumber'])


class ArtistTest(unittest.TestCase):

    def test_1(self):
        config.setting = settings
        node = XmlNode(children={
            'name_credit': [XmlNode(attribs={'joinphrase': ' & '}, children={
                'artist': [XmlNode(attribs={'id': '456'}, children={
                    'name': [XmlNode(text='Foo Bar')],
                    'sort_name': [XmlNode(text='Bar, Foo')]
                })]
            }), XmlNode(children={
                'artist': [XmlNode(attribs={'id': '789'}, children={
                    'name': [XmlNode(text='Baz')],
                    'sort_name': [XmlNode(text='Baz')]
                })]
            })]
        })
        artist, artist_sort, artists = artist_credit_from_node(node)
        self.assertEqual(['Foo Bar', 'Baz'], artists)
        self.assertEqual('Foo Bar & Baz', artist)
        self.assertEqual('Bar, Foo & Baz', artist_sort)
