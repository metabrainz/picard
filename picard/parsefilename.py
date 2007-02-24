import re

_patterns = [
    # AlbumArtist/1999 - Album/01-TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<artist>.*)(/|\\)((?P<year>\d{4}) - )(?P<album>.*)(/|\\)(?P<tracknum>\d{2})-(?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist - Album/01 - TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<artist>.*) - (?P<album>.*)(/|\\)(?P<tracknum>\d{2}) - (?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist - Album/01-TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<artist>.*) - (?P<album>.*)(/|\\)(?P<tracknum>\d{2})-(?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist - Album/01. TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<artist>.*) - (?P<album>.*)(/|\\)(?P<tracknum>\d{2})\. (?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist - Album/01 TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<artist>.*) - (?P<album>.*)(/|\\)(?P<tracknum>\d{2}) (?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist - Album/01_Artist_-_TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<albumartist>.*) - (?P<album>.*)(/|\\)(?P<tracknum>\d{2})_(?P<artist>.*)_-_(?P<title>.*)\.(?:\w{2,5})$"),
    # Album/Artist - Album - 01 - TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<artist>.*)(/|\\)(?P=artist) - (?P<album>.*) - (?P<tracknum>\d{2}) - (?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist/Album/Artist - 01 - TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<albumartist>.*)(/|\\)(?P<album>.*)(/|\\)(?P<artist>.*) - (?P<tracknum>\d{2}) - (?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist/Album/01. Artist - TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<albumartist>.*)(/|\\)(?P<album>.*)(/|\\)(?P<tracknum>\d{2})\. (?P<artist>.*) - (?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist/Album/01 - Artist - TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<albumartist>.*)(/|\\)(?P<album>.*)(/|\\)(?P<tracknum>\d{2}) - (?P<artist>.*) - (?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist/Album/01 - TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<artist>.*)(/|\\)(?P<album>.*)(/|\\)(?P<tracknum>\d{2}) - (?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist/Album/01. TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<artist>.*)(/|\\)(?P<album>.*)(/|\\)(?P<tracknum>\d{2})\. (?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist/Album/01 TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<artist>.*)(/|\\)(?P<album>.*)(/|\\)(?P<tracknum>\d{2}) (?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist/Album/Album-01-TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<albumartist>.*)(/|\\)(?P<album>.*)(/|\\)(?P=album)-(?P<tracknum>\d{2})-(?P<artist>.*)-(?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist/Album/Album-01-Artist-TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<artist>.*)(/|\\)(?P<album>.*)(/|\\)(?P=album)-(?P<tracknum>\d{2})-(?P<title>.*)\.(?:\w{2,5})$"),
    # AlbumArtist/Album/Artist-01-TrackTitle.ext
    re.compile(r"(?:.*(/|\\))?(?P<albumartist>.*)(/|\\)(?P<album>.*)(/|\\)(?P<artist>.*)-(?P<tracknum>\d{2})-(?P<title>.*)\.(?:\w{2,5})$"),
]

def parseFileName(filename, metadata):
    for pattern in _patterns:
        match = pattern.match(filename)
        if match:
            metadata["artist"] = match.group("artist")
            metadata["title"] = match.group("title")
            metadata["album"] = match.group("album")

if __name__ == "__main__":
    # Thanks to folks at http://www.last.fm/group/Get%2BYour%2BDamn%2BTags%2BRight/forum/13179/_/99927 :)
    testCases = [
        (u"F:\\Hudba\\2 Unlimited\\No Limit\\01 No Limit.mp3", u"2 Unlimited", u"No Limit", u"No Limit"),
        (u"F:\\Hudba\\2 Unlimited\\No Limit\\No Limit-01-No Limit.mp3", u"2 Unlimited", u"No Limit", u"No Limit"),
        (u"F:\\Hudba\\2 Unlimited\\No Limit\\No Limit-01-Test-No Limit.mp3", u"Test", u"No Limit", u"No Limit"),
        (u"F:\\grooves\\Brian Eno - Another Green World (1975)\\08 - Sombre Reptiles.ogg", u"Brian Eno", u"Another Green World (1975)", u"Sombre Reptiles"),
        (u"My Documents/Music/Various Artists/Album/01 - Artist - Track.ogg", u"Artist", u"Album", u"Track"),
        (u"M:\\Albums\\Artist\\Album\\artist - 01 - title.mp3", u"artist", u"Album", u"title"),
        (u"F:\\artist\\(year) album\\01 - title.mp3", u"artist", u"(year) album", u"title"),
        (u"/home/blaster/Data/Audio/Music/Deep Purple/[2003] Bananas/01 - Deep Purple - House of Pain.ogg", u"Deep Purple", u"[2003] Bananas", u"House of Pain"),
        (u"\\A\\A Perfect Circle\\(2000) Mer De Noms\\01 - The Hollow.mp3", u"A Perfect Circle", u"(2000) Mer De Noms", u"The Hollow"),
        (u"..\\My Music\\Metal\\Sonata Arctica\\Sonata Arctica - Successor - 05 - Shy.mp3", u"Sonata Arctica", u"Successor", u"Shy"),
        (u"D:\\Music\\Artist - Album (year)\\01_artist_-_trackname.mp3", u"artist", u"Album (year)", u"trackname"),
        (u"root/MP3/Band/Album/band-01-name.mp3", u"band", u"Album", u"name"),
        #(u"D:\\Music\\accPlus 64kb\\Artist\\Year - Album\\00 - Title - Artist.acc", u"Artist", u"Year - Album", u"Title"),
        (u"C:\\My Documents\\Media\\Audio\\A\\Autolux\\Future Perfect\\01. Turnstile Blues.mp3", u"Autolux", u"Future Perfect", u"Turnstile Blues"),
        (u"music\\artist\\1999 - Album Name\\01-TrackName.mp3", u"artist", u"Album Name", u"TrackName"),
    ]
    ok = 0
    for testCase in testCases:
        mdata = parseFileName(testCase[0])
        print testCase[0]
        if not mdata:
            print "Error"
        else:
            if mdata.artist != testCase[1]:
                print "Error", "-%s-" % mdata.artist, "-%s-" % testCase[1]
            elif mdata.album != testCase[2]:
                print "Error", "-%s-" % mdata.album, "-%s-" % testCase[2]
            elif mdata.title != testCase[3]:
                print "Error", "-%s-" % mdata.title, "-%s-" % testCase[3]
            else:
                ok += 1
            print "OK"
    print len(testCases), ok

