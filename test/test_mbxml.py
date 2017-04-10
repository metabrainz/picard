# -*- coding: utf-8 -*-

import unittest
import picard
from picard import config
from picard.metadata import Metadata
from picard.mbxml import (
    track_to_metadata,
    release_to_metadata,
    artist_credit_from_node,
    _translate_artist_node
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
            'position': [XmlNode(text=u'1')],
            'recording': [XmlNode(attribs={'id': u'123'}, children={
                'title': [XmlNode(text=u'Foo')],
                'length': [XmlNode(text=u'180000')],
                'relation_list': [XmlNode(attribs={'target_type': u'work'}, children={
                    'relation': [XmlNode(attribs={'type': u'performance'}, children={
                        'target': [XmlNode(text=u'movement5')],
                        'work': [XmlNode(attribs={'id': u'movement5'}, children={
                            'title': [XmlNode(text=u'Bar Part 5')],
                            'language': [XmlNode(text=u'eng')],
                            'disambiguation': [XmlNode(text=u'Movement comment')],
                            'relation_list': [XmlNode(attribs={'target_type': u'work'}, children={
                                'relation': [XmlNode(attribs={'type': u'parts'}, children={
                                    'target': [XmlNode(text=u'work-mbid')],
                                    'ordering_key': [XmlNode(text=u'5')],
                                    'work': [XmlNode(attribs={'id': u'work-mbid'}, children={
                                        'title': [XmlNode(text=u'Bar')],
                                        'disambiguation': [XmlNode(text=u'Work comment')]
                                    })]
                                })]
                            })]
                        })],
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
        self.assertEqual(u'Bar', m['work'])
        self.assertEqual(u'Bar Part 5', m['movementname'])
        self.assertEqual(u'Work comment', m['~workcomment'])
        self.assertEqual(u'Movement comment', m['~movementcomment'])
        self.assertEqual(u'5', m['movementnumber'])
        self.assertEqual(u'work-mbid', m['musicbrainz_workid'])
        self.assertEqual(u'movement5', m['musicbrainz_movementid'])
        self.assertEqual(u'eng', m['language'])


class MultiMovementTest(unittest.TestCase):

    def test_1(self):
        config.setting = settings

        class Track:
            pass

        node = XmlNode(attribs={'id': u'321'}, children={
            'position': [XmlNode(text=u'1')],
            'recording': [XmlNode(attribs={'id': u'123'}, children={
                'title': [XmlNode(text=u'Foo')],
                'length': [XmlNode(text=u'180000')],
                'relation_list': [XmlNode(attribs={'target_type': u'work'}, children={
                    'relation': [XmlNode(attribs={'type': u'performance'}, children={
                        'target': [XmlNode(text=u'movement5')],
                        'work': [XmlNode(attribs={'id': u'movement5'}, children={
                            'title': [XmlNode(text=u'Bar Part 5')],
                            'language': [XmlNode(text=u'eng')],
                            'disambiguation': [XmlNode(text=u'Movement comment 5')],
                            'relation_list': [XmlNode(attribs={'target_type': u'work'}, children={
                                'relation': [XmlNode(attribs={'type': u'parts'}, children={
                                    'target': [XmlNode(text=u'work-mbid')],
                                    'ordering_key': [XmlNode(text=u'5')],
                                    'work': [XmlNode(attribs={'id': u'work-mbid'}, children={
                                        'title': [XmlNode(text=u'Bar')],
                                        'disambiguation': [XmlNode(text=u'Work comment')],
                                    })],
                                })],
                            })],
                        })],
                    })],
                }), XmlNode(attribs={'target_type': u'work'}, children={
                    'relation': [XmlNode(attribs={'type': u'performance'}, children={
                        'target': [XmlNode(text=u'movement6')],
                        'work': [XmlNode(attribs={'id': u'movement6'}, children={
                            'title': [XmlNode(text=u'Bar Part 6')],
                            'language': [XmlNode(text=u'eng')],
                            'disambiguation': [XmlNode(text=u'Movement comment 6')],
                            'relation_list': [XmlNode(attribs={'target_type': u'work'}, children={
                                'relation': [XmlNode(attribs={'type': u'parts'}, children={
                                    'target': [XmlNode(text=u'work-mbid')],
                                    'ordering_key': [XmlNode(text=u'6')],
                                    'work': [XmlNode(attribs={'id': u'work-mbid'}, children={
                                        'title': [XmlNode(text=u'Bar')],
                                        'disambiguation': [XmlNode(text=u'Work comment')],
                                    })],
                                })],
                            })],
                        })],
                    })],
                })],
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
        self.assertEqual(u'Bar', m['work'])
        self.assertEqual(u'Bar Part 5; Bar Part 6', m['movementname'])
        self.assertEqual(u'Work comment', m['~workcomment'])
        self.assertEqual(u'Movement comment 5; Movement comment 6', m['~movementcomment'])
        self.assertEqual(u'', m['movementnumber'])
        self.assertEqual(u'work-mbid', m['musicbrainz_workid'])
        self.assertEqual(u'movement5; movement6', m['musicbrainz_movementid'])
        self.assertEqual(u'eng', m['language'])


class MismatchedMovementTest(unittest.TestCase):

    def test_1(self):
        config.setting = settings

        class Track:
            pass

        node = XmlNode(attribs={'id': u'321'}, children={
            'position': [XmlNode(text=u'1')],
            'recording': [XmlNode(attribs={'id': u'123'}, children={
                'title': [XmlNode(text=u'Foo')],
                'length': [XmlNode(text=u'180000')],
                'relation_list': [XmlNode(attribs={'target_type': u'work'}, children={
                    'relation': [XmlNode(attribs={'type': u'performance'}, children={
                        'target': [XmlNode(text=u'movement5')],
                        'work': [XmlNode(attribs={'id': u'movement5'}, children={
                            'title': [XmlNode(text=u'Bar Part 5')],
                            'language': [XmlNode(text=u'eng')],
                            'disambiguation': [XmlNode(text=u'Movement comment 5')],
                            'relation_list': [XmlNode(attribs={'target_type': u'work'}, children={
                                'relation': [XmlNode(attribs={'type': u'parts'}, children={
                                    'target': [XmlNode(text=u'work-mbid1')],
                                    'ordering_key': [XmlNode(text=u'5')],
                                    'work': [XmlNode(attribs={'id': u'work-mbid1'}, children={
                                        'title': [XmlNode(text=u'Bar')],
                                        'disambiguation': [XmlNode(text=u'Work comment')],
                                    })],
                                })],
                            })],
                        })],
                    })],
                }), XmlNode(attribs={'target_type': u'work'}, children={
                    'relation': [XmlNode(attribs={'type': u'performance'}, children={
                        'target': [XmlNode(text=u'movement6')],
                        'work': [XmlNode(attribs={'id': u'movement6'}, children={
                            'title': [XmlNode(text=u'Bar Part 6')],
                            'language': [XmlNode(text=u'eng')],
                            'disambiguation': [XmlNode(text=u'Movement comment 6')],
                            'relation_list': [XmlNode(attribs={'target_type': u'work'}, children={
                                'relation': [XmlNode(attribs={'type': u'parts'}, children={
                                    'target': [XmlNode(text=u'work-mbid2')],
                                    'ordering_key': [XmlNode(text=u'6')],
                                    'work': [XmlNode(attribs={'id': u'work-mbid2'}, children={
                                        'title': [XmlNode(text=u'Bar')],
                                        'disambiguation': [XmlNode(text=u'Work comment')],
                                    })],
                                })],
                            })],
                        })],
                    })],
                })],
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
        self.assertEqual(u'Bar Part 5; Bar Part 6', m['work'])
        self.assertEqual(u'', m['movementname'])
        self.assertEqual(u'Movement comment 5; Movement comment 6', m['~workcomment'])
        self.assertEqual(u'', m['~movementcomment'])
        self.assertEqual(u'', m['movementnumber'])
        self.assertEqual(u'movement5; movement6', m['musicbrainz_workid'])
        self.assertEqual(u'', m['musicbrainz_movementid'])
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

    def test_trans1(self):
        config.setting = settings

        node = XmlNode(
            attribs={u'id': u'666'},
            children={
                u'name': [XmlNode(text=u'Pink Floyd')],
                u'alias_list': [
                    XmlNode(
                        attribs={u'count': u'5'},
                        children={u'alias': [
                            XmlNode(
                                text=u'Pink Floid',
                                attribs={
                                    u'type': u'Search hint',
                                    u'sort_name': u'Pink Floid Sort'
                                }
                            ),
                            XmlNode(
                                text=u'Pink Floyd Artist',
                                attribs={
                                    u'locale': u'en',
                                    u'type': u'Artist name',
                                    u'primary': u'primary',
                                    u'sort_name': u'Pink Floyd Artist Sort'
                                }
                            ),
                            XmlNode(
                                text=u'The Pink Floyd',
                                attribs={
                                    u'locale': u'en',
                                    u'type': u'Artist name',
                                    u'sort_name': u'The Pink Floyd Sort'
                                }
                            ),
                            XmlNode(
                                text=u'ピンク・フロイド',
                                attribs={
                                    u'locale': u'ja',
                                    u'type': u'Artist name',
                                    u'primary': u'primary',
                                    u'sort_name': u'ピンク・フロイド Sort'
                                }
                            ),
                            XmlNode(
                                text=u'핑크 플로이드',
                                attribs={
                                    u'locale': u'ko',
                                    u'type': u'Artist name',
                                    u'primary': u'primary',
                                    u'sort_name': u'핑크 플로이드 Sort'
                                }
                            )
                        ]}
                    )
                ],
                u'sort_name': [XmlNode(text=u'Pink Floyd Sort')]
            }
        )

        config.setting["translate_artist_names"] = False
        config.setting["artist_locale"] = "en"
        transl, translsort = _translate_artist_node(node)
        self.assertEqual(u"Pink Floyd", transl)
        self.assertEqual(u"Pink Floyd Sort", translsort)

        config.setting["translate_artist_names"] = True
        config.setting["artist_locale"] = "ja"
        transl, translsort = _translate_artist_node(node)
        self.assertEqual(u'ピンク・フロイド', transl)
        self.assertEqual(u'ピンク・フロイド Sort', translsort)

        config.setting["artist_locale"] = "ko"
        transl, translsort = _translate_artist_node(node)
        self.assertEqual(u'핑크 플로이드', transl)
        self.assertEqual(u'핑크 플로이드 Sort', translsort)

        config.setting["artist_locale"] = "en"
        transl, translsort = _translate_artist_node(node)
        self.assertEqual(u"Pink Floyd Artist", transl)
        self.assertEqual(u"Pink Floyd Artist Sort", translsort)

    def test_trans3(self):
        "Legal name vs Artist name, same locales"
        config.setting = settings

        node = XmlNode(
            attribs={u'id': u'666'},
            children={
                u'name': [XmlNode(text=u'Pink Floyd')],
                u'alias_list': [
                    XmlNode(
                        attribs={u'count': u'3'},
                        children={u'alias': [
                            XmlNode(
                                text=u'Pink Floyd Legal en',
                                attribs={
                                    u'locale': u'en',
                                    u'primary': u'primary',
                                    u'type': u'Legal Name',
                                    u'sort_name': u'Pink Floyd Legal en Sort'
                                }
                            ),
                            XmlNode(
                                text=u'Pink Floyd Artist en',
                                attribs={
                                    u'locale': u'en',
                                    u'primary': u'primary',
                                    u'type': u'Artist name',
                                    u'sort_name': u'Pink Floyd Artist en Sort'
                                }
                            ),
                            XmlNode(
                                text=u'Pink Floyd Legal en_US',
                                attribs={
                                    u'locale': u'en_US',
                                    u'primary': u'primary',
                                    u'type': u'Legal Name',
                                    u'sort_name': u'Pink Floyd Legal en_US Sort'
                                }
                            ),
                        ]}
                    )
                ],
                u'sort_name': [XmlNode(text=u'Pink Floyd Sort')]
            }
        )

        config.setting["translate_artist_names"] = True

        config.setting["artist_locale"] = "en"
        transl, translsort = _translate_artist_node(node)
        self.assertEqual(u"Pink Floyd Artist en", transl)
        self.assertEqual(u"Pink Floyd Artist en Sort", translsort)

        # should pickup Artist name/en over Legal name/en_US ?
        config.setting["artist_locale"] = "en_US"
        transl, translsort = _translate_artist_node(node)
        self.assertEqual(u"Pink Floyd Artist en", transl)
        self.assertEqual(u"Pink Floyd Artist en Sort", translsort)

    def test_trans4(self):
        "exact locale match, new type/primary set"
        config.setting = settings

        node = XmlNode(
            attribs={u'id': u'666'},
            children={
                u'name': [XmlNode(text=u'Pink Floyd')],
                u'alias_list': [
                    XmlNode(
                        attribs={u'count': u'2'},
                        children={u'alias': [
                            XmlNode(
                                text=u'Pink Floyd en',
                                attribs={
                                    u'locale': u'en_US',
                                    u'primary': u'primary',
                                    u'type': u'New type',
                                    u'sort_name': u'Pink Floyd en Sort'
                                }
                            ),
                        ]}
                    )
                ],
                u'sort_name': [XmlNode(text=u'Pink Floyd Sort')]
            }
        )

        config.setting["translate_artist_names"] = True

        config.setting["artist_locale"] = "en_US"
        transl, translsort = _translate_artist_node(node)
        self.assertEqual(u"Pink Floyd en", transl)
        self.assertEqual(u"Pink Floyd en Sort", translsort)

    def test_trans5(self):
        "Lang vs locale, all artist name/primary"
        config.setting = settings

        node = XmlNode(
            attribs={u'id': u'666'},
            children={
                u'name': [XmlNode(text=u'Pink Floyd')],
                u'alias_list': [
                    XmlNode(
                        attribs={u'count': u'2'},
                        children={u'alias': [
                            XmlNode(
                                text=u'Pink Floyd en_US',
                                attribs={
                                    u'locale': u'en_US',
                                    u'primary': u'primary',
                                    u'type': u'Artist name',
                                    u'sort_name': u'Pink Floyd en_US Sort'
                                }
                            ),
                            XmlNode(
                                text=u'Pink Floyd en_UK',
                                attribs={
                                    u'locale': u'en_UK',
                                    u'primary': u'primary',
                                    u'type': u'Artist name',
                                    u'sort_name': u'Pink Floyd en_UK Sort'
                                }
                            ),
                            XmlNode(
                                text=u'Pink Floyd en',
                                attribs={
                                    u'locale': u'en',
                                    u'primary': u'primary',
                                    u'type': u'Artist name',
                                    u'sort_name': u'Pink Floyd en Sort'
                                }
                            ),
                            XmlNode(
                                text=u'Pink Floyd en_AU',
                                attribs={
                                    u'locale': u'en_AU',
                                    u'primary': u'primary',
                                    u'type': u'Artist name',
                                    u'sort_name': u'Pink Floyd en_AU Sort'
                                }
                            ),
                        ]}
                    )
                ],
                u'sort_name': [XmlNode(text=u'Pink Floyd Sort')]
            }
        )

        config.setting["translate_artist_names"] = True

        config.setting["artist_locale"] = "en"
        transl, translsort = _translate_artist_node(node)
        self.assertEqual(u"Pink Floyd en", transl)
        self.assertEqual(u"Pink Floyd en Sort", translsort)

    def test_trans6(self):
        "No alias, name without latin chars, it will use translate_from_sortname()"
        config.setting = settings

        node = XmlNode(
            attribs={u'id': u'666'},
            children={
                u'name': [XmlNode(text=u'ピンク・フロイド')],
                u'sort_name': [XmlNode(text=u'Pink Floyd')]
            }
        )

        config.setting["translate_artist_names"] = True

        # hacky en translation is chosen over native artist's name, because
        # artist's name has no locale definition, this case is a bit weird
        config.setting["artist_locale"] = "ja"
        transl, translsort = _translate_artist_node(node)
        self.assertEqual(u"Pink Floyd", transl)
        self.assertEqual(u"Pink Floyd", translsort)
