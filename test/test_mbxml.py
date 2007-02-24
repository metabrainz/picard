import unittest
from picard.metadata import Metadata
from picard.mbxml import track_to_metadata, release_to_metadata
from picard.webservice import XmlNode

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
                raise AttributeError, name


class TrackTest(unittest.TestCase):

    def test_1(self):
        track = XmlNode(attribs={'id': '123'}, children={
            'title': [XmlNode(text='Foo')],
            'artist': [XmlNode(attribs={'id': '546'}, children={
                'name': [XmlNode(text='Artist')]
            })],
        })
        m = Metadata()
        track_to_metadata(track, m)
        self.failUnlessEqual('123', m['musicbrainz_trackid'])
        self.failUnlessEqual('546', m['musicbrainz_artistid'])
        self.failUnlessEqual('Foo', m['title'])
        self.failUnlessEqual('Artist', m['artist'])


class ReleaseTest(unittest.TestCase):

    def test_1(self):
        release = XmlNode(attribs={'id': '123'}, children={
            'title': [XmlNode(text='Foo')],
            'artist': [XmlNode(attribs={'id': '546'}, children={
                'name': [XmlNode(text='Artist')]
            })],
        })
        m = Metadata()
        release_to_metadata(release, m)
        self.failUnlessEqual('123', m['musicbrainz_albumid'])
        self.failUnlessEqual('546', m['musicbrainz_artistid'])
        self.failUnlessEqual('546', m['musicbrainz_albumartistid'])
        self.failUnlessEqual('Foo', m['album'])
        self.failUnlessEqual('Artist', m['artist'])
        self.failUnlessEqual('Artist', m['albumartist'])
