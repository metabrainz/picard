import unittest
from picard.metadata import Metadata
from picard.mbxml import track_to_metadata, release_to_metadata

class config:
    setting = {
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
        class Track:
            pass
        node = XmlNode(children={
            'title': [XmlNode(text='Foo')],
            'length': [XmlNode(text='180000')],
            'position': [XmlNode(text='1')],
            'recording': [XmlNode(attribs={'id': '123'}, children={
                'relation_list': [XmlNode(attribs={'target_type': 'work'}, children={
                    'relation': [XmlNode(attribs={'type': 'performance'}, children={
                        'work': [XmlNode(attribs={'id': 'workid123'}, children={
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
        track_to_metadata(node, track, config)
        self.failUnlessEqual('123', m['musicbrainz_trackid'])
        self.failUnlessEqual('456; 789', m['musicbrainz_artistid'])
        self.failUnlessEqual('Foo', m['title'])
        self.failUnlessEqual('Foo Bar & Baz', m['artist'])
        self.failUnlessEqual('Bar, Foo & Baz', m['artistsort'])
        self.failUnlessEqual('workid123', m['musicbrainz_workid'])
        self.failUnlessEqual('eng', m['language'])

class ReleaseTest(unittest.TestCase):

    def test_1(self):
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
        release_to_metadata(release, m, config)
        self.failUnlessEqual('123', m['musicbrainz_albumid'])
        self.failUnlessEqual('456; 789', m['musicbrainz_albumartistid'])
        self.failUnlessEqual('Foo', m['album'])
        self.failUnlessEqual('official', m['releasestatus'])
        self.failUnlessEqual('eng', m['~releaselanguage'])
        self.failUnlessEqual('Latn', m['script'])
        self.failUnlessEqual('Foo Bar & Baz', m['albumartist'])
        self.failUnlessEqual('Bar, Foo & Baz', m['albumartistsort'])
        self.failUnlessEqual('2009-08-07', m['date'])
        self.failUnlessEqual('GB', m['releasecountry'])
        self.failUnlessEqual('012345678929', m['barcode'])
        self.failUnlessEqual('B123456789', m['asin'])
        self.failUnlessEqual('ABC', m['label'])
        self.failUnlessEqual('ABC 123', m['catalognumber'])
