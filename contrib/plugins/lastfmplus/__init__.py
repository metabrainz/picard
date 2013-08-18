# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Last.fm.Plus'
PLUGIN_AUTHOR = u'RifRaf, Lukáš Lalinský, voiceinsideyou'
PLUGIN_DESCRIPTION = u'''Uses folksonomy tags from Last.fm to<br/>
* Sort music into major and minor genres based on configurable genre "whitelists"<br/>
* Add "mood", "occasion" and other custom categories<br/>
* Add "original release year" and "decade" tags, as well as populate blank dates.'''
PLUGIN_VERSION = "0.14"
PLUGIN_API_VERSIONS = ["0.15"]

from PyQt4 import QtGui, QtCore
from picard.metadata import register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from picard.config import BoolOption, IntOption, TextOption
from picard.plugins.lastfmplus.ui_options_lastfm import Ui_LastfmOptionsPage
from picard.util import partial
import traceback
import re

LASTFM_HOST = "ws.audioscrobbler.com"
LASTFM_PORT = 80

# From http://www.last.fm/api/tos, 2011-07-30
# 4.4 (...) You will not make more than 5 requests per originating IP address per second, averaged over a
# 5 minute period, without prior written consent. (...)
from picard.webservice import REQUEST_DELAY
REQUEST_DELAY[(LASTFM_HOST, LASTFM_PORT)] = 200

# Cache for Tags to avoid re-requesting tags within same Picard session
_cache = {}
# Keeps track of requests for tags made to webservice API but not yet returned (to avoid re-requesting the same URIs)
_pending_xmlws_requests = {}

# Cache to Find the Genres and other Tags
ALBUM_GENRE = {}
ALBUM_SUBGENRE = {}
ALBUM_COUNTRY = {}
ALBUM_CITY = {}
ALBUM_DECADE = {}
ALBUM_YEAR = {}
ALBUM_OCCASION = {}
ALBUM_CATEGORY = {}
ALBUM_MOOD = {}

#noinspection PyDictCreation
GENRE_FILTER = {}
GENRE_FILTER["_loaded_"] = False
GENRE_FILTER["major"] = ["audiobooks, blues, classic rock, classical, country, dance, electronica, folk, hip-hop, indie, jazz, kids, metal, pop, punk, reggae, rock, soul, trance"]
GENRE_FILTER["minor"] = ["2 tone, a cappella, abstract hip-hop, acid, acid jazz, acid rock, acoustic, acoustic guitar, acoustic rock, adult alternative, adult contemporary, alternative, alternative country, alternative folk, alternative metal, alternative pop, alternative rock, ambient, anti-folk, art rock, atmospheric, aussie hip-hop, avant-garde, ballads, baroque, beach, beats, bebop, big band, blaxploitation, blue-eyed soul, bluegrass, blues rock, boogie rock, boogie woogie, bossa nova, breakbeat, breaks, brit pop, brit rock, british invasion, broadway, bubblegum pop, cabaret, calypso, cha cha, choral, christian rock, classic country, classical guitar, club, college rock, composers, contemporary country, contemporary folk, country folk, country pop, country rock, crossover, dance pop, dancehall, dark ambient, darkwave, delta blues, dirty south, disco, doo wop, doom metal, downtempo, dream pop, drum and bass, dub, dub reggae, dubstep, east coast rap, easy listening, electric blues, electro, electro pop, elevator music, emo, emocore, ethnic, eurodance, europop, experimental, fingerstyle, folk jazz, folk pop, folk punk, folk rock, folksongs, free jazz, french rap, funk, funk metal, funk rock, fusion, g-funk, gaelic, gangsta rap, garage, garage rock, glam rock, goa trance, gospel, gothic, gothic metal, gothic rock, gregorian, groove, grunge, guitar, happy hardcore, hard rock, hardcore, hardcore punk, hardcore rap, hardstyle, heavy metal, honky tonk, horror punk, house, humour, hymn, idm, indie folk, indie pop, indie rock, industrial, industrial metal, industrial rock, instrumental, instrumental hip-hop, instrumental rock, j-pop, j-rock, jangle pop, jazz fusion, jazz vocal, jungle, latin, latin jazz, latin pop, lounge, lovers rock, lullaby, madchester, mambo, medieval, melodic rock, minimal, modern country, modern rock, mood music, motown, neo-soul, new age, new romantic, new wave, noise, northern soul, nu metal, old school rap, opera, orchestral, philly soul, piano, political reggae, polka, pop life, pop punk, pop rock, pop soul, post punk, post rock, power pop, progressive, progressive rock, psychedelic, psychedelic folk, psychedelic punk, psychedelic rock, psychobilly, psytrance, punk rock, quiet storm, r&b, ragga, rap, rap metal, reggae pop, reggae rock, rock and roll, rock opera, rockabilly, rocksteady, roots, roots reggae, rumba, salsa, samba, screamo, shock rock, shoegaze, ska, ska punk, smooth jazz, soft rock, southern rock, space rock, spoken word, standards, stoner rock, surf rock, swamp rock, swing, symphonic metal, symphonic rock, synth pop, tango, techno, teen pop, thrash metal, traditional country, traditional folk, tribal, trip-hop, turntablism, underground, underground hip-hop, underground rap, urban, vocal trance, waltz, west coast rap, western swing, world, world fusion"]
GENRE_FILTER["country"] = ["african, american, arabic, australian, austrian, belgian, brazilian, british, canadian, caribbean, celtic, chinese, cuban, danish, dutch, eastern europe, egyptian, estonian, european, finnish, french, german, greek, hawaiian, ibiza, icelandic, indian, iranian, irish, island, israeli, italian, jamaican, japanese, korean, mexican, middle eastern, new zealand, norwegian, oriental, polish, portuguese, russian, scandinavian, scottish, southern, spanish, swedish, swiss, thai, third world, turkish, welsh, western"]
GENRE_FILTER["city"] = ["acapulco, adelaide, amsterdam, athens, atlanta, atlantic city, auckland, austin, bakersfield, bali, baltimore, bangalore, bangkok, barcelona, barrie, beijing, belfast, berlin, birmingham, bogota, bombay, boston, brasilia, brisbane, bristol, brooklyn, brussels, bucharest, budapest, buenos aires, buffalo, calcutta, calgary, california, cancun, caracas, charlotte, chicago, cincinnati, cleveland, copenhagen, dallas, delhi, denver, detroit, dublin, east coast, edmonton, frankfurt, geneva, glasgow, grand rapids, guadalajara, halifax, hamburg, hamilton, helsinki, hong kong, houston, illinois, indianapolis, istanbul, jacksonville, kansas city, kiev, las vegas, leeds, lisbon, liverpool, london, los angeles, louisville, madrid, manchester, manila, marseille, mazatlan, melbourne, memphis, mexico city, miami, michigan, milan, minneapolis, minnesota, mississippi, monterrey, montreal, munich, myrtle beach, nashville, new jersey, new orleans, new york, new york city, niagara falls, omaha, orlando, oslo, ottawa, palm springs, paris, pennsylvania, perth, philadelphia, phoenix, phuket, pittsburgh, portland, puebla, raleigh, reno, richmond, rio de janeiro, rome, sacramento, salt lake city, san antonio, san diego, san francisco, san jose, santiago, sao paulo, seattle, seoul, shanghai, sheffield, spokane, stockholm, sydney, taipei, tampa, texas, tijuana, tokyo, toledo, toronto, tucson, tulsa, vancouver, victoria, vienna, warsaw, wellington, westcoast, windsor, winnipeg, zurich"]
GENRE_FILTER["mood"] = ["angry, bewildered, bouncy, calm, cheerful, chill, cold, complacent, crazy, crushed, cynical, depressed, dramatic, dreamy, drunk, eclectic, emotional, energetic, envious, feel good, flirty, funky, groovy, happy, haunting, healing, high, hopeful, hot, humorous, inspiring, intense, irritated, laidback, lonely, lovesongs, meditation, melancholic, melancholy, mellow, moody, morose, passionate, peace, peaceful, playful, pleased, positive, quirky, reflective, rejected, relaxed, retro, sad, sentimental, sexy, silly, smooth, soulful, spiritual, suicidal, surprised, sympathetic, trippy, upbeat, uplifting, weird, wild, yearning"]
GENRE_FILTER["decade"] = ["1800s, 1810s, 1820s, 1830s, 1980s, 1850s, 1860s, 1870s, 1880s, 1890s, 1900s, 1910s, 1920s, 1930s, 1940s, 1950s, 1960s, 1970s, 1980s, 1990s, 2000s"]
GENRE_FILTER["year"] = ["1801, 1802, 1803, 1804, 1805, 1806, 1807, 1808, 1809, 1810, 1811, 1812, 1813, 1814, 1815, 1816, 1817, 1818, 1819, 1820, 1821, 1822, 1823, 1824, 1825, 1826, 1827, 1828, 1829, 1830, 1831, 1832, 1833, 1834, 1835, 1836, 1837, 1838, 1839, 1840, 1841, 1842, 1843, 1844, 1845, 1846, 1847, 1848, 1849, 1850, 1851, 1852, 1853, 1854, 1855, 1856, 1857, 1858, 1859, 1860, 1861, 1862, 1863, 1864, 1865, 1866, 1867, 1868, 1869, 1870, 1871, 1872, 1873, 1874, 1875, 1876, 1877, 1878, 1879, 1880, 1881, 1882, 1883, 1884, 1885, 1886, 1887, 1888, 1889, 1890, 1891, 1892, 1893, 1894, 1895, 1896, 1897, 1898, 1899, 1900, 1901, 1902, 1903, 1904, 1905, 1906, 1907, 1908, 1909, 1910, 1911, 1912, 1913, 1914, 1915, 1916, 1917, 1918, 1919, 1920, 1921, 1922, 1923, 1924, 1925, 1926, 1927, 1928, 1929, 1930, 1931, 1932, 1933, 1934, 1935, 1936, 1937, 1938, 1939, 1940, 1941, 1942, 1943, 1944, 1945, 1946, 1947, 1948, 1949, 1950, 1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 1960, 1961, 1962, 1963, 1964, 1965, 1966, 1967, 1968, 1969, 1970, 1971, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020"]
GENRE_FILTER["occasion"] = ["background, birthday, breakup, carnival, chillout, christmas, death, dinner, drinking, driving, graduation, halloween, hanging out, heartache, holiday, late night, love, new year, party, protest, rain, rave, romantic, sleep, spring, summer, sunny, twilight, valentine, wake up, wedding, winter, work"]
GENRE_FILTER["category"] = ["animal songs, attitude, autumn, b-side, ballad, banjo, bass, beautiful, body parts, bootlegs, brass, cafe del mar, chamber music, clarinet, classic, classic tunes, compilations, covers, cowbell, deceased, demos, divas, dj, drugs, drums, duets, field recordings, female, female vocalists, film score, flute, food, genius, girl group, great lyrics, guitar solo, guitarist, handclaps, harmonica, historical, horns, hypnotic, influential, insane, jam, keyboard, legends, life, linedance, live, loved, lyricism, male, male vocalists, masterpiece, melodic, memories, musicals, nostalgia, novelty, number songs, old school, oldie, oldies, one hit wonders, orchestra, organ, parody, poetry, political, promos, radio programs, rastafarian, remix, samples, satire, saxophone, showtunes, sing-alongs, singer-songwriter, slide guitar, solo instrumentals, songs with names, soundtracks, speeches, stories, strings, stylish, synth, title is a full sentence, top 40, traditional, trumpet, unique, unplugged, violin, virtuoso, vocalization, vocals"]
GENRE_FILTER["translate"] = {
"drum 'n' bass": u"drum and bass",
"drum n bass": u"drum and bass"
}


def matches_list(s, lst):
    if s in lst:
        return True
    for item in lst:
        if '*' in item:
            if re.match(re.escape(item).replace(r'\*', '.*?'), s):
                return True
    return False

# Function to sort/compare a 2 Element of Tupel


def cmp1(a, b):
    return cmp(a[1], b[1]) * -1
# Special Compare/Sort-Function to sort downloaded Tags


def cmptaginfo(a, b):
    return cmp(a[1][0], b[1][0]) * -1


def _lazy_load_filters(cfg):
    if not GENRE_FILTER["_loaded_"]:
        GENRE_FILTER["major"] = cfg["lastfm_genre_major"].split(',')
        GENRE_FILTER["minor"] = cfg["lastfm_genre_minor"].split(',')
        GENRE_FILTER["decade"] = cfg["lastfm_genre_decade"].split(',')
        GENRE_FILTER["year"] = cfg["lastfm_genre_year"].split(',')
        GENRE_FILTER["country"] = cfg["lastfm_genre_country"].split(',')
        GENRE_FILTER["city"] = cfg["lastfm_genre_city"].split(',')
        GENRE_FILTER["mood"] = cfg["lastfm_genre_mood"].split(',')
        GENRE_FILTER["occasion"] = cfg["lastfm_genre_occasion"].split(',')
        GENRE_FILTER["category"] = cfg["lastfm_genre_category"].split(',')
        GENRE_FILTER["translate"] = dict([item.split(',') for item in cfg["lastfm_genre_translations"].split("\n")])
        GENRE_FILTER["_loaded_"] = True


def apply_translations_and_sally(tag_to_count, sally, factor):
    ret = {}
    for name, count in tag_to_count.iteritems():
        # apply translations
        try:
            name = GENRE_FILTER["translate"][name.lower()]
        except KeyError:
            pass

        # make sure it's lowercase
        lower = name.lower()

        if lower not in ret or ret[lower][0] < (count * factor):
            ret[lower] = [count * factor, sally]
    return ret.items()


def _tags_finalize(album, metadata, tags, next):
    """Processes the tag metadata to decide which tags to use and sets metadata"""

    if next:
        next(tags)
    else:
        cfg = album.tagger.config.setting

        # last tag-weight for inter-tag comparsion
        lastw = {"n": False, "s": False}
        # List: (use sally-tags, use track-tags, use artist-tags, use
        # drop-info,use minweight,searchlist, max_elems
        info = {"major"   : [True,  True,  True,  True,  True,  GENRE_FILTER["major"],   cfg["lastfm_max_group_tags"]],
                "minor"   : [True,  True,  True,  True,  True,  GENRE_FILTER["minor"],   cfg["lastfm_max_minor_tags"]],
                "country" : [True,  False, True,  False, False, GENRE_FILTER["country"], 1],
                "city"    : [True,  False, True,  False, False, GENRE_FILTER["city"], 1],
                "decade"  : [True,  True,  False, False, False, GENRE_FILTER["decade"], 1],
                "year"    : [True,  True,  False, False, False, GENRE_FILTER["year"], 1],
                "year2"   : [True,  True,  False, False, False, GENRE_FILTER["year"], 1],
                "year3"   : [True,  True,  False, False, False, GENRE_FILTER["year"], 1],
                "mood"    : [True,  True,  True,  False, False, GENRE_FILTER["mood"],  cfg["lastfm_max_mood_tags"]],
                "occasion": [True,  True,  True,  False, False, GENRE_FILTER["occasion"],  cfg["lastfm_max_occasion_tags"]],
                "category": [True,  True,  True,  False, False, GENRE_FILTER["category"],  cfg["lastfm_max_category_tags"]]
               }
        hold = {"all/tags": []}

        # Init the Album-Informations
        albid = album.id
        if cfg["write_id3v23"]:
            year_tag = '~id3:TORY'
        else:
            year_tag = '~id3:TDOR'
        glb = {"major"    : {'metatag' : 'grouping', 'data' : ALBUM_GENRE},
               "country"  : {'metatag' : 'comment:Songs-DB_Custom3', 'data' : ALBUM_COUNTRY},
               "city"     : {'metatag' : 'comment:Songs-DB_Custom3', 'data' : ALBUM_CITY},
               "year"     : {'metatag' : year_tag, 'data' : ALBUM_YEAR},
               "year2"    : {'metatag' : 'originalyear', 'data' : ALBUM_YEAR},
               "year3"    : {'metatag' : 'date', 'data' : ALBUM_YEAR} }
        for elem in glb.keys():
            if not albid in glb[elem]['data']:
                glb[elem]['data'][albid] = {'count': 1, 'genres': {}}
            else:
                glb[elem]['data'][albid]['count'] += 1

        if tags:
            # search for tags
            tags.sort(cmp=cmptaginfo)
            for lowered, [weight, stype] in tags:
                name = lowered.title()
                # if is tag which should only used for extension (if too few
                # tags found)
                s = stype == 1
                arttag = stype > 0  # if is artist tag
                if not name in hold["all/tags"]:
                    hold["all/tags"].append(name)

                # Decide if tag should be searched in major and minor fields
                drop = not (s and (not lastw['s'] or (lastw['s'] - weight) < cfg["lastfm_max_artisttag_drop"])) and not (
                    not s and (not lastw['n'] or (lastw['n'] - weight) < cfg["lastfm_max_tracktag_drop"]))
                if not drop:
                    if s:
                        lastw['s'] = weight
                    else:
                        lastw['n'] = weight

                below = (s and weight < cfg["lastfm_min_artisttag_weight"]) or (
                    not s and weight < cfg["lastfm_min_tracktag_weight"])

                for group, ielem in info.items():
                    if matches_list(lowered, ielem[5]):
                        if below and ielem[4]:
                            # If Should use min-weigh information
                            break
                        if drop and ielem[3]:
                            # If Should use the drop-information
                            break
                        if s and not ielem[0]:
                            # If Sally-Tag and should not be used
                            break
                        if arttag and not ielem[2]:
                            # If Artist-Tag and should not be used
                            break
                        if not arttag and not ielem[1]:
                            # If Track-Tag and should not be used
                            break

                        # prefer Not-Sally-Tags (so, artist OR track-tags)
                        if not s and group + "/sally" in hold and name in hold[group + "/sally"]:
                            hold[group + "/sally"].remove(name)
                            hold[group + "/tags"].remove(name)
                        # Insert Tag
                        if not group + "/tags" in hold:
                            hold[group + "/tags"] = []
                        if not name in hold[group + "/tags"]:
                            if s:
                                if not group + "/sally" in hold:
                                    hold[group + "/sally"] = []
                                hold[group + "/sally"].append(name)
                            # collect global genre information for special
                            # tag-filters
                            if not arttag and group in glb:
                                if not name in glb[group]['data'][albid]['genres']:
                                    glb[group]['data'][albid][
                                        'genres'][name] = weight
                                else:
                                    glb[group]['data'][albid][
                                        'genres'][name] += weight
                            # append tag
                            hold[group + "/tags"].append(name)
                        # Break becase every Tag should be faced only by one
                        # GENRE_FILTER
                        break

            # cut to wanted size
            for group, ielem in info.items():
                while group + "/tags" in hold and len(hold[group + "/tags"]) > ielem[6]:
                    # Remove first all Sally-Tags
                    if group + "/sally" in hold and len(hold[group + "/sally"]) > 0:
                        deltag = hold[group + "/sally"].pop()
                        hold[group + "/tags"].remove(deltag)
                    else:
                        hold[group + "/tags"].pop()

            # join the information
            join_tags = cfg["lastfm_join_tags_sign"]

            def join_tags_or_not(list):
                if join_tags:
                    return join_tags.join(list)
                return list
            if 1:
                used = []

                # write the major-tags
                if "major/tags" in hold and len(hold["major/tags"]) > 0:
                    metadata["grouping"] = join_tags_or_not(hold["major/tags"])
                    used.extend(hold["major/tags"])

                # write the decade-tags
                if "decade/tags" in hold and len(hold["decade/tags"]) > 0 and cfg["lastfm_use_decade_tag"]:
                    metadata["comment:Songs-DB_Custom1"] = join_tags_or_not(
                        [item.lower() for item in hold["decade/tags"]])
                    used.extend(hold["decade/tags"])

                # write country tag
                if "country/tags" in hold and len(hold["country/tags"]) > 0 and "city/tags" in hold and len(hold["city/tags"]) > 0 and cfg["lastfm_use_country_tag"] and cfg["lastfm_use_city_tag"]:
                    metadata["comment:Songs-DB_Custom3"] = join_tags_or_not(
                        hold["country/tags"] + hold["city/tags"])
                    used.extend(hold["country/tags"])
                    used.extend(hold["city/tags"])
                elif "country/tags" in hold and len(hold["country/tags"]) > 0 and cfg["lastfm_use_country_tag"]:
                    metadata["comment:Songs-DB_Custom3"] = join_tags_or_not(
                        hold["country/tags"])
                    used.extend(hold["country/tags"])
                elif "city/tags" in hold and len(hold["city/tags"]) > 0 and cfg["lastfm_use_city_tag"]:
                    metadata["comment:Songs-DB_Custom3"] = join_tags_or_not(
                        hold["city/tags"])
                    used.extend(hold["city/tags"])

                # write the mood-tags
                if "mood/tags" in hold and len(hold["mood/tags"]) > 0:
                    metadata["mood"] = join_tags_or_not(hold["mood/tags"])
                    used.extend(hold["mood/tags"])

                # write the occasion-tags
                if "occasion/tags" in hold and len(hold["occasion/tags"]) > 0:
                    metadata["comment:Songs-DB_Occasion"] = join_tags_or_not(
                        hold["occasion/tags"])
                    used.extend(hold["occasion/tags"])

                # write the category-tags
                if "category/tags" in hold and len(hold["category/tags"]) > 0:
                    metadata["comment:Songs-DB_Custom2"] = join_tags_or_not(
                        hold["category/tags"])
                    used.extend(hold["category/tags"])

                # include major tags as minor tags also copy major to minor if
                # no minor genre
                if cfg["lastfm_app_major2minor_tag"] and "major/tags" in hold and "minor/tags" in hold and len(hold["minor/tags"]) > 0:
                    used.extend(hold["major/tags"])
                    used.extend(hold["minor/tags"])
                    if len(used) > 0:
                        metadata["genre"] = join_tags_or_not(
                            hold["major/tags"] + hold["minor/tags"])
                elif cfg["lastfm_app_major2minor_tag"] and "major/tags" in hold and "minor/tags" not in hold:
                    used.extend(hold["major/tags"])
                    if len(used) > 0:
                        metadata["genre"] = join_tags_or_not(
                            hold["major/tags"])
                elif "minor/tags" in hold and len(hold["minor/tags"]) > 0:
                        metadata["genre"] = join_tags_or_not(
                            hold["minor/tags"])
                        used.extend(hold["minor/tags"])
                else:
                    if "minor/tags" not in hold and "major/tags" in hold:
                        metadata["genre"] = metadata["grouping"]

                # replace blank original year with release date
                if cfg["lastfm_use_year_tag"]:
                    if "year/tags" not in hold and len(metadata["date"]) > 0:
                        metadata["originalyear"] = metadata["date"][:4]
                        if cfg["write_id3v23"]:
                            metadata["~id3:TORY"] = metadata["date"][:4]
                            #album.tagger.log.info('TORY: %r', metadata["~id3:TORY"])
                        else:
                            metadata["~id3:TDOR"] = metadata["date"][:4]
                            #album.tagger.log.info('TDOR: %r', metadata["~id3:TDOR"])
                    if metadata["originalyear"] > metadata["date"][:4]:
                        metadata["originalyear"] = metadata["date"][:4]
                    if metadata["~id3:TDOR"] > metadata["date"][:4] and not cfg["write_id3v23"]:
                        metadata["~id3:TDOR"] = metadata["date"][:4]
                    if metadata["~id3:TORY"] > metadata["date"][:4] and cfg["write_id3v23"]:
                        metadata["~id3:TORY"] = metadata["date"][:4]
                # Replace blank decades
                if "decade/tags" not in hold and len(metadata["originalyear"])>0 and int(metadata["originalyear"])>1999 and cfg["lastfm_use_decade_tag"]:
                    metadata["comment:Songs-DB_Custom1"] = "20%s0s" % str(metadata["originalyear"])[2]
                elif "decade/tags" not in hold and len(metadata["originalyear"])>0 and int(metadata["originalyear"])<2000 and int(metadata["originalyear"])>1899 and cfg["lastfm_use_decade_tag"]:
                    metadata["comment:Songs-DB_Custom1"] = "19%s0s" % str(metadata["originalyear"])[2]
                elif "decade/tags" not in hold and len(metadata["originalyear"])>0 and int(metadata["originalyear"])<1900 and int(metadata["originalyear"])>1799 and cfg["lastfm_use_decade_tag"]:
                    metadata["comment:Songs-DB_Custom1"] = "18%s0s" % str(metadata["originalyear"])[2]


def _tags_downloaded(album, metadata, sally, factor, next, current, data, reply, error):
    try:

        try:
            intags = data.toptags[0].tag
        except AttributeError:
            intags = []

        # Extract just names and counts from response; apply no parsing at this stage
        tag_to_count = {}
        for tag in intags:
            # name of the tag
            name = tag.name[0].text.strip()

            # count of the tag
            try:
                count = int(tag.count[0].text.strip())
            except ValueError:
                count = 0

            tag_to_count[name] = count

        url = str(reply.url().path())
        _cache[url] = tag_to_count

        tags = apply_translations_and_sally(tag_to_count, sally, factor)

        _tags_finalize(album, metadata, current + tags, next)

        # Process any pending requests for the same URL
        if url in _pending_xmlws_requests:
            pending = _pending_xmlws_requests[url]
            del _pending_xmlws_requests[url]
            for delayed_call in pending:
                delayed_call()

    except:
        album.tagger.log.error("Problem processing downloaded tags in last.fm plus plugin: %s", traceback.format_exc())
        raise
    finally:
        album._requests -= 1
        album._finalize_loading(None)


def get_tags(album, metadata, path, sally, factor, next, current):
    """Get tags from an URL."""

    # Ensure config is loaded (or reloaded if has been changed)
    _lazy_load_filters(album.tagger.config.setting)

    url = str(QtCore.QUrl.fromPercentEncoding(path))
    if url in _cache:
        tags = apply_translations_and_sally(_cache[url], sally, factor)
        _tags_finalize(album, metadata, current + tags, next)
    else:

        # If we have already sent a request for this URL, delay this call until later
        if url in _pending_xmlws_requests:
            _pending_xmlws_requests[url].append(partial(get_tags, album, metadata, path, sally, factor, next, current))
        else:
            _pending_xmlws_requests[url] = []
            album._requests += 1
            album.tagger.xmlws.get(LASTFM_HOST, LASTFM_PORT, path,
                                   partial(_tags_downloaded, album, metadata, sally, factor, next, current),
                                   priority=True, important=True)

def encode_str(s):
    # Yes, that's right, Last.fm prefers double URL-encoding
    s = QtCore.QUrl.toPercentEncoding(s)
    s = QtCore.QUrl.toPercentEncoding(unicode(s))
    return s


def get_track_tags(album, metadata, artist, track, next, current):
    path = "/1.0/track/%s/%s/toptags.xml" % (encode_str(artist), encode_str(track))
    sally = 0
    factor = 1.0
    return get_tags(album, metadata, path, sally, factor, next, current)


def get_artist_tags(album, metadata, artist, next, current):
    path = "/1.0/artist/%s/toptags.xml" % encode_str(artist)
    sally = 2
    if album.tagger.config.setting["lastfm_artist_tag_us_ex"]:
        sally = 1
    factor = album.tagger.config.setting["lastfm_artist_tags_weight"] / 100.0
    return get_tags(album, metadata, path, sally, factor, next, current)


def process_track(album, metadata, release, track):
    tagger = album.tagger
    use_track_tags = tagger.config.setting["lastfm_use_track_tags"]
    use_artist_tags = tagger.config.setting["lastfm_artist_tag_us_ex"] or tagger.config.setting["lastfm_artist_tag_us_yes"]

    if use_track_tags or use_artist_tags:
        artist = metadata["artist"]
        title = metadata["title"]
        if artist:
            if use_artist_tags:
                get_artist_tags_func = partial(get_artist_tags, album, metadata, artist, None)
            else:
                get_artist_tags_func = None
            if title and use_track_tags:
                get_track_tags(album, metadata, artist, title, get_artist_tags_func, [])
            elif get_artist_tags_func:
                get_artist_tags_func([])


class LastfmOptionsPage(OptionsPage):
    NAME = "lastfmplus"
    TITLE = "Last.fm.Plus"
    PARENT = "plugins"

    options = [
        IntOption("setting", "lastfm_max_minor_tags", 4),
        IntOption("setting", "lastfm_max_group_tags", 1),
        IntOption("setting", "lastfm_max_mood_tags", 4),
        IntOption("setting", "lastfm_max_occasion_tags", 4),
        IntOption("setting", "lastfm_max_category_tags", 4),
        BoolOption("setting", "lastfm_use_country_tag", True),
        BoolOption("setting", "lastfm_use_city_tag", True),
        BoolOption("setting", "lastfm_use_decade_tag", True),
        BoolOption("setting", "lastfm_use_year_tag", True),
        TextOption("setting", "lastfm_join_tags_sign", "; "),
        BoolOption("setting", "lastfm_app_major2minor_tag", True),
        BoolOption("setting", "lastfm_use_track_tags", True),
        IntOption("setting", "lastfm_min_tracktag_weight", 5),
        IntOption("setting", "lastfm_max_tracktag_drop", 90),
        BoolOption("setting", "lastfm_artist_tag_us_no", False),
        BoolOption("setting", "lastfm_artist_tag_us_ex", True),
        BoolOption("setting", "lastfm_artist_tag_us_yes", False),
        IntOption("setting", "lastfm_artist_tags_weight", 95),
        IntOption("setting", "lastfm_min_artisttag_weight", 10),
        IntOption("setting", "lastfm_max_artisttag_drop", 80),
        TextOption("setting", "lastfm_genre_major", ",".join(GENRE_FILTER["major"]).lower()),
        TextOption("setting", "lastfm_genre_minor", ",".join(GENRE_FILTER["minor"]).lower()),
        TextOption("setting", "lastfm_genre_decade",", ".join(GENRE_FILTER["decade"]).lower()),
        TextOption("setting", "lastfm_genre_year",", ".join(GENRE_FILTER["year"]).lower()),
        TextOption("setting", "lastfm_genre_occasion",", ".join(GENRE_FILTER["occasion"]).lower()),
        TextOption("setting", "lastfm_genre_category",", ".join(GENRE_FILTER["category"]).lower()),
        TextOption("setting", "lastfm_genre_country",", ".join(GENRE_FILTER["country"]).lower()),
        TextOption("setting", "lastfm_genre_city",", ".join(GENRE_FILTER["city"]).lower()),
        TextOption("setting", "lastfm_genre_mood", ",".join(GENRE_FILTER["mood"]).lower()),
        TextOption("setting", "lastfm_genre_translations", "\n".join(["%s,%s" % (k,v) for k, v in GENRE_FILTER["translate"].items()]).lower())
    ]

    def __init__(self, parent=None):
        super(LastfmOptionsPage, self).__init__(parent)
        self.ui = Ui_LastfmOptionsPage()
        self.ui.setupUi(self)
        # TODO Not yet implemented properly
        # self.connect(self.ui.check_translation_list, QtCore.SIGNAL("clicked()"), self.check_translations)
        self.connect(self.ui.check_word_lists,
                     QtCore.SIGNAL("clicked()"), self.check_words)
        self.connect(self.ui.load_default_lists,
                     QtCore.SIGNAL("clicked()"), self.load_defaults)
        self.connect(self.ui.filter_report,
                     QtCore.SIGNAL("clicked()"), self.create_report)

    # function to check all translations and make sure a corresponding word
    # exists in word lists, notify in message translations pointing nowhere.
    def check_translations(self):
        cfg = self.config.setting
        translations = (cfg["lastfm_genre_translations"].replace("\n", "|"))
        tr2 = list(item for item in translations.split('|'))
        wordlists = (cfg["lastfm_genre_major"] + cfg["lastfm_genre_minor"] + cfg["lastfm_genre_country"] + cfg["lastfm_genre_occasion"]
                     + cfg["lastfm_genre_mood"] + cfg["lastfm_genre_decade"] + cfg["lastfm_genre_year"] + cfg["lastfm_genre_category"])
        # TODO need to check to see if translations are in wordlists
        QtGui.QMessageBox.information(
            self, self.tr("QMessageBox.showInformation()"), ",".join(tr2))

    # function to check that word lists contain no duplicate entries, notify
    # in message duplicates and which lists they appear in
    def check_words(self):
        cfg = self.config.setting
        # Create a set for each option cfg option

        word_sets = {
            "Major": set(str(self.ui.genre_major.text()).split(",")),
            "Minor": set(str(self.ui.genre_minor.text()).split(",")),
            "Countries": set(str(self.ui.genre_country.text()).split(",")),
            "Cities": set(str(self.ui.genre_city.text()).split(",")),
            "Moods": set(str(self.ui.genre_mood.text()).split(",")),
            "Occasions": set(str(self.ui.genre_occasion.text()).split(",")),
            "Decades": set(str(self.ui.genre_decade.text()).split(",")),
            "Years": set(str(self.ui.genre_year.text()).split(",")),
            "Categories": set(str(self.ui.genre_category.text()).split(","))
        }

        text = []
        duplicates = {}

        for name, words in word_sets.iteritems():
            for word in words:
                word = word.strip().title()
                duplicates.setdefault(word, []).append(name)

        for word, names in duplicates.iteritems():
            if len(names) > 1:
                names = "%s and %s" % (", ".join(names[:-1]), names.pop())
                text.append('"%s" in %s lists.' % (word, names))

        if not text:
            text = "No issues found."
        else:
            text = "\n\n".join(text)

        # Display results in information box
        QtGui.QMessageBox.information(self, self.tr("QMessageBox.showInformation()"), text)

    # load/reload defaults
    def load_defaults(self):
        self.ui.genre_major.setText(", ".join(GENRE_FILTER["major"]))
        self.ui.genre_minor.setText(", ".join(GENRE_FILTER["minor"]))
        self.ui.genre_decade.setText(", ".join(GENRE_FILTER["decade"]))
        self.ui.genre_country.setText(", ".join(GENRE_FILTER["country"]))
        self.ui.genre_city.setText(", ".join(GENRE_FILTER["city"]))
        self.ui.genre_year.setText(", ".join(GENRE_FILTER["year"]))
        self.ui.genre_occasion.setText(", ".join(GENRE_FILTER["occasion"]))
        self.ui.genre_category.setText(", ".join(GENRE_FILTER["category"]))
        self.ui.genre_mood.setText(", ".join(GENRE_FILTER["mood"]))
        self.ui.genre_translations.setText("00s, 2000s\n10s, 1910s\n1920's, 1920s\n1930's, 1930s\n1940's, 1940s\n1950's, 1950s\n1960's, 1960s\n1970's, 1970s\n1980's, 1980s\n1990's, 1990s\n2-tone, 2 tone\n20's, 1920s\n2000's, 2000s\n2000s, 2000s\n20s, 1920s\n20th century classical, classical\n30's, 1930s\n30s, 1930s\n3rd wave ska revival, ska\n40's, 1940s\n40s, 1940s\n50's, 1950s\n50s, 1950s\n60's, 1960s\n60s, 1960s\n70's, 1970s\n70s, 1970s\n80's, 1980s\n80s, 1980s\n90's, 1990s\n90s, 1990s\na capella, a cappella\nabstract-hip-hop, hip-hop\nacapella, a cappella\nacid-rock, acid rock\nafrica, african\naggresive, angry\naggressive, angry\nalone, lonely\nalready-dead, deceased\nalt rock, alternative rock\nalt-country, alternative country\nalternative  punk, punk\nalternative dance, dance\nalternative hip-hop, hip-hop\nalternative pop-rock, pop rock\nalternative punk, punk\nalternative rap, rap\nambient-techno, ambient\namericain, american\namericana, american\nanimal-songs, animal songs\nanimals, animal songs\nanti-war, protest\narena rock, rock\natmospheric-drum-and-bass, drum and bass\nau, australian\naussie hip hop, aussie hip-hop\naussie hiphop, aussie hip-hop\naussie rock, australian\naussie, australian\naussie-rock, rock\naustralia, australian\naustralian aboriginal, world\naustralian country, country\naustralian hip hop, aussie hip-hop\naustralian hip-hop, aussie hip-hop\naustralian rap, aussie hip-hop\naustralian rock, rock\naustralian-music, australian\naustralianica, australian\naustralicana, australian\naustria, austrian\navantgarde, avant-garde\nbakersfield-sound, bakersfield\nbaroque pop, baroque\nbeach music, beach\nbeat, beats\nbelgian music, belgian\nbelgian-music, belgian\nbelgium, belgian\nbhangra, indian\nbig beat, beats\nbigbeat, beats\nbittersweet, cynical\nblack metal, doom metal\nblue, sad\nblues guitar, blues\nblues-rock, blues rock\nbluesrock, blues rock\nbollywood, indian\nboogie, boogie woogie\nboogiewoogieflu, boogie woogie\nbrazil, brazilian\nbreakbeats, breakbeat\nbreaks artists, breakbeat\nbrit, british\nbrit-pop, brit pop\nbrit-rock, brit rock\nbritish blues, blues\nbritish punk, punk\nbritish rap, rap\nbritish rock, brit rock\nbritish-folk, folk\nbritpop, brit pop\nbritrock, brit rock\nbroken beat, breakbeat\nbrutal-death-metal, doom metal\nbubblegum, bubblegum pop\nbuddha bar, chillout\ncalming, relaxed\ncanada, canadian\ncha-cha, cha cha\ncha-cha-cha, cha cha\nchicago blues, blues\nchildren, kids\nchildrens music, kids\nchildrens, kids\nchill out, chillout\nchill-out, chillout\nchilled, chill\nchillhouse, chill\nchillin, hanging out\nchristian, gospel\nchina, chinese\nclasica, classical\nclassic blues, blues\nclassic jazz, jazz\nclassic metal, metal\nclassic pop, pop\nclassic punk, punk\nclassic roots reggae, roots reggae\nclassic soul, soul\nclassic-hip-hop, hip-hop\nclassical crossover, classical\nclassical music, classical\nclassics, classic tunes\nclassique, classical\nclub-dance, dance\nclub-house, house\nclub-music, club\ncollegiate acappella, a cappella\ncomedy rock, humour\ncomedy, humour\ncomposer, composers\nconscious reggae, reggae\ncontemporary classical, classical\ncontemporary gospel, gospel\ncontemporary jazz, jazz\ncontemporary reggae, reggae\ncool-covers, covers\ncountry folk, country\ncountry soul, country\ncountry-divas, country\ncountry-female, country\ncountry-legends, country\ncountry-pop, country pop\ncountry-rock, country rock\ncover, covers\ncover-song, covers\ncover-songs, covers\ncowboy, country\ncowhat-fav, country\ncowhat-hero, country\ncuba, cuban\ncyberpunk, punk\nd'n'b, drum and bass\ndance party, party\ndance-punk, punk\ndance-rock, rock\ndancefloor, dance\ndancehall-reggae, dancehall\ndancing, dance\ndark-psy, psytrance\ndark-psytrance, psytrance\ndarkpsy, dark ambient\ndeath metal, doom metal\ndeathcore, thrash metal\ndeep house, house\ndeep-soul, soul\ndeepsoul, soul\ndepressing, depressed\ndepressive, depressed \ndeutsch, german\ndisco-funk, disco\ndisco-house, disco\ndiva, divas\ndj mix, dj\ndnb, drum and bass\ndope, drugs\ndownbeat, downtempo\ndream dance, trance\ndream trance, trance\ndrill 'n' bass, drum and bass\ndrill and bass, drum and bass\ndrill n bass, drum and bass\ndrill-n-bass, drum and bass\ndrillandbass, drum and bass\ndrinking songs, drinking\ndriving-music, driving\ndrum 'n' bass, drum and bass\ndrum n bass, drum and bass\ndrum'n'bass, drum and bass\ndrum, drums\ndrum-n-bass, drum and bass\ndrumandbass, drum and bass\ndub-u, dub\ndub-u-dub, dub\ndub-wise, dub\nduet, duets\nduo, duets\ndutch artists, dutch\ndutch rock, rock\ndutch-bands, dutch\ndutch-sound, dutch\nearly reggae, reggae\neasy, easy listening\negypt, egyptian\neighties, 1980s\nelectro dub, electro\nelectro funk, electro\nelectro house, house\nelectro rock, electro\nelectro-pop, electro\nelectroclash, electro\nelectrofunk, electro\nelectrohouse, house\nelectronic, electronica\nelectronic-rock, rock\nelectronicadance, dance\nelectropop, electro pop\nelectropunk, punk\nelegant, stylish\nelektro, electro\nelevator, elevator music\nemotive, emotional\nenergy, energetic\nengland, british\nenglish, british\nenraged, angry\nepic-trance, trance\nethnic fusion, ethnic\neuro-dance, eurodance\neuro-pop, europop\neuro-trance, trance\neurotrance, trance\neurovision, eurodance\nexperimental-rock, experimental\nfair dinkum australian mate, australian\nfeel good music, feel good\nfeelgood, feel good\nfemale artists, female\nfemale country, country\nfemale fronted, female\nfemale singers, female\nfemale vocalist, female vocalists\nfemale-vocal, female vocalists\nfemale-vocals, female vocalists\nfemale-voices, female vocalists\nfield recording, field recordings\nfilm, film score\nfilm-score, film score\nfingerstyle guitar, fingerstyle\nfinland, finnish\nfinnish-metal, metal\nflamenco rumba, rumba\nfolk-jazz, folk jazz\nfolk-pop, folk pop\nfolk-rock, folk rock\nfolkrock, folk rock\nfrancais, french\nfrance, french\nfreestyle, electronica\nfull on, energetic\nfull-on, energetic\nfull-on-psychedelic-trance, psytrance\nfull-on-trance, trance\nfullon, intense \nfuneral, death\nfunky breaks, breaks\nfunky house, house\nfunny, humorous\ngabber, hardcore\ngeneral pop, pop\ngeneral rock, rock\ngentle, smooth\ngermany, german\ngirl-band, girl group\ngirl-group, girl group\ngirl-groups, girl group\ngirl-power, girl group\ngirls, girl group\nglam metal, glam rock\nglam, glam rock\ngloomy, depressed\ngoa classic, goa trance\ngoa, goa trance\ngoa-psy-trance, psytrance\ngoatrance, trance\ngolden oldies, oldies\ngoth rock, gothic rock\ngoth, gothic\ngothic doom metal, gothic metal\ngreat-lyricists, great lyrics\ngreat-lyrics, great lyrics\ngrime, dubstep\ngregorian chant, gregorian\ngrock 'n' roll, rock and roll\ngroovin, groovy\ngrunge rock, grunge\nguitar god, guitar\nguitar gods, guitar\nguitar hero, guitar\nguitar rock, rock\nguitar-solo, guitar solo\nguitar-virtuoso, guitarist\nhair metal, glam rock\nhanging-out, hanging out\nhappiness, happy\nhappy thoughts, happy\nhard dance, dance\nhard house, house\nhard-trance, trance\nhardcore-techno, techno\nhawaii, hawaiian\nheartbreak, heartache\nheavy rock, hard rock\nhilarious, humorous\nhip hop, hip-hop\nhip-hop and rap, hip-hop\nhip-hoprap, hip-hop\nhiphop, hip-hop\nhippie, stoner rock\nhope, hopeful\nhorrorcore, thrash metal\nhorrorpunk, horror punk\nhumor, humour\nindia, indian\nindie electronic, electronica\nindietronica, electronica\ninspirational, inspiring\ninstrumental pop, instrumental \niran, iranian\nireland, irish\nisrael, israeli\nitaly, italian\njam band, jam\njamaica, jamaican\njamaican ska, ska\njamaician, jamaican\njamaican-artists, jamaican\njammer, jam\njazz blues, jazz\njazz funk, jazz\njazz hop, jazz\njazz piano, jazz\njpop, j-pop\njrock, j-rock\njazz rock, jazz\njazzy, jazz\njump blues, blues\nkiwi, new zealand\nlaid back, easy listening\nlatin rock, latin\nlatino, latin\nle rap france, french rap\nlegend, legends\nlegendary, legends\nlekker ska, ska\nlions-reggae-dancehall, dancehall\nlistless, irritated\nlively, energetic\nlove metal, metal\nlove song, romantic\nlove-songs, lovesongs\nlovely, beautiful\nmade-in-usa, american\nmakes me happy, happy\nmale country, country\nmale groups, male\nmale rock, male\nmale solo artists, male\nmale vocalist, male vocalists\nmale-vocal, male vocalists\nmale-vocals, male vocalists\nmarijuana, drugs\nmelancholic days, melancholy\nmelodic death metal, doom metal\nmelodic hardcore, hardcore\nmelodic metal, metal\nmelodic metalcore, metal\nmelodic punk, punk\nmelodic trance, trance\nmetalcore, thrash metal\nmetro downtempo, downtempo\nmetro reggae, reggae\nmiddle east, middle eastern\nminimal techno, techno\nmood, moody\nmorning, wake up\nmoses reggae, reggae\nmovie, soundtracks\nmovie-score, soundtracks\nmovie-score-composers, composers\nmovie-soundtrack, soundtracks\nmusical, musicals\nmusical-theatre, musicals\nneder rock, rock \nnederland, dutch\nnederlands, dutch\nnederlandse-muziek, dutch\nnederlandstalig, dutch\nnederpop, pop\nnederrock, rock\nnederska, ska\nnedertop, dutch\nneo prog, progressive\nneo progressive rock, progressive rock\nneo progressive, progressive\nneo psychedelia, psychedelic\nneo soul, soul\nnerd rock, rock\nnetherlands, dutch\nneurofunk, funk\nnew rave, rave\nnew school breaks, breaks \nnew school hardcore, hardcore\nnew traditionalist country, traditional country\nnice elevator music, elevator music\nnight, late night\nnight-music, late night\nnoise pop, pop\nnoise rock, rock\nnorway, norwegian\nnostalgic, nostalgia\nnu breaks, breaks\nnu jazz, jazz\nnu skool breaks, breaks \nnu-metal, nu metal\nnumber-songs, number songs\nnumbers, number songs\nnumetal, metal\nnz, new zealand\nold country, country\nold school hardcore, hardcore \nold school hip-hop, hip-hop\nold school reggae, reggae\nold school soul, soul\nold-favorites, oldie\nold-skool, old school\nold-timey, oldie\noldschool, old school\none hit wonder, one hit wonders\noptimistic, positive\noutlaw country, country\noz hip hop, aussie hip-hop\noz rock, rock\noz, australian\nozzie, australian\npancaribbean, caribbean\nparodies, parody\nparty-groovin, party\nparty-music, party\nparty-time, party\npiano rock, piano\npolitical punk, punk\npolitical rap, rap\npool party, party\npop country, country pop\npop music, pop\npop rap, rap\npop-rap, rap\npop-rock, pop rock\npop-soul, pop soul\npoprock, pop rock\nportugal, portuguese\npositive-vibrations, positive\npost grunge, grunge\npost hardcore, hardcore\npost-grunge, grunge\npost-hardcore, hardcore\npost-punk, post punk\npost-rock, post rock\npostrock, post rock\npower ballad, ballad\npower ballads, ballad\npower metal, metal\nprog rock, progressive rock\nprogressive breaks, breaks\nprogressive house, house\nprogressive metal, nu metal\nprogressive psytrance, psytrance \nprogressive trance, psytrance\nproto-punk, punk\npsy, psytrance\npsy-trance, psytrance\npsybient, ambient\npsych folk, psychedelic folk\npsych, psytrance\npsychadelic, psychedelic\npsychedelia, psychedelic\npsychedelic pop, psychedelic\npsychedelic trance, psytrance\npsychill, psytrance\npsycho, insane\npsytrance artists, psytrance\npub rock, rock \npunk blues, punk\npunk caberet, punk\npunk favorites, punk \npunk pop, punk\npunk revival, punk\npunkabilly, punk\npunkrock, punk rock\nqueer, quirky\nquiet, relaxed\nr and b, r&b\nr'n'b, r&b\nr-n-b, r&b\nraggae, reggae\nrap and hip-hop, rap\nrap hip-hop, rap\nrap rock, rap\nrapcore, rap metal\nrasta, rastafarian\nrastafari, rastafarian\nreal hip-hop, hip-hop\nreegae, reggae\nreggae and dub, reggae\nreggae broeder, reggae\nreggae dub ska, reggae\nreggae roots, roots reggae\nreggae-pop, reggae pop\nreggea, reggae\nrelax, relaxed\nrelaxing, relaxed\nrhythm and blues, r&b\nrnb, r&b\nroad-trip, driving\nrock ballad, ballad\nrock ballads, ballad\nrock n roll, rock and roll\nrock pop, pop rock\nrock roll, rock and roll\nrock'n'roll, rock and roll\nrock-n-roll, rock and roll\nrocknroll, rock and roll\nrockpop, pop rock\nromance, romantic\nromantic-tension, romantic\nroots and culture, roots\nroots rock, rock\nrootsreggae, roots reggae \nrussian alternative, russian\nsad-songs, sad\nsample, samples\nsaturday night, party\nsax, saxophone\nscotland, scottish\nseden, swedish\nsensual, passionate\nsing along, sing-alongs\nsing alongs, sing-alongs\nsing-along, sing-alongs\nsinger-songwriters, singer-songwriter\nsingersongwriter, singer-songwriter\nsixties, 1960s\nska revival, ska \nska-punk, ska punk\nskacore, ska\nskate punk, punk\nskinhead reggae, reggae\nsleepy, sleep\nslow jams, slow jam\nsmooth soul, soul\nsoft, smooth\nsolo country acts, country\nsolo instrumental, solo instrumentals\nsoothing, smooth\nsoulful drum and bass, drum and bass\nsoundtrack, soundtracks\nsouth africa, african\nsouth african, african\nsouthern rap, rap\nsouthern soul, soul\nspain, spanish\nspeed metal, metal\nspeed, drugs\nspirituals, spiritual\nspliff, drugs\nstoner, stoner rock\nstreet punk, punk\nsuicide, death\nsuicide, suicidal\nsummertime, summer\nsun-is-shining, sunny\nsunshine pop, pop\nsuper pop, pop\nsurf, surf rock\nswamp blues, swamp rock\nswamp, swamp rock\nsweden, swedish\nswedish metal, metal\nsymphonic power metal, symphonic metal\nsynthpop, synth pop\ntexas blues, blues\ntexas country, country\nthird wave ska revival, ska\nthird wave ska, ska\ntraditional-ska, ska\ntrancytune, trance\ntranquility, peaceful\ntribal house, tribal\ntribal rock, tribal\ntrip hop, trip-hop\ntriphop, trip-hop\ntwo tone, 2 tone\ntwo-tone, 2 tone\nuk hip-hop, hip-hop\nuk, british\nunited kingdom, british\nunited states, american\nuntimely-death, deceased\nuplifting trance, trance\nus, american\nusa, american\nvocal house, house\nvocal jazz, jazz vocal\nvocal pop, pop\nvocal, vocals\nwales, welsh\nweed, drugs\nwest-coast, westcoast\nworld music, world\nxmas, christmas\n")


    def import_newlist(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,
                                         self.tr("QFileDialog.getOpenFileName()"),
                                         self.ui.fileName.text(),
                                         self.tr("All Files (*);;Text Files (*.txt)"))
        if not fileName.isEmpty():
            self.ui.fileName.setText(fileName)
        columns = []
        lists = {}
        for line in open(fileName):
            data = line.rstrip('\r\n').split(",")
            if not columns:  # first line
                columns = tuple(data)
                for column in columns:
                    lists[column] = []
            else:  # data lines
                for column, value in zip(columns, data):
                    if value:
                        lists[column].append(value)
        self.ui.genre_major.setText(', '.join(lists['Major']))
        self.ui.genre_minor.setText(', '.join(lists['Minor']))
        self.ui.genre_country.setText(', '.join(lists['Country']))
        self.ui.genre_city.setText(', '.join(lists['City']))
        self.ui.genre_decade.setText(', '.join(lists['Decade']))
        self.ui.genre_mood.setText(', '.join(lists['Mood']))
        self.ui.genre_occasion.setText(', '.join(lists['Occasion']))

    # Function to create simple report window.  Could do a count of values in
    # each section and the amount of translations. Total tags being scanned
    # for.
    def create_report(self):
        cfg = self.config.setting
        options = [
            ('lastfm_genre_major', 'Major Genre Terms'),
            ('lastfm_genre_minor', 'Minor Genre Terms'),
            ('lastfm_genre_country', 'Country Terms'),
            ('lastfm_genre_city', 'City Terms'),
            ('lastfm_genre_mood', 'Mood Terms'),
            ('lastfm_genre_occasion', 'Occasions Terms'),
            ('lastfm_genre_decade', 'Decade Terms'),
            ('lastfm_genre_year', 'Year Terms'),
            ('lastfm_genre_category', 'Category Terms'),
            ('lastfm_genre_translations', 'Translation Terms'),
        ]
        text = []
        for name, label in options:
            nterms = cfg[name].count(',') + 1
            if nterms:
                text.append(" &bull; %d %s" % (nterms, label))
        if not text:
            text = "No terms found"
        else:
            text = "You have a total of:<br />" + "<br />".join(text) + ""
        # Display results in information box
        QtGui.QMessageBox.information(self, self.tr("QMessageBox.showInformation()"), text)

    def load(self):
        # general
        cfg = self.config.setting
        self.ui.max_minor_tags.setValue(cfg["lastfm_max_minor_tags"])
        self.ui.max_group_tags.setValue(cfg["lastfm_max_group_tags"])
        self.ui.max_mood_tags.setValue(cfg["lastfm_max_mood_tags"])
        self.ui.max_occasion_tags.setValue(cfg["lastfm_max_occasion_tags"])
        self.ui.max_category_tags.setValue(cfg["lastfm_max_category_tags"])
        self.ui.use_country_tag.setChecked(cfg["lastfm_use_country_tag"])
        self.ui.use_city_tag.setChecked(cfg["lastfm_use_city_tag"])
        self.ui.use_decade_tag.setChecked(cfg["lastfm_use_decade_tag"])
        self.ui.use_year_tag.setChecked(cfg["lastfm_use_year_tag"])
        self.ui.join_tags_sign.setText(cfg["lastfm_join_tags_sign"])
        self.ui.app_major2minor_tag.setChecked(cfg["lastfm_app_major2minor_tag"])
        self.ui.use_track_tags.setChecked(cfg["lastfm_use_track_tags"])
        self.ui.min_tracktag_weight.setValue(cfg["lastfm_min_tracktag_weight"])
        self.ui.max_tracktag_drop.setValue(cfg["lastfm_max_tracktag_drop"])
        self.ui.artist_tag_us_no.setChecked(cfg["lastfm_artist_tag_us_no"])
        self.ui.artist_tag_us_ex.setChecked(cfg["lastfm_artist_tag_us_ex"])
        self.ui.artist_tag_us_yes.setChecked(cfg["lastfm_artist_tag_us_yes"])
        self.ui.artist_tags_weight.setValue(cfg["lastfm_artist_tags_weight"])
        self.ui.min_artisttag_weight.setValue(cfg["lastfm_min_artisttag_weight"])
        self.ui.max_artisttag_drop.setValue(cfg["lastfm_max_artisttag_drop"])
        self.ui.genre_major.setText(   cfg["lastfm_genre_major"].replace(",", ", ") )
        self.ui.genre_minor.setText(   cfg["lastfm_genre_minor"].replace(",", ", ") )
        self.ui.genre_decade.setText( cfg["lastfm_genre_decade"].replace(",", ", ") )
        self.ui.genre_country.setText(cfg["lastfm_genre_country"].replace(",", ", ") )
        self.ui.genre_city.setText(cfg["lastfm_genre_city"].replace(",", ", ") )
        self.ui.genre_year.setText( cfg["lastfm_genre_year"].replace(",", ", ") )
        self.ui.genre_occasion.setText(cfg["lastfm_genre_occasion"].replace(",", ", ") )
        self.ui.genre_category.setText(cfg["lastfm_genre_category"].replace(",", ", ") )
        self.ui.genre_year.setText(cfg["lastfm_genre_year"].replace(",", ", ") )
        self.ui.genre_mood.setText(   cfg["lastfm_genre_mood"].replace(",", ", ") )
        self.ui.genre_translations.setText(cfg["lastfm_genre_translations"].replace(",", ", ") )

    def save(self):
        self.config.setting["lastfm_max_minor_tags"] = self.ui.max_minor_tags.value()
        self.config.setting["lastfm_max_group_tags"] = self.ui.max_group_tags.value()
        self.config.setting["lastfm_max_mood_tags"] = self.ui.max_mood_tags.value()
        self.config.setting["lastfm_max_occasion_tags"] = self.ui.max_occasion_tags.value()
        self.config.setting["lastfm_max_category_tags"] = self.ui.max_category_tags.value()
        self.config.setting["lastfm_use_country_tag"] = self.ui.use_country_tag.isChecked()
        self.config.setting["lastfm_use_city_tag"] = self.ui.use_city_tag.isChecked()
        self.config.setting["lastfm_use_decade_tag"] = self.ui.use_decade_tag.isChecked()
        self.config.setting["lastfm_use_year_tag"] = self.ui.use_year_tag.isChecked()
        self.config.setting["lastfm_join_tags_sign"] = self.ui.join_tags_sign.text()
        self.config.setting["lastfm_app_major2minor_tag"] = self.ui.app_major2minor_tag.isChecked()
        self.config.setting["lastfm_use_track_tags"] = self.ui.use_track_tags.isChecked()
        self.config.setting["lastfm_min_tracktag_weight"] = self.ui.min_tracktag_weight.value()
        self.config.setting["lastfm_max_tracktag_drop"] = self.ui.max_tracktag_drop.value()
        self.config.setting["lastfm_artist_tag_us_no"] = self.ui.artist_tag_us_no.isChecked()
        self.config.setting["lastfm_artist_tag_us_ex"] = self.ui.artist_tag_us_ex.isChecked()
        self.config.setting["lastfm_artist_tag_us_yes"] = self.ui.artist_tag_us_yes.isChecked()
        self.config.setting["lastfm_artist_tags_weight"] = self.ui.artist_tags_weight.value()
        self.config.setting["lastfm_min_artisttag_weight"] = self.ui.min_artisttag_weight.value()
        self.config.setting["lastfm_max_artisttag_drop"] = self.ui.max_artisttag_drop.value()

        # parse littlebit the text-inputs
        tmp0 = {}
        tmp1 = [tmp0.setdefault(i.strip(),i.strip()) for i in unicode(self.ui.genre_major.text()).lower().split(",") if i not in tmp0]
        tmp1.sort()
        self.config.setting["lastfm_genre_major"] = ",".join(tmp1)
        tmp0 = {}
        tmp1 = [tmp0.setdefault(i.strip(),i.strip()) for i in unicode(self.ui.genre_minor.text()).lower().split(",") if i not in tmp0]
        tmp1.sort()
        self.config.setting["lastfm_genre_minor"] = ",".join(tmp1)
        tmp0 = {}
        tmp1 = [tmp0.setdefault(i.strip(),i.strip()) for i in unicode(self.ui.genre_decade.text()).lower().split(",") if i not in tmp0]
        tmp1.sort()
        self.config.setting["lastfm_genre_decade"] = ",".join(tmp1)
        tmp0 = {}
        tmp1 = [tmp0.setdefault(i.strip(),i.strip()) for i in unicode(self.ui.genre_year.text()).lower().split(",") if i not in tmp0]
        tmp1.sort()
        self.config.setting["lastfm_genre_year"] = ",".join(tmp1)
        tmp0 = {}
        tmp1 = [tmp0.setdefault(i.strip(),i.strip()) for i in unicode(self.ui.genre_country.text()).lower().split(",") if i not in tmp0]
        tmp1.sort()
        self.config.setting["lastfm_genre_country"] = ",".join(tmp1)
        tmp0 = {}
        tmp1 = [tmp0.setdefault(i.strip(),i.strip()) for i in unicode(self.ui.genre_city.text()).lower().split(",") if i not in tmp0]
        tmp1.sort()
        self.config.setting["lastfm_genre_city"] = ",".join(tmp1)
        tmp0 = {}
        tmp1 = [tmp0.setdefault(i.strip(),i.strip()) for i in unicode(self.ui.genre_occasion.text()).lower().split(",") if i not in tmp0]
        tmp1.sort()
        self.config.setting["lastfm_genre_occasion"] = ",".join(tmp1)
        tmp0 = {}
        tmp1 = [tmp0.setdefault(i.strip(),i.strip()) for i in unicode(self.ui.genre_category.text()).lower().split(",") if i not in tmp0]
        tmp1.sort()
        self.config.setting["lastfm_genre_category"] = ",".join(tmp1)
        tmp0 = {}
        tmp1 = [tmp0.setdefault(i.strip(),i.strip()) for i in unicode(self.ui.genre_mood.text()).lower().split(",") if i not in tmp0]
        tmp1.sort()
        self.config.setting["lastfm_genre_mood"] = ",".join(tmp1)

        trans = {}
        tmp0=unicode(self.ui.genre_translations.toPlainText()).lower().split("\n")
        for tmp1 in tmp0:
            tmp2=tmp1.split(',')
            if len(tmp2) == 2:
                tmp2[0]=tmp2[0].strip()
                tmp2[1]=tmp2[1].strip()
                if len(tmp2[0]) < 1 or len(tmp2[1]) < 1: continue
                if tmp2[0] in trans and trans[tmp2[0]] <> tmp2[1]: del trans[tmp2[0]]
                elif not tmp2[0] in trans: trans[tmp2[0]] = tmp2[1]

        tmp3 = trans.items()
        tmp3.sort()
        self.config.setting["lastfm_genre_translations"] = "\n".join(["%s,%s" % (k,v) for k, v in tmp3])
        GENRE_FILTER["_loaded_"] = False


register_track_metadata_processor(process_track)
register_options_page(LastfmOptionsPage)