# Version 2.6.0b2 - 2021-03-06

## Bugfixes

- [PICARD-2131](https://tickets.metabrainz.org/browse/PICARD-2131) - Tagger button reacts slow in Firefox

## Improvements

- [PICARD-2130](https://tickets.metabrainz.org/browse/PICARD-2130) - Restructure cover art options to make them easier to understand


# Version 2.6.0b1 - 2021-03-02

## Bugfixes

- [PICARD-1528](https://tickets.metabrainz.org/browse/PICARD-1528) - "Search for similar albums" causes crashes if the selection includes clusters and files
- [PICARD-1689](https://tickets.metabrainz.org/browse/PICARD-1689) - Freezes when adding tags to large album
- [PICARD-1926](https://tickets.metabrainz.org/browse/PICARD-1926) - "Show changes first" in tag preview window leads to freeze
- [PICARD-2088](https://tickets.metabrainz.org/browse/PICARD-2088) - Picard hangs when adding new tag to multiple tracks in an album
- [PICARD-2091](https://tickets.metabrainz.org/browse/PICARD-2091) - Loading images from cover art via drag and drop from browser only loads PNG and JPEG images
- [PICARD-2097](https://tickets.metabrainz.org/browse/PICARD-2097) - Crash with zh_CN locale
- [PICARD-2113](https://tickets.metabrainz.org/browse/PICARD-2113) - Script can change title of "Unclustered files" special cluster
- [PICARD-2127](https://tickets.metabrainz.org/browse/PICARD-2127) - "Lookup in browser" in metadata box does not pass tagger port

## New Features

- [PICARD-204](https://tickets.metabrainz.org/browse/PICARD-204) - Support for track-level original release date
- [PICARD-1998](https://tickets.metabrainz.org/browse/PICARD-1998) - Add "director" (for videos) tag
- [PICARD-2089](https://tickets.metabrainz.org/browse/PICARD-2089) - Support WebP images for cover art
- [PICARD-2124](https://tickets.metabrainz.org/browse/PICARD-2124) - Add MB release annotation field as `%_releaseannotation%` variable

## Tasks

- [PICARD-715](https://tickets.metabrainz.org/browse/PICARD-715) - Chrome to block browser access to localhost
- [PICARD-1950](https://tickets.metabrainz.org/browse/PICARD-1950) - Fix macOS builds with PyQt > 5.13.2

## Improvements

- [PICARD-2084](https://tickets.metabrainz.org/browse/PICARD-2084) - Use TLS for AcoustID web service requests
- [PICARD-2090](https://tickets.metabrainz.org/browse/PICARD-2090) - Reenable TIFF support for cover art images
- [PICARD-2092](https://tickets.metabrainz.org/browse/PICARD-2092) - Improve script editor function/variable auto completion
- [PICARD-2105](https://tickets.metabrainz.org/browse/PICARD-2105) - Improve script function popup descriptions
- [PICARD-2110](https://tickets.metabrainz.org/browse/PICARD-2110) - Add `%originaldate%` and `%originalyear%` to file naming examples
- [PICARD-2114](https://tickets.metabrainz.org/browse/PICARD-2114) - Show disambiguation comment in CD Lookup popup window
- [PICARD-2125](https://tickets.metabrainz.org/browse/PICARD-2125) - Enable CAA Release Group cover art provider by default
- [PICARD-2126](https://tickets.metabrainz.org/browse/PICARD-2126) - Allow cross origin access to browser integration


# Version 2.5.6 - 2021-01-05

## Bugfixes

- [PICARD-1943](https://tickets.metabrainz.org/browse/PICARD-1943) - App does not start on macOS 10.12 / 10.13, Gatekeeper reports it as damaged
- [PICARD-2074](https://tickets.metabrainz.org/browse/PICARD-2074) - Crash when trying to add new tags
- [PICARD-2083](https://tickets.metabrainz.org/browse/PICARD-2083) - Snap version: path to fpcalc gets invalid after update
- [PICARD-2087](https://tickets.metabrainz.org/browse/PICARD-2087) - Adding new tags crashes Picard with Qt < 5.10


# Version 2.5.5 - 2020-12-17

## Bugfixes

- [PICARD-2070](https://tickets.metabrainz.org/browse/PICARD-2070) - Lookup on cluster only moves every other file
- [PICARD-2071](https://tickets.metabrainz.org/browse/PICARD-2071) - Track listings sometimes in reverse order


# Version 2.5.4 - 2020-12-15

## Bugfixes

- [PICARD-2067](https://tickets.metabrainz.org/browse/PICARD-2067) - 2.5.3 crashes on start on Windows


# Version 2.5.3 - 2020-12-15

## Bugfixes
- [PICARD-2016](https://tickets.metabrainz.org/browse/PICARD-2016) - AcoustID API Key is not stripped
- [PICARD-2017](https://tickets.metabrainz.org/browse/PICARD-2017) - Picard crashes when removing entries on the right side while loading
- [PICARD-2019](https://tickets.metabrainz.org/browse/PICARD-2019) - Saving tracks to SMB share on Windows 10 results in ever more nested folders
- [PICARD-2020](https://tickets.metabrainz.org/browse/PICARD-2020) - Multi-value album or recording ID tags prevent Picard from loading the proper albums
- [PICARD-2021](https://tickets.metabrainz.org/browse/PICARD-2021) - SameFileError when moving files between network path and local path on Windows
- [PICARD-2022](https://tickets.metabrainz.org/browse/PICARD-2022) - Crash accessing network share without access rights on Windows
- [PICARD-2023](https://tickets.metabrainz.org/browse/PICARD-2023) - Appdata file not generated on non-Linux platforms
- [PICARD-2028](https://tickets.metabrainz.org/browse/PICARD-2028) - Deleting albums and saving files is extremely slow
- [PICARD-2031](https://tickets.metabrainz.org/browse/PICARD-2031) - Scripting documentation link 404
- [PICARD-2036](https://tickets.metabrainz.org/browse/PICARD-2036) - MultiMetadataProxy::pop is not flagged as a WRITE_METHOD; this breaks the "keep" plugin
- [PICARD-2037](https://tickets.metabrainz.org/browse/PICARD-2037) - Improve Info/Error tab readability
- [PICARD-2045](https://tickets.metabrainz.org/browse/PICARD-2045) - After fingerprint, unsaved tracks have green tick
- [PICARD-2050](https://tickets.metabrainz.org/browse/PICARD-2050) - File selector pane jumps around horizontally instead of expanding / collapsing the folder
- [PICARD-2056](https://tickets.metabrainz.org/browse/PICARD-2056) - Interface color changes are not saved
- [PICARD-2058](https://tickets.metabrainz.org/browse/PICARD-2058) - Add File dialog does not show files with uppercase extension on case-sensitive file systems
- [PICARD-2059](https://tickets.metabrainz.org/browse/PICARD-2059) - Scripting Documentation shows extra line for each function
- [PICARD-2062](https://tickets.metabrainz.org/browse/PICARD-2062) - Searching for similar tracks can remove current album even if there are unmatched tracks
- [PICARD-2064](https://tickets.metabrainz.org/browse/PICARD-2064) - Cluster shows empty album column

## Improvements
- [PICARD-2034](https://tickets.metabrainz.org/browse/PICARD-2034) - Add context menu entry for copy and paste to metadata view
- [PICARD-2035](https://tickets.metabrainz.org/browse/PICARD-2035) - More verbose tooltip for album error icon
- [PICARD-2038](https://tickets.metabrainz.org/browse/PICARD-2038) - Integrate metadata box clipboard with system clipboard
- [PICARD-2039](https://tickets.metabrainz.org/browse/PICARD-2039) - Unify error handling for albums, non-album tracks and files, show errors in info dialog
- [PICARD-2044](https://tickets.metabrainz.org/browse/PICARD-2044) - Add date and originaldate fields to the choice of columns in the list views
- [PICARD-2046](https://tickets.metabrainz.org/browse/PICARD-2046) - AcoustID submission can fail due to body size limit of AcoustID server
- [PICARD-2047](https://tickets.metabrainz.org/browse/PICARD-2047) - Improve contrast for console text in dark mode
- [PICARD-2057](https://tickets.metabrainz.org/browse/PICARD-2057) - Allow showing all files in Add Files dialog
- [PICARD-2063](https://tickets.metabrainz.org/browse/PICARD-2063) - Add an option to disable automatic horizontal scrolling in file browser


# Version 2.5.2 - 2020-11-15

## Bugfixes
- [PICARD-1948](https://tickets.metabrainz.org/browse/PICARD-1948) - ScaleFactorRoundPolicy breaks text rendering on Linux
- [PICARD-1991](https://tickets.metabrainz.org/browse/PICARD-1991) - Case-only changes to file names are not applied on case insensitive file systems on Linux
- [PICARD-1992](https://tickets.metabrainz.org/browse/PICARD-1992) - Case-only changes to file names are not applied on FAT32 and exFAT file systems on Windows 10
- [PICARD-2001](https://tickets.metabrainz.org/browse/PICARD-2001) - Directory drag & drop from file browser to cluster area broken
- [PICARD-2004](https://tickets.metabrainz.org/browse/PICARD-2004) - Metadata changes loaded asynchronously by plugins are reset if file gets matched to track
- [PICARD-2005](https://tickets.metabrainz.org/browse/PICARD-2005) - Modified fields are sometimes not correctly marked as changed when multiple files are selected
- [PICARD-2006](https://tickets.metabrainz.org/browse/PICARD-2006) - "Local files" cover provider does not detect cover files for files already present at release loading time
- [PICARD-2012](https://tickets.metabrainz.org/browse/PICARD-2012) - Loaded files not shown in UI if release MBID is a redirect
- [PICARD-2014](https://tickets.metabrainz.org/browse/PICARD-2014) - Config upgrade from Picard < 1.3.0 to version 2.4 or later fails

## Improvements
- [PICARD-1828](https://tickets.metabrainz.org/browse/PICARD-1828) - Allow assigning cover art to multiple selected files
- [PICARD-1999](https://tickets.metabrainz.org/browse/PICARD-1999) - Provide binary distributions for Windows and macOS on PyPI
- [PICARD-2007](https://tickets.metabrainz.org/browse/PICARD-2007) - Disable analyze / audio fingerprinting for MIDI files


# Version 2.5.1 - 2020-10-28

## Bugfixes
- [PICARD-1987](https://tickets.metabrainz.org/browse/PICARD-1987) - Special variables `%_multiartist%`, `%_pregap%`, `%_datatrack%` and `%_totalalbumtracks%` missing after files got matched to a track
- [PICARD-1988](https://tickets.metabrainz.org/browse/PICARD-1988) - Aborts if directory scan finds a directory which cannot be read
- [PICARD-1989](https://tickets.metabrainz.org/browse/PICARD-1989) - Auto-sizing does not work right on first column
- [PICARD-1990](https://tickets.metabrainz.org/browse/PICARD-1990) - Case-only changes to file names are not applied on Windows if running with Python >= 3.8

## Improvements
- [PICARD-1985](https://tickets.metabrainz.org/browse/PICARD-1985) - Support chorus master recording relationships as "performer:chorus master" instead of second conductor
- [PICARD-1995](https://tickets.metabrainz.org/browse/PICARD-1995) - Add command line parameter `--no-player` to disable media player
- [PICARD-1997](https://tickets.metabrainz.org/browse/PICARD-1997) - Reduce performance impact of fingerprinting column


# Version 2.5 - 2020-10-22

## Bugfixes
- [PICARD-214](https://tickets.metabrainz.org/browse/PICARD-214) - Take case insensitive file systems into account when renaming files
- [PICARD-1972](https://tickets.metabrainz.org/browse/PICARD-1972) - Times missing in bottom panel
- [PICARD-1973](https://tickets.metabrainz.org/browse/PICARD-1973) - Multi-value tags getting flattened when files get matched to tracks
- [PICARD-1974](https://tickets.metabrainz.org/browse/PICARD-1974) - Picard crashes when using the same tag name more than once in "Tags from File Names..."
- [PICARD-1975](https://tickets.metabrainz.org/browse/PICARD-1975) - Tags from file names does not properly set hidden tags
- [PICARD-1976](https://tickets.metabrainz.org/browse/PICARD-1976) - Cover art providers do not handle URLs with query arguments correctly
- [PICARD-1979](https://tickets.metabrainz.org/browse/PICARD-1979) - Comment tag in MP4 not saved correctly
- [PICARD-1982](https://tickets.metabrainz.org/browse/PICARD-1982) - Cover art not saving properly

## Improvements
- [PICARD-1978](https://tickets.metabrainz.org/browse/PICARD-1978) - Add keyboard shortcut for Tags From Filenames and allow to place it in toolbar


# Version 2.5.0b1 - 2020-10-15

## Bugfixes
- [PICARD-1858](https://tickets.metabrainz.org/browse/PICARD-1858) - MusicBrainz Picard does not respond on macOS 11 Big Sur Beta
- [PICARD-1882](https://tickets.metabrainz.org/browse/PICARD-1882) - Scripting text not well readable with dark theme on KDE
- [PICARD-1888](https://tickets.metabrainz.org/browse/PICARD-1888) - Returning tracks to cluster uses matched release rather than what's in the files
- [PICARD-1932](https://tickets.metabrainz.org/browse/PICARD-1932) - Failed AcoustID submission shows as successful
- [PICARD-1939](https://tickets.metabrainz.org/browse/PICARD-1939) - Crash when "Remove" button is hit without picking a file first
- [PICARD-1941](https://tickets.metabrainz.org/browse/PICARD-1941) - Unchanged multi-value tags on tracks show up as changed
- [PICARD-1954](https://tickets.metabrainz.org/browse/PICARD-1954) - Right-clicking on album with "could not load album" message crashes
- [PICARD-1956](https://tickets.metabrainz.org/browse/PICARD-1956) - It is possible to have the same file multiple times inside the same cluster
- [PICARD-1961](https://tickets.metabrainz.org/browse/PICARD-1961) - Capitalization for non-standardized instruments
- [PICARD-1963](https://tickets.metabrainz.org/browse/PICARD-1963) - Possible stack overflow when loading files
- [PICARD-1964](https://tickets.metabrainz.org/browse/PICARD-1964) - Scripting documentation does not support RTL languages
- [PICARD-1969](https://tickets.metabrainz.org/browse/PICARD-1969) - Browser integration port changes without saving options
- [PICARD-1971](https://tickets.metabrainz.org/browse/PICARD-1971) - Tags from file names dialog does not restore window size

## New Features
- [PICARD-259](https://tickets.metabrainz.org/browse/PICARD-259) - Make file-specific variables and metadata available to tagger script
- [PICARD-534](https://tickets.metabrainz.org/browse/PICARD-534) - Support SOCKS proxy
- [PICARD-1908](https://tickets.metabrainz.org/browse/PICARD-1908) - Allow loading release group URLs / MBIDs
- [PICARD-1942](https://tickets.metabrainz.org/browse/PICARD-1942) - Display tracklist in Info dialog for loaded releases
- [PICARD-1946](https://tickets.metabrainz.org/browse/PICARD-1946) - Map "vocal arranger" rel to arranger tag

## Improvements
- [PICARD-1390](https://tickets.metabrainz.org/browse/PICARD-1390) - Apply a network timeout to avoid network requests hanging indefinitely
- [PICARD-1782](https://tickets.metabrainz.org/browse/PICARD-1782) - Allow locking table headers to prevent accidental resorting
- [PICARD-1879](https://tickets.metabrainz.org/browse/PICARD-1879) - When dragging tracks onto a release add those tracks sequentially
- [PICARD-1906](https://tickets.metabrainz.org/browse/PICARD-1906) - Clarify uninstall message in Windows installer
- [PICARD-1936](https://tickets.metabrainz.org/browse/PICARD-1936) - Rename the "Whitelist" cover art provider to "Allowed Cover Art URLs"
- [PICARD-1937](https://tickets.metabrainz.org/browse/PICARD-1937) - Add context menu entry to cover art box to browse for local file
- [PICARD-1938](https://tickets.metabrainz.org/browse/PICARD-1938) - Add context menu option to load files / folders from file browser
- [PICARD-1951](https://tickets.metabrainz.org/browse/PICARD-1951) - Avoid complete hiding of metadata box or file panes
- [PICARD-1952](https://tickets.metabrainz.org/browse/PICARD-1952) - Allow using native Qt styles on Linux
- [PICARD-1955](https://tickets.metabrainz.org/browse/PICARD-1955) - Use built-in search by default for new installs
- [PICARD-1957](https://tickets.metabrainz.org/browse/PICARD-1957) - Load files in file browser on double click
- [PICARD-1958](https://tickets.metabrainz.org/browse/PICARD-1958) - macOS: Offer link to Applications folder in disk image
- [PICARD-1959](https://tickets.metabrainz.org/browse/PICARD-1959) - In disc ID dialog rename "Lookup in Browser" to "Submit disc ID"
- [PICARD-1960](https://tickets.metabrainz.org/browse/PICARD-1960) - Allow adding new items in list editor views using Insert key
- [PICARD-1965](https://tickets.metabrainz.org/browse/PICARD-1965) - Allow opening fingerprinting options in AcoustID missing API key dialog

## Tasks
- [PICARD-1929](https://tickets.metabrainz.org/browse/PICARD-1929) - Make NSIS installer translations available on Transifex


# Version 2.4.4 - 2020-09-04

## Bugfixes
- [PICARD-1931](https://tickets.metabrainz.org/browse/PICARD-1931) - Regression: "Unmatched Files" do not appear when release was deleted from MB


# Version 2.4.3 - 2020-09-04

## Bugfixes
- [PICARD-1916](https://tickets.metabrainz.org/browse/PICARD-1916) - Picard crashes on older releases of macOS due to theming exception
- [PICARD-1918](https://tickets.metabrainz.org/browse/PICARD-1918) - Saving files fails if there is no front image and "Save only one front image as separate file" is enabled
- [PICARD-1921](https://tickets.metabrainz.org/browse/PICARD-1921) - Windows 10: With dark theme inactive checkboxes cannot be distinguished from active ones
- [PICARD-1928](https://tickets.metabrainz.org/browse/PICARD-1928) - After clustering fingerprint icon disappears
- [PICARD-1931](https://tickets.metabrainz.org/browse/PICARD-1931) - Regression: "Unmatched Files" do not appear when release was deleted from MB

## Improvements
- [PICARD-1935](https://tickets.metabrainz.org/browse/PICARD-1935) - Include tests in PyPI sdist tarball


# Version 2.4.2 - 2020-08-18

## Bugfixes
- [PICARD-1909](https://tickets.metabrainz.org/browse/PICARD-1909) - No refresh of metadata on "Use Original Value" or remove tags
- [PICARD-1911](https://tickets.metabrainz.org/browse/PICARD-1911) - Removing tags does not update list views
- [PICARD-1913](https://tickets.metabrainz.org/browse/PICARD-1913) - Changing tags of a track without matched files changes original metadata
- [PICARD-1914](https://tickets.metabrainz.org/browse/PICARD-1914) - Editing track metadata edits data of previously linked file
- [PICARD-1915](https://tickets.metabrainz.org/browse/PICARD-1915) - An album selected during loading should update the metadata view when loading has finished
- [PICARD-1916](https://tickets.metabrainz.org/browse/PICARD-1916) - Picard crashes on older releases of macOS due to theming exception

## Improvements
- [PICARD-1860](https://tickets.metabrainz.org/browse/PICARD-1860) - New added tag should open field to enter value automatically
- [PICARD-1899](https://tickets.metabrainz.org/browse/PICARD-1899) - Update help links to go to http://picard-docs.musicbrainz.org
- [PICARD-1920](https://tickets.metabrainz.org/browse/PICARD-1920) - Open documentation in options dialog using the platform's help shortcut (e.g. F1 on Windows or Ctrl+? on macOS)


# Version 2.4.1 - 2020-08-11

## Bugfixes
- [PICARD-1904](https://tickets.metabrainz.org/browse/PICARD-1904) - Picard 2.4 does not start on Windows 7 and Windows 8


# Version 2.4 - 2020-08-10

## Bugfixes
- [PICARD-1763](https://tickets.metabrainz.org/browse/PICARD-1763) - App does not start on macOS 10.13 High Sierra
- [PICARD-1873](https://tickets.metabrainz.org/browse/PICARD-1873) - Scripting documentation uses an ugly font on Windows
- [PICARD-1881](https://tickets.metabrainz.org/browse/PICARD-1881) - Function names in script documentation not readable with dark theme
- [PICARD-1884](https://tickets.metabrainz.org/browse/PICARD-1884) - No tracknumber tag if track number is 0
- [PICARD-1889](https://tickets.metabrainz.org/browse/PICARD-1889) - "Use track relationships" is including release relationships
- [PICARD-1890](https://tickets.metabrainz.org/browse/PICARD-1890) - User is warned about color changes when exiting options, even if no change was made
- [PICARD-1891](https://tickets.metabrainz.org/browse/PICARD-1891) - Crash parsing bad date in metadata
- [PICARD-1892](https://tickets.metabrainz.org/browse/PICARD-1892) - Deleting "Total Tracks" or "Total Discs" from Vorbis tags causes save to fail
- [PICARD-1894](https://tickets.metabrainz.org/browse/PICARD-1894) - Detecting track number from filename wrongly detects leading or trailing numbers
- [PICARD-1896](https://tickets.metabrainz.org/browse/PICARD-1896) - Instrument arranger is not being mapped for tagging using the correct key
- [PICARD-1902](https://tickets.metabrainz.org/browse/PICARD-1902) - Crash when typing `$noop(\)` in the script editor

## New Features
- [PICARD-1128](https://tickets.metabrainz.org/browse/PICARD-1128) - Support Microsoft WAVE format (RIFF/WAVE) tagging with ID3
- [PICARD-1839](https://tickets.metabrainz.org/browse/PICARD-1839) - Support DSDIFF (DFF) files

## Improvements
- [PICARD-1812](https://tickets.metabrainz.org/browse/PICARD-1812) - Support RIFF INFO chunks for WAVE files
- [PICARD-1871](https://tickets.metabrainz.org/browse/PICARD-1871) - Use tag list editor for preserved tags
- [PICARD-1875](https://tickets.metabrainz.org/browse/PICARD-1875) - Improve function documentation for `$firstalphachar`
- [PICARD-1878](https://tickets.metabrainz.org/browse/PICARD-1878) - Inefficient reading of tracks leads to slow saving on some file systems and network shares
- [PICARD-1880](https://tickets.metabrainz.org/browse/PICARD-1880) - Use Consolas font on Windows for monospace font (script editor, log view etc.)
- [PICARD-1887](https://tickets.metabrainz.org/browse/PICARD-1887) - On macOS use dark syntax theme if dark mode is enabled (currently only when running from source)


# Version 2.4.0b2 - 2020-07-05

## Bugfixes
- [PICARD-1864](https://tickets.metabrainz.org/browse/PICARD-1864) - Adding single files does ignore existing MBIDs
- [PICARD-1866](https://tickets.metabrainz.org/browse/PICARD-1866) - Coverart pane does not update during / after saving files
- [PICARD-1867](https://tickets.metabrainz.org/browse/PICARD-1867) - Guess format fallback is broken
- [PICARD-1868](https://tickets.metabrainz.org/browse/PICARD-1868) - CAA type selection dialog does not translate "Unknown"


# Version 2.4.0b1 - 2020-07-01

## Bugfixes
- [PICARD-1753](https://tickets.metabrainz.org/browse/PICARD-1753) - Fix font size of script editor and log view on Windows
- [PICARD-1807](https://tickets.metabrainz.org/browse/PICARD-1807) - Wrong error handling when using python-libdiscid
- [PICARD-1813](https://tickets.metabrainz.org/browse/PICARD-1813) - `$title` function throws error on empty value
- [PICARD-1820](https://tickets.metabrainz.org/browse/PICARD-1820) - PLUGIN_VERSION no longer displayed correctly in plugins dialog
- [PICARD-1823](https://tickets.metabrainz.org/browse/PICARD-1823) - Genre tag ordering is non-deterministic
- [PICARD-1826](https://tickets.metabrainz.org/browse/PICARD-1826) - "no appropriate stream found" when saving .ogg (OPUS) file
- [PICARD-1838](https://tickets.metabrainz.org/browse/PICARD-1838) - Files with a .dff file extension are interpreted as DSF files and fail to load
- [PICARD-1853](https://tickets.metabrainz.org/browse/PICARD-1853) - Crash if tags contain null character
- [PICARD-1855](https://tickets.metabrainz.org/browse/PICARD-1855) - Relationships not tagged for non-album track
- [PICARD-1859](https://tickets.metabrainz.org/browse/PICARD-1859) - "ValueError: Invalid literal" followed by crash when opening certain files

## New Features
- [PICARD-1704](https://tickets.metabrainz.org/browse/PICARD-1704) - Support Windows 10 dark mode
- [PICARD-1797](https://tickets.metabrainz.org/browse/PICARD-1797) - Autocompletion for script functions and variables
- [PICARD-1798](https://tickets.metabrainz.org/browse/PICARD-1798) - Add support for inline translatable documentation

## Improvements
- [PICARD-824](https://tickets.metabrainz.org/browse/PICARD-824) - Expand all option submenus by default
- [PICARD-920](https://tickets.metabrainz.org/browse/PICARD-920) - Remember selected options page
- [PICARD-1117](https://tickets.metabrainz.org/browse/PICARD-1117) - Instrumental recordings of a work should set language to "No lyrics"
- [PICARD-1796](https://tickets.metabrainz.org/browse/PICARD-1796) - Consider release date when matching files to releases
- [PICARD-1805](https://tickets.metabrainz.org/browse/PICARD-1805) - Make it easier to add the first script
- [PICARD-1818](https://tickets.metabrainz.org/browse/PICARD-1818) - Make PyQt5.QtDBus optional
- [PICARD-1829](https://tickets.metabrainz.org/browse/PICARD-1829) - Add support for disc numbers in cluster Info dialog tracklists
- [PICARD-1831](https://tickets.metabrainz.org/browse/PICARD-1831) - Mitigate performance impacts of file selection and UI updates during processing
- [PICARD-1840](https://tickets.metabrainz.org/browse/PICARD-1840) - Instrumental recordings of a work should drop the lyricist credit
- [PICARD-1842](https://tickets.metabrainz.org/browse/PICARD-1842) - AIFF and DSF: Add support for albumsort, artistsort, titlesort and discsubtitle
- [PICARD-1843](https://tickets.metabrainz.org/browse/PICARD-1843) - Improve load and clustering performance
- [PICARD-1844](https://tickets.metabrainz.org/browse/PICARD-1844) - Further improve loading and clustering performance
- [PICARD-1845](https://tickets.metabrainz.org/browse/PICARD-1845) - Add "lookup in browser" for musicbrainz_discid tag in metadata view
- [PICARD-1846](https://tickets.metabrainz.org/browse/PICARD-1846) - Metadata.unset should not raise KeyError
- [PICARD-1847](https://tickets.metabrainz.org/browse/PICARD-1847) - Restructure tag compatibility options
- [PICARD-1852](https://tickets.metabrainz.org/browse/PICARD-1852) - Make about a separate dialog
- [PICARD-1854](https://tickets.metabrainz.org/browse/PICARD-1854) - Improve sorting performance in main window
- [PICARD-1856](https://tickets.metabrainz.org/browse/PICARD-1856) - Use pgettext function in Python 3.8


# Version 2.3.2 - 2020-05-06

## Bugfixes
- [PICARD-1775](https://tickets.metabrainz.org/browse/PICARD-1775) - `$firstwords` function doesn't catch IndexError
- [PICARD-1776](https://tickets.metabrainz.org/browse/PICARD-1776) - `$datetime` crashes when invalid format specified
- [PICARD-1781](https://tickets.metabrainz.org/browse/PICARD-1781) - Have `$find` return "" rather than "-1" on not found
- [PICARD-1783](https://tickets.metabrainz.org/browse/PICARD-1783) - Deleting performer, comment or lyrics tag fails for some cases in ID3, Vorbis, MP4 and Apev2 tags
- [PICARD-1784](https://tickets.metabrainz.org/browse/PICARD-1784) - Host not found error when downloading PDF artwork
- [PICARD-1785](https://tickets.metabrainz.org/browse/PICARD-1785) - `$delete(_id3:TXXX:foo)` does not delete the ID3 frames
- [PICARD-1786](https://tickets.metabrainz.org/browse/PICARD-1786) - Deleting tag stored in ID3 TIPL frame only removes first occurrence
- [PICARD-1787](https://tickets.metabrainz.org/browse/PICARD-1787) - Deleting case-insensitive TXXX frames does not delete anything
- [PICARD-1788](https://tickets.metabrainz.org/browse/PICARD-1788) - Saving ID3 tags marked as case-insensitive causes duplicated TXXX frames
- [PICARD-1790](https://tickets.metabrainz.org/browse/PICARD-1790) - Crash when selecting plugin that can be updated
- [PICARD-1791](https://tickets.metabrainz.org/browse/PICARD-1791) - Network access is disabled error under VPN service
- [PICARD-1795](https://tickets.metabrainz.org/browse/PICARD-1795) - iTunes tags not removable (reappear after being deleted)
- [PICARD-1801](https://tickets.metabrainz.org/browse/PICARD-1801) - List index out of range when saving Vorbis file
- [PICARD-1803](https://tickets.metabrainz.org/browse/PICARD-1803) - Instrument EWI is rewritten "e w i"

## Improvements
- [PICARD-1777](https://tickets.metabrainz.org/browse/PICARD-1777) - Support fractional scaling on Windows 10
- [PICARD-1800](https://tickets.metabrainz.org/browse/PICARD-1800) - Simplify Unicode 'Bullet' to ASCII 'Hyphen-minus'
- [PICARD-1809](https://tickets.metabrainz.org/browse/PICARD-1809) - Optimize format detection logic


# Version 2.3.1 - 2020-02-27

## Bugfixes
- [PICARD-1745](https://tickets.metabrainz.org/browse/PICARD-1745) - Packaged libdiscid is not compatible with macOS 10.12
- [PICARD-1748](https://tickets.metabrainz.org/browse/PICARD-1748) - Many release events can cause the versions context menu to overflow
- [PICARD-1750](https://tickets.metabrainz.org/browse/PICARD-1750) - Existing acoustid_fingerprint tags are not considered for AcoustID submission
- [PICARD-1754](https://tickets.metabrainz.org/browse/PICARD-1754) - DEL always removes release or file from main window
- [PICARD-1756](https://tickets.metabrainz.org/browse/PICARD-1756) - Plugin update fails to compare plugin versions with double digit versions
- [PICARD-1757](https://tickets.metabrainz.org/browse/PICARD-1757) - Crash on loading a release if `$div(n,0)` is used in a script
- [PICARD-1760](https://tickets.metabrainz.org/browse/PICARD-1760) - Prevent duplicates in top tags editor
- [PICARD-1762](https://tickets.metabrainz.org/browse/PICARD-1762) - Dropping a PDF file on cover art image box doesn't work
- [PICARD-1765](https://tickets.metabrainz.org/browse/PICARD-1765) - Adding uppercase tags to preserved tags list is not handled correctly
- [PICARD-1772](https://tickets.metabrainz.org/browse/PICARD-1772) - Unexpected results with `$num` function
- [PICARD-1773](https://tickets.metabrainz.org/browse/PICARD-1773) - Untrapped error on `$mod` with zero input
- [PICARD-1774](https://tickets.metabrainz.org/browse/PICARD-1774) - `$lenmulti` with missing name returns "1"

## New Features
- [PICARD-1743](https://tickets.metabrainz.org/browse/PICARD-1743) - Add script functions `$sortmulti` and `$reversemulti` to sort and reverse multi-value variables
- [PICARD-1751](https://tickets.metabrainz.org/browse/PICARD-1751) - Provide a `%_releasecountries%` variable

## Improvements
- [PICARD-1746](https://tickets.metabrainz.org/browse/PICARD-1746) - Change Generate AcoustID Fingerprints shortcut to Ctrl+Shift+Y / ⌘⇧Y
- [PICARD-1752](https://tickets.metabrainz.org/browse/PICARD-1752) - Use preferred release countries to select a matching release country if there are multiple
- [PICARD-1755](https://tickets.metabrainz.org/browse/PICARD-1755) - "Supported Languages" on Microsoft Store shows only English (United States)
- [PICARD-1759](https://tickets.metabrainz.org/browse/PICARD-1759) - Make editing tags in top tags list more intuitive
- [PICARD-1771](https://tickets.metabrainz.org/browse/PICARD-1771) - Completely ignore release types set to zero in preferred releases


# Version 2.3 - 2020-02-17

## Bugfixes
- [PICARD-1739](https://tickets.metabrainz.org/browse/PICARD-1739) - Update check does not handle alpha, beta and rc versions properly
- [PICARD-1744](https://tickets.metabrainz.org/browse/PICARD-1744) - Invalid ignore path regex can crash Picard

## Improvements
- [PICARD-1740](https://tickets.metabrainz.org/browse/PICARD-1740) - Save originalfilename to ASF tags


# Version 2.3.0rc1 - 2020-02-11

## Bugfixes
- [PICARD-1688](https://tickets.metabrainz.org/browse/PICARD-1688) - "Submit AcoustIDs" fails with many tracks
- [PICARD-1719](https://tickets.metabrainz.org/browse/PICARD-1719) - `$unset` marks tag for deletion
- [PICARD-1724](https://tickets.metabrainz.org/browse/PICARD-1724) - Fingerprint status on left should not be submittable (red)
- [PICARD-1725](https://tickets.metabrainz.org/browse/PICARD-1725) - Fingerprint indicator rendering artifacts
- [PICARD-1726](https://tickets.metabrainz.org/browse/PICARD-1726) - Crash when closing options quickly before plugin list got loaded
- [PICARD-1727](https://tickets.metabrainz.org/browse/PICARD-1727) - Performer tag in metadata list is not translated
- [PICARD-1733](https://tickets.metabrainz.org/browse/PICARD-1733) - App does not start on macOS 10.12
- [PICARD-1736](https://tickets.metabrainz.org/browse/PICARD-1736) - "Generate AcoustID Fingerprints" is too long for the toolbar

## Improvements
- [PICARD-1716](https://tickets.metabrainz.org/browse/PICARD-1716) - Add script functions for strings (`$find`, `$reverse`, `$substr`), multi-value variables (`$getmulti`), and loops (`$foreach`, `$while`, `$map`)
- [PICARD-1717](https://tickets.metabrainz.org/browse/PICARD-1717) - Backup config file on update
- [PICARD-1720](https://tickets.metabrainz.org/browse/PICARD-1720) - Add script function `$slice` to extract a portion of a multi-value variable
- [PICARD-1721](https://tickets.metabrainz.org/browse/PICARD-1721) - Add script function `$join` to join the elements of a multi-value variable
- [PICARD-1723](https://tickets.metabrainz.org/browse/PICARD-1723) - Match to album should consider the disc number
- [PICARD-1729](https://tickets.metabrainz.org/browse/PICARD-1729) - Add scripting function `$datetime` to return the current date and time
- [PICARD-1737](https://tickets.metabrainz.org/browse/PICARD-1737) - Add keyboard shortcut Ctrl+Alt+F for "Generate Fingerprints"
- [PICARD-1738](https://tickets.metabrainz.org/browse/PICARD-1738) - Load a recording URL entered into the search field as standalone recording


# Version 2.3.0b1 - 2020-01-30

## Bugfixes
- [PICARD-239](https://tickets.metabrainz.org/browse/PICARD-239) - Using tag "comment" should behave the same as "comment:" (with colon) in tagger script
- [PICARD-965](https://tickets.metabrainz.org/browse/PICARD-965) - Items in tagger scripts list are squished
- [PICARD-1054](https://tickets.metabrainz.org/browse/PICARD-1054) - Picard swallows values of Qt command line arguments
- [PICARD-1218](https://tickets.metabrainz.org/browse/PICARD-1218) - Script names aren't truncated properly
- [PICARD-1312](https://tickets.metabrainz.org/browse/PICARD-1312) - Hotkeys for buttons do not work on macOS
- [PICARD-1565](https://tickets.metabrainz.org/browse/PICARD-1565) - Picard ignores results in Acoust ID web service response
- [PICARD-1592](https://tickets.metabrainz.org/browse/PICARD-1592) - APEv2: Read tags case insensitive
- [PICARD-1625](https://tickets.metabrainz.org/browse/PICARD-1625) - UI unresponsive while matching files to release
- [PICARD-1626](https://tickets.metabrainz.org/browse/PICARD-1626) - Locales in Options > Metadata are not translated and not sorted
- [PICARD-1629](https://tickets.metabrainz.org/browse/PICARD-1629) - Duration for AAC files with APEv2 tags is wrong
- [PICARD-1658](https://tickets.metabrainz.org/browse/PICARD-1658) - macOS: System wide libdiscid is used instead of the bundled one
- [PICARD-1662](https://tickets.metabrainz.org/browse/PICARD-1662) - Issue saving FLAC with large (~ 16 MiB) embedded images
- [PICARD-1664](https://tickets.metabrainz.org/browse/PICARD-1664) - Cluster lookup does not use preferred release types
- [PICARD-1667](https://tickets.metabrainz.org/browse/PICARD-1667) - Some scripting functions are always true
- [PICARD-1668](https://tickets.metabrainz.org/browse/PICARD-1668) - Read fails if mp4 file has "disk" tag set but empty
- [PICARD-1675](https://tickets.metabrainz.org/browse/PICARD-1675) - Allow disabling auto update for Windows builds
- [PICARD-1678](https://tickets.metabrainz.org/browse/PICARD-1678) - Picard crashes if result from search server contains non-integer scores
- [PICARD-1693](https://tickets.metabrainz.org/browse/PICARD-1693) - Position and size of log view and activity history are not preserved
- [PICARD-1699](https://tickets.metabrainz.org/browse/PICARD-1699) - On scan asking the user to enable the fingerprinting does always abort the scan
- [PICARD-1700](https://tickets.metabrainz.org/browse/PICARD-1700) - Crash with PyQt5 when opening cover art context menu
- [PICARD-1709](https://tickets.metabrainz.org/browse/PICARD-1709) - Saving AIFF files can make them unreadable (requires mutagen >= 1.43)
- [PICARD-1711](https://tickets.metabrainz.org/browse/PICARD-1711) - Cannot delete lyrics from ASF, ID3, MP4 and APE files

## New Features
- [PICARD-34](https://tickets.metabrainz.org/browse/PICARD-34) - Add a fingerprint indicator
- [PICARD-118](https://tickets.metabrainz.org/browse/PICARD-118) - Windows: Provide a portable Picard version
- [PICARD-125](https://tickets.metabrainz.org/browse/PICARD-125) - Support for AC3
- [PICARD-170](https://tickets.metabrainz.org/browse/PICARD-170) - Allow selecting displayed columns
- [PICARD-714](https://tickets.metabrainz.org/browse/PICARD-714) - Allow user to reorder fields in the lower pane
- [PICARD-991](https://tickets.metabrainz.org/browse/PICARD-991) - Allow calculating AcoustID fingerprints for matched recordings
- [PICARD-1098](https://tickets.metabrainz.org/browse/PICARD-1098) - MP4: Support custom tags
- [PICARD-1521](https://tickets.metabrainz.org/browse/PICARD-1521) - Make Picard recognize "TOFN (Original Filename)" ID3 tag
- [PICARD-1656](https://tickets.metabrainz.org/browse/PICARD-1656) - Allow setting cover art for clusters
- [PICARD-1673](https://tickets.metabrainz.org/browse/PICARD-1673) - Show progress in Windows taskbar
- [PICARD-1674](https://tickets.metabrainz.org/browse/PICARD-1674) - Show progress in Linux docks / taskbar supporting the Unity.LauncherEntry DBus interface
- [PICARD-1677](https://tickets.metabrainz.org/browse/PICARD-1677) - Option to ignore tags for file changed status
- [PICARD-1684](https://tickets.metabrainz.org/browse/PICARD-1684) - Allow re-ordering multi-value tags

## Improvements
- [PICARD-115](https://tickets.metabrainz.org/browse/PICARD-115) - Display 'YYYY', 'MM' and 'DD' in date input field when value not available
- [PICARD-321](https://tickets.metabrainz.org/browse/PICARD-321) - Backslash support in filenames if Windows compatibility is disabled
- [PICARD-1260](https://tickets.metabrainz.org/browse/PICARD-1260) - Sort entries in Clusters more "naturally"
- [PICARD-1349](https://tickets.metabrainz.org/browse/PICARD-1349) - Change the sorting by clicking on a column title so that it switches through three states (sort ascending/descending/not at all)
- [PICARD-1401](https://tickets.metabrainz.org/browse/PICARD-1401) - CD Lookup dialog does not make it clear how to submit a disc ID
- [PICARD-1402](https://tickets.metabrainz.org/browse/PICARD-1402) - macOS: Register for supported file types to open with Finder or drag and drop on dock icon
- [PICARD-1467](https://tickets.metabrainz.org/browse/PICARD-1467) - Provide signed Windows installer
- [PICARD-1523](https://tickets.metabrainz.org/browse/PICARD-1523) - Make Picard case-agnostic for "Preserve tags from being cleared"
- [PICARD-1589](https://tickets.metabrainz.org/browse/PICARD-1589) - Support language for ID3 COMM tags with `comment:{language}:{description}` syntax (enables support for MediaMonkey's Songs-DB_Custom tags)
- [PICARD-1628](https://tickets.metabrainz.org/browse/PICARD-1628) - Make APEv2 tags with AAC optional
- [PICARD-1631](https://tickets.metabrainz.org/browse/PICARD-1631) - Notarize macOS app
- [PICARD-1646](https://tickets.metabrainz.org/browse/PICARD-1646) - Respect preferred release types when scanning tracks
- [PICARD-1650](https://tickets.metabrainz.org/browse/PICARD-1650) - Select / load multiple items from search results
- [PICARD-1652](https://tickets.metabrainz.org/browse/PICARD-1652) - Support extended info for TAK files (requires mutagen >= 1.43)
- [PICARD-1659](https://tickets.metabrainz.org/browse/PICARD-1659) - Natural sorting for search results
- [PICARD-1661](https://tickets.metabrainz.org/browse/PICARD-1661) - Improve preserved tags autocomplete
- [PICARD-1665](https://tickets.metabrainz.org/browse/PICARD-1665) - Disable uninstall for globally installed plugins
- [PICARD-1666](https://tickets.metabrainz.org/browse/PICARD-1666) - Consider video / audio when comparing files to tracks
- [PICARD-1671](https://tickets.metabrainz.org/browse/PICARD-1671) - Rework Options > Tags page
- [PICARD-1672](https://tickets.metabrainz.org/browse/PICARD-1672) - MP4: Use hdvd atom to detect videos (requires mutagen >= 1.43)
- [PICARD-1680](https://tickets.metabrainz.org/browse/PICARD-1680) - Select / load multiple items from CD lookup results
- [PICARD-1682](https://tickets.metabrainz.org/browse/PICARD-1682) - Multiline editing for lyrics and comments
- [PICARD-1683](https://tickets.metabrainz.org/browse/PICARD-1683) - Autocompletion when editing media, releasetype, releasecountry and releasestatus tags
- [PICARD-1686](https://tickets.metabrainz.org/browse/PICARD-1686) - Always keep [non-album tracks] entry on top
- [PICARD-1692](https://tickets.metabrainz.org/browse/PICARD-1692) - Change sliders to jump to clicked position
- [PICARD-1695](https://tickets.metabrainz.org/browse/PICARD-1695) - Make script editor UI consistent with other option pages
- [PICARD-1712](https://tickets.metabrainz.org/browse/PICARD-1712) - Use Ctrl+D as keyboard shortcut to remove albums or files
- [PICARD-1714](https://tickets.metabrainz.org/browse/PICARD-1714) - Focus search input with Ctrl+F
- [PICARD-1715](https://tickets.metabrainz.org/browse/PICARD-1715) - Allow changing file extension by manipulating the `%_extension%` variable in renaming script

## Tasks
- [PICARD-1406](https://tickets.metabrainz.org/browse/PICARD-1406) - Refactor `Metadata.set` and `Metadata.__setitem__`
- [PICARD-1465](https://tickets.metabrainz.org/browse/PICARD-1465) - Add Picard to Windows Store
- [PICARD-1596](https://tickets.metabrainz.org/browse/PICARD-1596) - Automate PyPI deployment
- [PICARD-1653](https://tickets.metabrainz.org/browse/PICARD-1653) - macOS: Enable Hardened Runtime
- [PICARD-1669](https://tickets.metabrainz.org/browse/PICARD-1669) - Build Windows 10 MSIX app package
- [PICARD-1703](https://tickets.metabrainz.org/browse/PICARD-1703) - Upgrade to PyInstaller 3.6


# Version 2.2.3 - 2019-11-06

## Bugfixes
- [PICARD-1633](https://tickets.metabrainz.org/browse/PICARD-1633) - macOS: Automatic locale detection broken
- [PICARD-1634](https://tickets.metabrainz.org/browse/PICARD-1634) - macOS: File browser sets wrong horizontal scroll position
- [PICARD-1635](https://tickets.metabrainz.org/browse/PICARD-1635) - Terminated randomly when deleting files when saving
- [PICARD-1636](https://tickets.metabrainz.org/browse/PICARD-1636) - Default locale detection fails if locale categories have different locales
- [PICARD-1637](https://tickets.metabrainz.org/browse/PICARD-1637) - Crash when saving after removing some underlying files
- [PICARD-1640](https://tickets.metabrainz.org/browse/PICARD-1640) - Picard with --config-file parameter copies over legacy configuration
- [PICARD-1642](https://tickets.metabrainz.org/browse/PICARD-1642) - Picard crashes on launch (AttributeError: 'NoneType' object has no attribute 'setPopupMode')
- [PICARD-1643](https://tickets.metabrainz.org/browse/PICARD-1643) - Performer with instruments containing non-ASCII characters are not written to Vorbis and APE tags
- [PICARD-1644](https://tickets.metabrainz.org/browse/PICARD-1644) - Crash when initializing translations on Python 3.8
- [PICARD-1647](https://tickets.metabrainz.org/browse/PICARD-1647) - macOS: Plugin enable/disable button does not always update the icon
- [PICARD-1648](https://tickets.metabrainz.org/browse/PICARD-1648) - Crashes when using search dialogs
- [PICARD-1651](https://tickets.metabrainz.org/browse/PICARD-1651) - File and release counts in status bar not updated when files get removed
- [PICARD-1654](https://tickets.metabrainz.org/browse/PICARD-1654) - macOS: Logout button / username stays visible after logout
- [PICARD-1655](https://tickets.metabrainz.org/browse/PICARD-1655) - macOS: Login dialog can be hidden behind options

## Improvements
- [PICARD-1630](https://tickets.metabrainz.org/browse/PICARD-1630) - Ensure FLAC metadata is visible/editable in Windows Explorer
- [PICARD-1632](https://tickets.metabrainz.org/browse/PICARD-1632) - Tooltips for genre filter help hide too quickly


# Version 2.2.2 - 2019-10-08

## Bugfixes
- [PICARD-1606](https://tickets.metabrainz.org/browse/PICARD-1606) - Crashes on opening options with broken plugin
- [PICARD-1612](https://tickets.metabrainz.org/browse/PICARD-1612) - Trackpad tap is not working properly on macOS
- [PICARD-1614](https://tickets.metabrainz.org/browse/PICARD-1614) - macOS: Incorrect 'LSMinimumSystemVersion'
- [PICARD-1618](https://tickets.metabrainz.org/browse/PICARD-1618) - macOS and Windows packages built without C astrcmp
- [PICARD-1621](https://tickets.metabrainz.org/browse/PICARD-1621) - Lookup CD dropdown does not list additional drives
- [PICARD-1624](https://tickets.metabrainz.org/browse/PICARD-1624) - Updating default CD device in options does not change default for keyboard shortcut

## Improvements
- [PICARD-1610](https://tickets.metabrainz.org/browse/PICARD-1610) - Make the labels in Options > User Interface > Colours wider
- [PICARD-1619](https://tickets.metabrainz.org/browse/PICARD-1619) - Grey out cover art providers list when cover art is disabled


# Version 2.2.1 - 2019-09-20

## Bugfixes
- [PICARD-1603](https://tickets.metabrainz.org/browse/PICARD-1603) - Translations from picard/ui/colors.py don’t show up in Picard
- [PICARD-1604](https://tickets.metabrainz.org/browse/PICARD-1604) - Windows install is not using Qt default translations
- [PICARD-1607](https://tickets.metabrainz.org/browse/PICARD-1607) - Upgrading a plugin displays the dialog box multiple times
- [PICARD-1608](https://tickets.metabrainz.org/browse/PICARD-1608) - "[non-album tracks]" can not directly be removed
- [PICARD-1609](https://tickets.metabrainz.org/browse/PICARD-1609) - Picard About shows Qt version PyQt was build against, not actually used Qt

## Improvements
- [PICARD-1602](https://tickets.metabrainz.org/browse/PICARD-1602) - Tests should not be included in the sdist package


# Version 2.2 - 2019-09-14

## Bugfixes
- [PICARD-456](https://tickets.metabrainz.org/browse/PICARD-456) - "Delete empty directories" should not delete special folders such as the desktop
- [PICARD-571](https://tickets.metabrainz.org/browse/PICARD-571) - Scripting and renaming font on macOS and Windows not monospace
- [PICARD-622](https://tickets.metabrainz.org/browse/PICARD-622) - File Browser resets horizontal scrolling on selection change
- [PICARD-765](https://tickets.metabrainz.org/browse/PICARD-765) - Refreshing a release reloads the CAA index.json file from cache, even if it changed online
- [PICARD-1025](https://tickets.metabrainz.org/browse/PICARD-1025) - An empty destination directory prevents the options from being saved, but doesn't show an error
- [PICARD-1090](https://tickets.metabrainz.org/browse/PICARD-1090) - Match quality indicators are blurry
- [PICARD-1282](https://tickets.metabrainz.org/browse/PICARD-1282) - ⌘W does not close Preferences window
- [PICARD-1284](https://tickets.metabrainz.org/browse/PICARD-1284) - Can't quit with preferences open
- [PICARD-1446](https://tickets.metabrainz.org/browse/PICARD-1446) - Expand/collapse indicator for the release is briefly missing
- [PICARD-1483](https://tickets.metabrainz.org/browse/PICARD-1483) - Can't submit fingerprints to non-album recordings
- [PICARD-1489](https://tickets.metabrainz.org/browse/PICARD-1489) - Crash on start when loading python-discid without libdiscid being available
- [PICARD-1490](https://tickets.metabrainz.org/browse/PICARD-1490) - Local cover art provider fails on Windows
- [PICARD-1491](https://tickets.metabrainz.org/browse/PICARD-1491) - Version check when loading Picard plugins too strict
- [PICARD-1492](https://tickets.metabrainz.org/browse/PICARD-1492) - Can’t save rated tracks when it’s a FLAC file (when Metadata/Ratings is active)
- [PICARD-1493](https://tickets.metabrainz.org/browse/PICARD-1493) - Crash on pre 1.0 config upgrade
- [PICARD-1497](https://tickets.metabrainz.org/browse/PICARD-1497) - Saving fails when setting tags with invalid names for the underlying tagging format
- [PICARD-1499](https://tickets.metabrainz.org/browse/PICARD-1499) - Picard loads embedded cover art with ID3 type "other" as sticker
- [PICARD-1501](https://tickets.metabrainz.org/browse/PICARD-1501) - Double click in a cover opens it in web browser instead of an image viewer
- [PICARD-1503](https://tickets.metabrainz.org/browse/PICARD-1503) - Scanning CDROM uses path containing ampersand (&)
- [PICARD-1516](https://tickets.metabrainz.org/browse/PICARD-1516) - Picard fails to load MP4 without tags
- [PICARD-1517](https://tickets.metabrainz.org/browse/PICARD-1517) - Functions matchedtracks and is_complete throw exception when run on cluster
- [PICARD-1522](https://tickets.metabrainz.org/browse/PICARD-1522) - Crash when removing NAT recordings
- [PICARD-1527](https://tickets.metabrainz.org/browse/PICARD-1527) - Can't resize options window in 2.1.x (Mac)
- [PICARD-1529](https://tickets.metabrainz.org/browse/PICARD-1529) - NAT tracks get assigned wrong cover art
- [PICARD-1533](https://tickets.metabrainz.org/browse/PICARD-1533) - Attribute Qt::AA_EnableHighDpiScaling must be set before QCoreApplication is created
- [PICARD-1541](https://tickets.metabrainz.org/browse/PICARD-1541) - Closing log views destroys widgets
- [PICARD-1543](https://tickets.metabrainz.org/browse/PICARD-1543) - v2.1.3 crashes when selecting Preferences in the Apple menu 10.14.5
- [PICARD-1547](https://tickets.metabrainz.org/browse/PICARD-1547) - Picard doesn't warn about not updating .wav metadata
- [PICARD-1549](https://tickets.metabrainz.org/browse/PICARD-1549) - Source distributions are broken on Windows
- [PICARD-1551](https://tickets.metabrainz.org/browse/PICARD-1551) - "compare_to_track" method considers "score" parameter only if track has releases
- [PICARD-1556](https://tickets.metabrainz.org/browse/PICARD-1556) - Default File Naming Script produces "00" track number in file name.
- [PICARD-1558](https://tickets.metabrainz.org/browse/PICARD-1558) - Setting rating on a track does not apply to already matched files
- [PICARD-1566](https://tickets.metabrainz.org/browse/PICARD-1566) - Cannot drag misidentified song back to the left pane
- [PICARD-1567](https://tickets.metabrainz.org/browse/PICARD-1567) - Parsing track number from file name modifies original title in metadata
- [PICARD-1571](https://tickets.metabrainz.org/browse/PICARD-1571) - On macOS multiple option dialogs can be opened
- [PICARD-1573](https://tickets.metabrainz.org/browse/PICARD-1573) - Crash when loading release with a tag that contains only whitespace.
- [PICARD-1575](https://tickets.metabrainz.org/browse/PICARD-1575) - Can't drag and drop a picture from the Google Picture Result Page to Picard.
- [PICARD-1580](https://tickets.metabrainz.org/browse/PICARD-1580) - Crash when closing options window on "Preferred Releases" page
- [PICARD-1582](https://tickets.metabrainz.org/browse/PICARD-1582) - "Allow selection of multiple directories" has no effect on Linux with Gtk file chooser
- [PICARD-1584](https://tickets.metabrainz.org/browse/PICARD-1584) - Crash when disabling script function providing plugin
- [PICARD-1585](https://tickets.metabrainz.org/browse/PICARD-1585) - On macOS restore default options dialog opens in background
- [PICARD-1588](https://tickets.metabrainz.org/browse/PICARD-1588) - Metadata box shows tags unsupported by format
- [PICARD-1591](https://tickets.metabrainz.org/browse/PICARD-1591) - Error when loading Vorbis file with invalid metadata_block_picture
- [PICARD-1593](https://tickets.metabrainz.org/browse/PICARD-1593) - Picard crashes on plugin install error
- [PICARD-1595](https://tickets.metabrainz.org/browse/PICARD-1595) - Cursor in tag edit box always jumps to end on input
- [PICARD-1598](https://tickets.metabrainz.org/browse/PICARD-1598) - Metadata box hidden when album gets updated
- [PICARD-1601](https://tickets.metabrainz.org/browse/PICARD-1601) - PyPI source tarball misses some test data

## New Features
- [PICARD-143](https://tickets.metabrainz.org/browse/PICARD-143) - Add a plugin hook for a file-added-to-a-track event
- [PICARD-1130](https://tickets.metabrainz.org/browse/PICARD-1130) - Post save plugins
- [PICARD-1488](https://tickets.metabrainz.org/browse/PICARD-1488) - Built-in media player (beta feature)
- [PICARD-1510](https://tickets.metabrainz.org/browse/PICARD-1510) - Add a plugin hook for a file-removed-from-a-track event
- [PICARD-1512](https://tickets.metabrainz.org/browse/PICARD-1512) - Add a plugin hook for an album-removed event
- [PICARD-1514](https://tickets.metabrainz.org/browse/PICARD-1514) - Replace genre / folksonomy tag blacklist with more comprehensive list
- [PICARD-1524](https://tickets.metabrainz.org/browse/PICARD-1524) - Replace hardcoded colors by user-configurable ones
- [PICARD-1560](https://tickets.metabrainz.org/browse/PICARD-1560) - Add a plugin hook for a file loaded event
- [PICARD-1594](https://tickets.metabrainz.org/browse/PICARD-1594) - Provide `$is_video()` / `$is_audio()` scripting functions

## Tasks
- [PICARD-1353](https://tickets.metabrainz.org/browse/PICARD-1353) - Update Travis CI to use newer Xcode
- [PICARD-1388](https://tickets.metabrainz.org/browse/PICARD-1388) - Document how to uninstall local built version of picard from CLI
- [PICARD-1561](https://tickets.metabrainz.org/browse/PICARD-1561) - test_file.TestPreserveTimes fails on macOS 10.14
- [PICARD-1563](https://tickets.metabrainz.org/browse/PICARD-1563) - Add 'picard.egg-info' file to .gitignore

## Improvements
- [PICARD-1235](https://tickets.metabrainz.org/browse/PICARD-1235) - Picard is not responding during start while CD is being inserted
- [PICARD-1361](https://tickets.metabrainz.org/browse/PICARD-1361) - Add "Launch Picard" to Windows installer
- [PICARD-1400](https://tickets.metabrainz.org/browse/PICARD-1400) - Remove Amazon cover art provider from Picard and place it into a plugin
- [PICARD-1468](https://tickets.metabrainz.org/browse/PICARD-1468) - Localize Windows installer
- [PICARD-1485](https://tickets.metabrainz.org/browse/PICARD-1485) - Picard should show the hours of long tracks
- [PICARD-1494](https://tickets.metabrainz.org/browse/PICARD-1494) - Use Python3.3+ nano seconds resolution stat()/utime() to preserve times on file save
- [PICARD-1496](https://tickets.metabrainz.org/browse/PICARD-1496) - Display count of Other versions available once known in album's contextual menu
- [PICARD-1502](https://tickets.metabrainz.org/browse/PICARD-1502) - qApp.setDesktopFileName (wayland app_ip)
- [PICARD-1525](https://tickets.metabrainz.org/browse/PICARD-1525) - Log/History views are updated even if not actually visible
- [PICARD-1546](https://tickets.metabrainz.org/browse/PICARD-1546) - Display in Others submenu is messy for albums with a lot of tracks
- [PICARD-1552](https://tickets.metabrainz.org/browse/PICARD-1552) - "compare_to_release_parts" considers track count of only first medium
- [PICARD-1559](https://tickets.metabrainz.org/browse/PICARD-1559) - Allow moving files to subfolders without renaming
- [PICARD-1564](https://tickets.metabrainz.org/browse/PICARD-1564) - Picard code for parsing response from AcoustID servers ignores tracks
- [PICARD-1576](https://tickets.metabrainz.org/browse/PICARD-1576) - Open option help context sensitive
- [PICARD-1578](https://tickets.metabrainz.org/browse/PICARD-1578) - Allow dragging images from Bing image search result
- [PICARD-1579](https://tickets.metabrainz.org/browse/PICARD-1579) - Dragging cover art from Google image search on Linux drops just preview image
- [PICARD-1581](https://tickets.metabrainz.org/browse/PICARD-1581) - "Recursively add files and folders" is very technical and hard to understand
- [PICARD-1586](https://tickets.metabrainz.org/browse/PICARD-1586) - Support for ReplayGain 2.0 tags
- [PICARD-1599](https://tickets.metabrainz.org/browse/PICARD-1599) - Use fpcalc json output for more robust output parsing


# Version 2.1.3 - 2019-03-03
## Bugfixes
- [PICARD-323](https://tickets.metabrainz.org/browse/PICARD-323) - Only the discid of the first disc in a release is written to tags
- [PICARD-455](https://tickets.metabrainz.org/browse/PICARD-455) - Picard setting cover art height, width and depth to 0 for FLAC files --> breaks libFLAC
- [PICARD-729](https://tickets.metabrainz.org/browse/PICARD-729) - Tracks get stuck at "[loading track information]" on Bad Gateway errors
- [PICARD-938](https://tickets.metabrainz.org/browse/PICARD-938) - Need two left-arrow key presses to go from track with file to album
- [PICARD-1178](https://tickets.metabrainz.org/browse/PICARD-1178) - Images tagged with extra types that the user has chosen to ignore should not be shown as 'modified'
- [PICARD-1288](https://tickets.metabrainz.org/browse/PICARD-1288) - Folskonomy tags / genre fallback on album artists tags not working
- [PICARD-1422](https://tickets.metabrainz.org/browse/PICARD-1422) - Windows: Uninstall 32 bit Picard before upgrade
- [PICARD-1447](https://tickets.metabrainz.org/browse/PICARD-1447) - When releasing a new version, appdata should also be updated
- [PICARD-1460](https://tickets.metabrainz.org/browse/PICARD-1460) - Windows installer does not detect running instance
- [PICARD-1461](https://tickets.metabrainz.org/browse/PICARD-1461) - Crash when running with Spanish language
- [PICARD-1463](https://tickets.metabrainz.org/browse/PICARD-1463) - Picard crashes on startup on Windows
- [PICARD-1469](https://tickets.metabrainz.org/browse/PICARD-1469) - Force close when adding songs to larger albums
- [PICARD-1471](https://tickets.metabrainz.org/browse/PICARD-1471) - Artist searches do not show begin and end area
- [PICARD-1473](https://tickets.metabrainz.org/browse/PICARD-1473) - AcoustId lookup fails if fingerprint already in tags
- [PICARD-1474](https://tickets.metabrainz.org/browse/PICARD-1474) - Windows installer shows outdated version string in file properties
- [PICARD-1475](https://tickets.metabrainz.org/browse/PICARD-1475) - Cover art sources do not support HTTPS
- [PICARD-1476](https://tickets.metabrainz.org/browse/PICARD-1476) - Filled up thread pool prevents metadata box updates
- [PICARD-1478](https://tickets.metabrainz.org/browse/PICARD-1478) - Changing MB server requires a restart
- [PICARD-1480](https://tickets.metabrainz.org/browse/PICARD-1480) - Search line input clear button icon is too small

## Tasks
- [PICARD-1459](https://tickets.metabrainz.org/browse/PICARD-1459) - Remove OptionsPage.info method
- [PICARD-1472](https://tickets.metabrainz.org/browse/PICARD-1472) - macOS code signing on Travis CI fails for xcode7.3 image

## Improvements
- [PICARD-1242](https://tickets.metabrainz.org/browse/PICARD-1242) - Consider the number of AcoustID sources for linked recordings
- [PICARD-1457](https://tickets.metabrainz.org/browse/PICARD-1457) - "Check for Update" should be in the Picard menu
- [PICARD-1458](https://tickets.metabrainz.org/browse/PICARD-1458) - "Check for Update" should have an ellipsis at the end
- [PICARD-1470](https://tickets.metabrainz.org/browse/PICARD-1470) - Make warning about Qt locale loading less prominent


# Version 2.1.2 - 2019-01-29
## Bugfixes
- [PICARD-1382](https://tickets.metabrainz.org/browse/PICARD-1382) - macOS packaging script ignores all errors

## Tasks
- [PICARD-1456](https://tickets.metabrainz.org/browse/PICARD-1456) - macOS packaging fails due to PIP bug


# Version 2.1.1 - 2019-01-29
## Bugfixes
- [PICARD-1451](https://tickets.metabrainz.org/browse/PICARD-1451) - Redirects of authenticated requests fail with 401 error
- [PICARD-1453](https://tickets.metabrainz.org/browse/PICARD-1453) - Dropping events do not work in CoverArtBox
- [PICARD-1454](https://tickets.metabrainz.org/browse/PICARD-1454) - Crashes when adding action to toolbar in options


## Tasks
- [PICARD-1452](https://tickets.metabrainz.org/browse/PICARD-1452) - Appveyor auto-deploy not working

## Improvements
- [PICARD-1450](https://tickets.metabrainz.org/browse/PICARD-1450) - Fix language label for zh_CN and zh_TW


# Version 2.1.0 - 2018-12-20
## Bugfixes
- [PICARD-105](https://tickets.metabrainz.org/browse/PICARD-105) - Picard won't load non-album tracks from fingerprints
- [PICARD-421](https://tickets.metabrainz.org/browse/PICARD-421) - Releases in private collections are not shown as being in them
- [PICARD-518](https://tickets.metabrainz.org/browse/PICARD-518) - Sliders without labels in "Options - Metadata - Preferred Releases"
- [PICARD-637](https://tickets.metabrainz.org/browse/PICARD-637) - `$matchedtracks` is broken
- [PICARD-875](https://tickets.metabrainz.org/browse/PICARD-875) - AIFF does not support any of the compatid3 tags
- [PICARD-949](https://tickets.metabrainz.org/browse/PICARD-949) - Track can be placed in the incorrect spot on the release after using Scan
- [PICARD-1013](https://tickets.metabrainz.org/browse/PICARD-1013) - False file save error in specific circumstances
- [PICARD-1060](https://tickets.metabrainz.org/browse/PICARD-1060) - Collections menu not displayed correctly anymore
- [PICARD-1112](https://tickets.metabrainz.org/browse/PICARD-1112) - Cannot save tags that were previously deleted from file
- [PICARD-1133](https://tickets.metabrainz.org/browse/PICARD-1133) - Plugins list doesn't load automatically after setting proxy
- [PICARD-1162](https://tickets.metabrainz.org/browse/PICARD-1162) - Solo vocals are tagged wrong
- [PICARD-1219](https://tickets.metabrainz.org/browse/PICARD-1219) - Picard creating empty ID3 TIPL / TMCL / IPLS frames
- [PICARD-1245](https://tickets.metabrainz.org/browse/PICARD-1245) - Set field "Grouping" doesn't work as expected
- [PICARD-1275](https://tickets.metabrainz.org/browse/PICARD-1275) - After uninstalling a plugin Picard needs to be restarted for it to be reinstalled
- [PICARD-1281](https://tickets.metabrainz.org/browse/PICARD-1281) - Picard has wrong version string on macOS
- [PICARD-1320](https://tickets.metabrainz.org/browse/PICARD-1320) - Black text on a dark theme
- [PICARD-1332](https://tickets.metabrainz.org/browse/PICARD-1332) - Deleted tags for matched files stay deleted
- [PICARD-1336](https://tickets.metabrainz.org/browse/PICARD-1336) - MP4 reports "bpm" as unsupported tag
- [PICARD-1339](https://tickets.metabrainz.org/browse/PICARD-1339) - Removing unclustered files can be very slow
- [PICARD-1340](https://tickets.metabrainz.org/browse/PICARD-1340) - File info doesn't display Mono / Stereo in Channels field anymore
- [PICARD-1341](https://tickets.metabrainz.org/browse/PICARD-1341) - Cluster track order misinterprets disc/track numbers
- [PICARD-1346](https://tickets.metabrainz.org/browse/PICARD-1346) - Move additional files fails if multiple patterns match
- [PICARD-1348](https://tickets.metabrainz.org/browse/PICARD-1348) - Keyboard shortcuts broken due to localization
- [PICARD-1350](https://tickets.metabrainz.org/browse/PICARD-1350) - Drag and drop on cover image box does not always work as expected
- [PICARD-1355](https://tickets.metabrainz.org/browse/PICARD-1355) - Setting or unsetting album for non-album tracks does not work
- [PICARD-1359](https://tickets.metabrainz.org/browse/PICARD-1359) - Crash with tagger integration when using DuckDuckGo Privacy Essentials
- [PICARD-1364](https://tickets.metabrainz.org/browse/PICARD-1364) - picard.exe has no version tag
- [PICARD-1368](https://tickets.metabrainz.org/browse/PICARD-1368) - Info messages are not shown on logging level Info
- [PICARD-1369](https://tickets.metabrainz.org/browse/PICARD-1369) - Crash on Python 3.7.0 opening URLs
- [PICARD-1370](https://tickets.metabrainz.org/browse/PICARD-1370) - Windows installer to add "Quick Launch" icon no longer supported on Win10
- [PICARD-1371](https://tickets.metabrainz.org/browse/PICARD-1371) - Windows installer does not warn when installing on 32 bit system
- [PICARD-1373](https://tickets.metabrainz.org/browse/PICARD-1373) - Source distributions are unusable
- [PICARD-1374](https://tickets.metabrainz.org/browse/PICARD-1374) - Picard crashes while typing a regular expression in some cases
- [PICARD-1375](https://tickets.metabrainz.org/browse/PICARD-1375) - Metadata sanitation before move-script execution fails
- [PICARD-1376](https://tickets.metabrainz.org/browse/PICARD-1376) - Error saving Ape files with tag marked for deletion that does not exist
- [PICARD-1381](https://tickets.metabrainz.org/browse/PICARD-1381) - Test results depend on execution order of tests
- [PICARD-1397](https://tickets.metabrainz.org/browse/PICARD-1397) - Do not save tags marked as unsupported
- [PICARD-1398](https://tickets.metabrainz.org/browse/PICARD-1398) - Snap package is missing locale files
- [PICARD-1405](https://tickets.metabrainz.org/browse/PICARD-1405) - Pasting formatted text into scripting window shows formatting
- [PICARD-1410](https://tickets.metabrainz.org/browse/PICARD-1410) - Loading Vorbis file with invalid rating value fails
- [PICARD-1412](https://tickets.metabrainz.org/browse/PICARD-1412) - Deleting tag counts not as important metadata change
- [PICARD-1414](https://tickets.metabrainz.org/browse/PICARD-1414) - Image errors lead to crash in info dialog
- [PICARD-1415](https://tickets.metabrainz.org/browse/PICARD-1415) - Open Containing Folder and Open with MusicPlayer does nothing for UNC paths
- [PICARD-1418](https://tickets.metabrainz.org/browse/PICARD-1418) - Display localized default dialogs and keyboard shortcut hints
- [PICARD-1420](https://tickets.metabrainz.org/browse/PICARD-1420) - Can not save wma file. TypeError: sequence item 0
- [PICARD-1428](https://tickets.metabrainz.org/browse/PICARD-1428) - Removing tags which are only in original file metadata not possible
- [PICARD-1430](https://tickets.metabrainz.org/browse/PICARD-1430) - "Authentication required" dialog does not trigger authentication
- [PICARD-1431](https://tickets.metabrainz.org/browse/PICARD-1431) - Some ID3 frames gets deleted even if the corresponding tags are shown as unchanged
- [PICARD-1434](https://tickets.metabrainz.org/browse/PICARD-1434) - Tag acoustid_id can not be removed or deleted in script
- [PICARD-1436](https://tickets.metabrainz.org/browse/PICARD-1436) - Text extraction of "title" and "label" for translation.
- [PICARD-1437](https://tickets.metabrainz.org/browse/PICARD-1437) - After reload file is being shown as changed
- [PICARD-1438](https://tickets.metabrainz.org/browse/PICARD-1438) - Message box buttons Yes/No aren't translated
- [PICARD-1439](https://tickets.metabrainz.org/browse/PICARD-1439) - Newline character in cover art naming script causes exception on saving

## New Features
- [PICARD-490](https://tickets.metabrainz.org/browse/PICARD-490) - Allow tagging AAC/ADTS files with APEv2 tags
- [PICARD-1043](https://tickets.metabrainz.org/browse/PICARD-1043) - Support reading & writing iTunes Classical tags
- [PICARD-1045](https://tickets.metabrainz.org/browse/PICARD-1045) - Check for new version
- [PICARD-1268](https://tickets.metabrainz.org/browse/PICARD-1268) - Support concertmaster recording relationships as performer:concertmaster
- [PICARD-1273](https://tickets.metabrainz.org/browse/PICARD-1273) - Add an option to exclude new cover art type "Raw / Unedited"
- [PICARD-1319](https://tickets.metabrainz.org/browse/PICARD-1319) - Provide cover art metadata to cover image naming script
- [PICARD-1344](https://tickets.metabrainz.org/browse/PICARD-1344) - Add `$delete` function
- [PICARD-1352](https://tickets.metabrainz.org/browse/PICARD-1352) - Add a command-line option to skip plugin loading
- [PICARD-1354](https://tickets.metabrainz.org/browse/PICARD-1354) - Allow using vocals and instruments as credited
- [PICARD-1367](https://tickets.metabrainz.org/browse/PICARD-1367) - Allow opening searches in browser when using search dialogs
- [PICARD-1384](https://tickets.metabrainz.org/browse/PICARD-1384) - Add AppStream data
- [PICARD-1386](https://tickets.metabrainz.org/browse/PICARD-1386) - Add `$title` function
- [PICARD-1395](https://tickets.metabrainz.org/browse/PICARD-1395) - Support genres from MusicBrainz
- [PICARD-1440](https://tickets.metabrainz.org/browse/PICARD-1440) - Support loading and renaming Standard MIDI Files (SMF)

## Tasks
- [PICARD-1333](https://tickets.metabrainz.org/browse/PICARD-1333) - Run CI tests agaist oldest supported mutagen
- [PICARD-1347](https://tickets.metabrainz.org/browse/PICARD-1347) - Refactor script.py to avoid code duplication
- [PICARD-1365](https://tickets.metabrainz.org/browse/PICARD-1365) - Allow building with PyQt 5.11 or later
- [PICARD-1442](https://tickets.metabrainz.org/browse/PICARD-1442) - Support new Audio Play secondary type

## Sub-tasks
- [PICARD-1407](https://tickets.metabrainz.org/browse/PICARD-1407) - Save originalalbum / originalartist to ASF/WMA
- [PICARD-1408](https://tickets.metabrainz.org/browse/PICARD-1408) - Save originalalbum / originalartist to APE

## Improvements
- [PICARD-664](https://tickets.metabrainz.org/browse/PICARD-664) - When dragging a recording, show the actual file name instead of the path
- [PICARD-792](https://tickets.metabrainz.org/browse/PICARD-792) - Package a start menu tile for Windows 10 on the windows version
- [PICARD-1039](https://tickets.metabrainz.org/browse/PICARD-1039) - Use forward delete instead of delete button on macOS
- [PICARD-1049](https://tickets.metabrainz.org/browse/PICARD-1049) - Picard should use TXXX:WORK rather than TXXX:Work
- [PICARD-1068](https://tickets.metabrainz.org/browse/PICARD-1068) - Picard should use MP4 ©wrk for Work rather than generic text field
- [PICARD-1244](https://tickets.metabrainz.org/browse/PICARD-1244) - Refresh list of plugins after uninstalling or installing a local plugin
- [PICARD-1285](https://tickets.metabrainz.org/browse/PICARD-1285) - There is no Close menu item in Picard 2.0 on macOS
- [PICARD-1313](https://tickets.metabrainz.org/browse/PICARD-1313) - Refactor plugin UI
- [PICARD-1325](https://tickets.metabrainz.org/browse/PICARD-1325) - Allow disabling new version update checking for packagers
- [PICARD-1338](https://tickets.metabrainz.org/browse/PICARD-1338) - Picard should be more resilient if it gets invalid responses from servers
- [PICARD-1358](https://tickets.metabrainz.org/browse/PICARD-1358) - Use macOS style widgets in the user interface of the macOS version of Picard
- [PICARD-1363](https://tickets.metabrainz.org/browse/PICARD-1363) - AcoustId submission for matched files is impossible when musicbrainz_recordingid is unset
- [PICARD-1366](https://tickets.metabrainz.org/browse/PICARD-1366) - Show Python version in about
- [PICARD-1379](https://tickets.metabrainz.org/browse/PICARD-1379) - Port astrcmp to new Python C Unicode API
- [PICARD-1383](https://tickets.metabrainz.org/browse/PICARD-1383) - Use MCN / barcode read from disc to improve DiscId lookup
- [PICARD-1393](https://tickets.metabrainz.org/browse/PICARD-1393) - Change the application ID
- [PICARD-1416](https://tickets.metabrainz.org/browse/PICARD-1416) - Should store ID3 Artists field as TXXX:ARTISTS not TXXX:Artists
- [PICARD-1417](https://tickets.metabrainz.org/browse/PICARD-1417) - Only show plugins with compatible API version
- [PICARD-1424](https://tickets.metabrainz.org/browse/PICARD-1424) - Translate AppStream data
- [PICARD-1425](https://tickets.metabrainz.org/browse/PICARD-1425) - Support all movement tags for APE, Vorbis and MP3
- [PICARD-1426](https://tickets.metabrainz.org/browse/PICARD-1426) - Map musicbrainz_originalalbumid and musicbrainz_originalartistid to MP4 and WMA
- [PICARD-1443](https://tickets.metabrainz.org/browse/PICARD-1443) - Sort secondary release types in UI alphabetically


# Version 2.0.4 - 2018-09-05
## Bugfixes
- [PICARD-803](https://tickets.metabrainz.org/browse/PICARD-803) - tagging "8½ Minutes" with "replace with non-ascii characters" results in a directory being created
- [PICARD-1216](https://tickets.metabrainz.org/browse/PICARD-1216) - Does not display version information
- [PICARD-1267](https://tickets.metabrainz.org/browse/PICARD-1267) - 2.0.0dev6 crash in debug mode on Windows April Update (1803)
- [PICARD-1281](https://tickets.metabrainz.org/browse/PICARD-1281) - Picard has wrong version string
- [PICARD-1294](https://tickets.metabrainz.org/browse/PICARD-1294) - Crashes every time Picard connects to MB server.
- [PICARD-1310](https://tickets.metabrainz.org/browse/PICARD-1310) - Picard crashes on clearing log
- [PICARD-1318](https://tickets.metabrainz.org/browse/PICARD-1318) - RuntimeError: dictionary changed size during iteration
- [PICARD-1321](https://tickets.metabrainz.org/browse/PICARD-1321) - CD drive selection not working on Linux
- [PICARD-1322](https://tickets.metabrainz.org/browse/PICARD-1322) - Crash in options on "Restore defaults"
- [PICARD-1323](https://tickets.metabrainz.org/browse/PICARD-1323) - Restore defaults does not restore CAA types
- [PICARD-1324](https://tickets.metabrainz.org/browse/PICARD-1324) - Default locale not working reliable
- [PICARD-1326](https://tickets.metabrainz.org/browse/PICARD-1326) - Picard Save Changes 5.1 Mix Type
- [PICARD-1327](https://tickets.metabrainz.org/browse/PICARD-1327) - Loading TAK files fails
- [PICARD-1328](https://tickets.metabrainz.org/browse/PICARD-1328) - Loading OptimFROG files fails
- [PICARD-1329](https://tickets.metabrainz.org/browse/PICARD-1329) - Picard fails saving ID3 tags with iTunNORM tag
- [PICARD-1331](https://tickets.metabrainz.org/browse/PICARD-1331) - Picard crashes on error during plugin install



# Version 2.0.3 - 2018-08-10
## Bugfixes
- [PICARD-1122](https://tickets.metabrainz.org/browse/PICARD-1122) - Preffered release type settings are exclusive and should be inclusive
- [PICARD-1207](https://tickets.metabrainz.org/browse/PICARD-1207) - Move additional files feature fails when source directory contains non-ascii characters
- [PICARD-1247](https://tickets.metabrainz.org/browse/PICARD-1247) - Not all "preserved" tags are preserved
- [PICARD-1305](https://tickets.metabrainz.org/browse/PICARD-1305) - Search dialog crashes picard when record doesn't have an album
- [PICARD-1306](https://tickets.metabrainz.org/browse/PICARD-1306) - picard crashes when opening the options dialog if the cwd doesn't exist

## New Features
- [PICARD-1289](https://tickets.metabrainz.org/browse/PICARD-1289) - Allow manually running any tagger script


## Improvements
- [PICARD-1292](https://tickets.metabrainz.org/browse/PICARD-1292) - MusicBrainz Picard 2.01 64-bit for windows installs to "C:\Program Files (x86)" by default
- [PICARD-1302](https://tickets.metabrainz.org/browse/PICARD-1302) - Dropping an image from Google image crashes picard
- [PICARD-1303](https://tickets.metabrainz.org/browse/PICARD-1303) - picard crashes when matching a cluster with a release with no tracks
- [PICARD-1304](https://tickets.metabrainz.org/browse/PICARD-1304) - Info dialog for album crashes because track doesn't have a tracknumber

## Regression
- [PICARD-259](https://tickets.metabrainz.org/browse/PICARD-259) - Make file-specific variables available to tagger script


# Version 2.0.2 - 2018-07-30
## Sub-tasks
- [PICARD-1296](https://tickets.metabrainz.org/browse/PICARD-1296) - Code sign Picard for macOS

## Tasks
- [PICARD-1301](https://tickets.metabrainz.org/browse/PICARD-1301) - Use PyQT 5.10 for macOS

## Bugfixes
- [PICARD-342](https://tickets.metabrainz.org/browse/PICARD-342) - Picard is not properly signed for Mac OS X Gatekeeper
- [PICARD-1212](https://tickets.metabrainz.org/browse/PICARD-1212) - Picard 2.0.0dev4 crashing at startup
- [PICARD-1300](https://tickets.metabrainz.org/browse/PICARD-1300) - Picard crashes when logging lots of events

# Version 2.0.1 - 2018-07-21
## Bugfixes
- [PICARD-1283](https://tickets.metabrainz.org/browse/PICARD-1283) - Fingerprinting not working on macOS in Picard 2.0
- [PICARD-1286](https://tickets.metabrainz.org/browse/PICARD-1286) - Error creating SSL context on Windows

## Improvements
- [PICARD-1290](https://tickets.metabrainz.org/browse/PICARD-1290) - Improve slow start up times by moving to a non single file exe
- [PICARD-1291](https://tickets.metabrainz.org/browse/PICARD-1291) - Use an installer for Picard 2.x windows exe

# Version 2.0 - 2018-07-18
## Bugfixes
- [PICARD-153](https://tickets.metabrainz.org/browse/PICARD-153) - Non-configuration data is saved in Picard.conf
- [PICARD-173](https://tickets.metabrainz.org/browse/PICARD-173) - ID3 tag TSOP appears to be stored blank
- [PICARD-340](https://tickets.metabrainz.org/browse/PICARD-340) - Cover art embedding will overwrite existing ones
- [PICARD-405](https://tickets.metabrainz.org/browse/PICARD-405) - Save stopped working
- [PICARD-817](https://tickets.metabrainz.org/browse/PICARD-817) - On high-resolution / high DPI displays, Picard's GUI is scaled wrong
- [PICARD-1047](https://tickets.metabrainz.org/browse/PICARD-1047) - Incompatible plugins are loaded with picard 2.0
- [PICARD-1051](https://tickets.metabrainz.org/browse/PICARD-1051) - Searching for similar tracks causes coredumps
- [PICARD-1052](https://tickets.metabrainz.org/browse/PICARD-1052) - Not disabled Search for similar tracks can cause coredumps
- [PICARD-1056](https://tickets.metabrainz.org/browse/PICARD-1056) - Crash when viewing file info dialog
- [PICARD-1058](https://tickets.metabrainz.org/browse/PICARD-1058) - Saving images as files doesn't work
- [PICARD-1062](https://tickets.metabrainz.org/browse/PICARD-1062) - Picard crashes when moving files on release
- [PICARD-1063](https://tickets.metabrainz.org/browse/PICARD-1063) - After #689 unit tests fail if astrcmp is not compiled
- [PICARD-1064](https://tickets.metabrainz.org/browse/PICARD-1064) - python setup.py test -v doesn't work
- [PICARD-1065](https://tickets.metabrainz.org/browse/PICARD-1065) - python setup.py patch_version doesn't work
- [PICARD-1066](https://tickets.metabrainz.org/browse/PICARD-1066) - python setup.py update_constants doesn't work
- [PICARD-1067](https://tickets.metabrainz.org/browse/PICARD-1067) - Visual bug after un-checking an installed plugin
- [PICARD-1073](https://tickets.metabrainz.org/browse/PICARD-1073) - "Add New Tag" crashes picard
- [PICARD-1084](https://tickets.metabrainz.org/browse/PICARD-1084) - Picard 2 doesn't find DVD drive
- [PICARD-1085](https://tickets.metabrainz.org/browse/PICARD-1085) - Multi-Dir Add Folder not working
- [PICARD-1105](https://tickets.metabrainz.org/browse/PICARD-1105) - Crashes when using the edit tag dialog
- [PICARD-1106](https://tickets.metabrainz.org/browse/PICARD-1106) - cancel plugin installation file dialog results in crash
- [PICARD-1114](https://tickets.metabrainz.org/browse/PICARD-1114) - Cannot submit ratings in Picard 2.0 dev
- [PICARD-1119](https://tickets.metabrainz.org/browse/PICARD-1119) - picard sets "Disc Subtitle" to the track title
- [PICARD-1123](https://tickets.metabrainz.org/browse/PICARD-1123) - Multiple work languages are collapsed
- [PICARD-1126](https://tickets.metabrainz.org/browse/PICARD-1126) - Unhelpful error message logged on network request errors
- [PICARD-1135](https://tickets.metabrainz.org/browse/PICARD-1135) - Picard is not able to save on MTP devices
- [PICARD-1138](https://tickets.metabrainz.org/browse/PICARD-1138) - Search crashes due to AttributeError
- [PICARD-1143](https://tickets.metabrainz.org/browse/PICARD-1143) - Wrong amount of songs from added files
- [PICARD-1147](https://tickets.metabrainz.org/browse/PICARD-1147) - FYI, Can't load "Alan Parsons" album "On air" in Picard 1.2
- [PICARD-1153](https://tickets.metabrainz.org/browse/PICARD-1153) - "Lookup in Browser" and "Search" fail silently if artist name contains umlaut
- [PICARD-1156](https://tickets.metabrainz.org/browse/PICARD-1156) - Picard fails to start when trying to upgrade plugin which is a symlink
- [PICARD-1159](https://tickets.metabrainz.org/browse/PICARD-1159) - Can't open WAV files
- [PICARD-1161](https://tickets.metabrainz.org/browse/PICARD-1161) - Dragging artwork from Chrome pages doesn't work
- [PICARD-1171](https://tickets.metabrainz.org/browse/PICARD-1171) - Text of "About" can't be selected
- [PICARD-1179](https://tickets.metabrainz.org/browse/PICARD-1179) - Error while searching for alt. releases
- [PICARD-1181](https://tickets.metabrainz.org/browse/PICARD-1181) - In-app search dialog excessive slow down
- [PICARD-1188](https://tickets.metabrainz.org/browse/PICARD-1188) - Picard chooses incorrect value for language tag
- [PICARD-1199](https://tickets.metabrainz.org/browse/PICARD-1199) - Crash when right-clicking album
- [PICARD-1202](https://tickets.metabrainz.org/browse/PICARD-1202) - Right click on tag listing causes exception and crash
- [PICARD-1203](https://tickets.metabrainz.org/browse/PICARD-1203) - Hide unsupported tags from the tag diff in UI
- [PICARD-1204](https://tickets.metabrainz.org/browse/PICARD-1204) - Picard freezes on unchecking show diff tags first
- [PICARD-1206](https://tickets.metabrainz.org/browse/PICARD-1206) - Text is not displaying properly in some fields.
- [PICARD-1210](https://tickets.metabrainz.org/browse/PICARD-1210) - Long lines in the option dialogue don’t wrap
- [PICARD-1213](https://tickets.metabrainz.org/browse/PICARD-1213) - Wrong Movement of coverart providers
- [PICARD-1215](https://tickets.metabrainz.org/browse/PICARD-1215) - Does not use config / ini file specified on command line
- [PICARD-1221](https://tickets.metabrainz.org/browse/PICARD-1221) - Picard 2.0 won't start on Windows 10
- [PICARD-1226](https://tickets.metabrainz.org/browse/PICARD-1226) - Different fonts in the plugins dialog
- [PICARD-1230](https://tickets.metabrainz.org/browse/PICARD-1230) - Looking up CD crashes Picard
- [PICARD-1234](https://tickets.metabrainz.org/browse/PICARD-1234) - Crash when loading plugin from local directory
- [PICARD-1252](https://tickets.metabrainz.org/browse/PICARD-1252) - Crash on pasting invalid naming script
- [PICARD-1253](https://tickets.metabrainz.org/browse/PICARD-1253) - Crash on image saving
- [PICARD-1255](https://tickets.metabrainz.org/browse/PICARD-1255) - Crash on startup - no GUI
- [PICARD-1265](https://tickets.metabrainz.org/browse/PICARD-1265) - Can't "Lookup in Browser": UnicodeEncodeError: 'latin-1' codec can't encode characters in position 0-7: ordinal not in range(256)
- [PICARD-1270](https://tickets.metabrainz.org/browse/PICARD-1270) - Corruption of saved audio files located on a network share
- [PICARD-1271](https://tickets.metabrainz.org/browse/PICARD-1271) - Artist credit saved in tags sometimes loses closing parenthesis
- [PICARD-1277](https://tickets.metabrainz.org/browse/PICARD-1277) - Picard crashes on unknown cover art types

## New Features
- [PICARD-1187](https://tickets.metabrainz.org/browse/PICARD-1187) - Add DSF file support
- [PICARD-1220](https://tickets.metabrainz.org/browse/PICARD-1220) - Add keyboard shortcut for deleting scripts from options > scripting page

## Tasks
- [PICARD-960](https://tickets.metabrainz.org/browse/PICARD-960) - Migrate to PyQt5
- [PICARD-1186](https://tickets.metabrainz.org/browse/PICARD-1186) - Support only 64 bit Picard builds from 2.0

## Improvements
- [PICARD-259](https://tickets.metabrainz.org/browse/PICARD-259) - Make file-specific variables available to tagger script
- [PICARD-581](https://tickets.metabrainz.org/browse/PICARD-581) - Picard XML processing should use lxml module rather than QXmlStreamReader
- [PICARD-588](https://tickets.metabrainz.org/browse/PICARD-588) - Picard 2.0 based on Python 3
- [PICARD-807](https://tickets.metabrainz.org/browse/PICARD-807) - Retry release fetch on MB server overload
- [PICARD-922](https://tickets.metabrainz.org/browse/PICARD-922) - Make multi-value script functions work correctly
- [PICARD-976](https://tickets.metabrainz.org/browse/PICARD-976) - Reimplement the picard WS code to accommodate future versions of MBWS
- [PICARD-978](https://tickets.metabrainz.org/browse/PICARD-978) - Distinguish in UI between unclustered and release unmatched files
- [PICARD-994](https://tickets.metabrainz.org/browse/PICARD-994) - Show all release countries in CD lookup
- [PICARD-1075](https://tickets.metabrainz.org/browse/PICARD-1075) - Add unit tests for Metadata object variables
- [PICARD-1087](https://tickets.metabrainz.org/browse/PICARD-1087) - Improvements to UI for Lookup CD
- [PICARD-1100](https://tickets.metabrainz.org/browse/PICARD-1100) - Error when running confined in a snap because of gconf
- [PICARD-1174](https://tickets.metabrainz.org/browse/PICARD-1174) - Option to tolerate differences in track times
- [PICARD-1200](https://tickets.metabrainz.org/browse/PICARD-1200) - In Options dialog, tree pane on the left cannot be resized
- [PICARD-1201](https://tickets.metabrainz.org/browse/PICARD-1201) - Add a command-line option to not restore persisted UI sizes or positions
- [PICARD-1211](https://tickets.metabrainz.org/browse/PICARD-1211) - The “X” close button doesn’t work on the options dialogue

# Version 1.4.2 - 2017-05-08
## Bugfixes
- [PICARD-1053](https://tickets.metabrainz.org/browse/PICARD-1053) - Picard does not stop analyzer while moving
- [PICARD-1055](https://tickets.metabrainz.org/browse/PICARD-1055) - picard hangs with: RuntimeError: maximum recursion depth exceeded in cmp
- [PICARD-1070](https://tickets.metabrainz.org/browse/PICARD-1070) - The "Convert Unicode punctuation characters to ASCII" function only works in certain tags
- [PICARD-1077](https://tickets.metabrainz.org/browse/PICARD-1077) - ID3v2.4 text encoding settings are not saved correctly

## Improvements
- [PICARD-969](https://tickets.metabrainz.org/browse/PICARD-969) - Search dialog webservices get queued behind matched album requests
- [PICARD-1034](https://tickets.metabrainz.org/browse/PICARD-1034) - Picard not seeing TOPE and TOAL

# Version 1.4.1 - 2017-04-01
## Bugfixes
- [PICARD-953](https://tickets.metabrainz.org/browse/PICARD-953) - Album shown matched even if extra unmatched files
- [PICARD-972](https://tickets.metabrainz.org/browse/PICARD-972) - Removing album with saves pending does not remove pending saves
- [PICARD-973](https://tickets.metabrainz.org/browse/PICARD-973) - Pending log messages not flushed to stderr on quit
- [PICARD-988](https://tickets.metabrainz.org/browse/PICARD-988) - Drag & Drop not working
- [PICARD-990](https://tickets.metabrainz.org/browse/PICARD-990) - Picard violating ID3 standard for TXXX frames
- [PICARD-996](https://tickets.metabrainz.org/browse/PICARD-996) - Disabling the cover art box and enabling it again doesn't bring it back
- [PICARD-998](https://tickets.metabrainz.org/browse/PICARD-998) - Disabling the action toolbar sometimes doesn't work
- [PICARD-1005](https://tickets.metabrainz.org/browse/PICARD-1005) - If a cluster is moved to the album side of the main window it gets moved to unmatched files
- [PICARD-1006](https://tickets.metabrainz.org/browse/PICARD-1006) - Drag and drop for cover arts doesnt work on OSX
- [PICARD-1010](https://tickets.metabrainz.org/browse/PICARD-1010) - Unsetting View/Cover Art doesn't work permanently
- [PICARD-1011](https://tickets.metabrainz.org/browse/PICARD-1011) - Toolbar tab order incorrect after PICARD-908
- [PICARD-1014](https://tickets.metabrainz.org/browse/PICARD-1014) - Number of images in release info is calculated incorrectly
- [PICARD-1015](https://tickets.metabrainz.org/browse/PICARD-1015) - Artwork tab of the Track Info DIalog doesn't show changes anymore
- [PICARD-1018](https://tickets.metabrainz.org/browse/PICARD-1018) - CoverArtBox doesn't show new/removed images after unmatched files are added/removed to the album
- [PICARD-1023](https://tickets.metabrainz.org/browse/PICARD-1023) - Directory persistence for Add Directory needs tweaking
- [PICARD-1029](https://tickets.metabrainz.org/browse/PICARD-1029) - Fix ~artists_sort metadata variable
- [PICARD-1042](https://tickets.metabrainz.org/browse/PICARD-1042) - Missing import for PICARD_APP_NAME

## New Features
- [PICARD-258](https://tickets.metabrainz.org/browse/PICARD-258) - Visual feedback for changes to artwork in before-after pane.
- [PICARD-1000](https://tickets.metabrainz.org/browse/PICARD-1000) - Implement artwork diff for albums

## Tasks
- [PICARD-943](https://tickets.metabrainz.org/browse/PICARD-943) - Remove monkey patching of file write methods in picard formats
- [PICARD-1041](https://tickets.metabrainz.org/browse/PICARD-1041) - Replace Ok button text by Make It So! in Options dialog

## Improvements
- [PICARD-223](https://tickets.metabrainz.org/browse/PICARD-223) - Remove should work when Unmatched Files is selected
- [PICARD-951](https://tickets.metabrainz.org/browse/PICARD-951) - Always use HTTPS for musicbrainz.org
- [PICARD-952](https://tickets.metabrainz.org/browse/PICARD-952) - Use Cover Art Archive over HTTPS
- [PICARD-961](https://tickets.metabrainz.org/browse/PICARD-961) - Mention AcoustID on Scan button too
- [PICARD-980](https://tickets.metabrainz.org/browse/PICARD-980) - Drag&drop cover art doesn't work for images from amazon/google images/https links
- [PICARD-1012](https://tickets.metabrainz.org/browse/PICARD-1012) - Buttons on the "User Interface" and "Scripting" pages are smaller than buttons in other places
- [PICARD-1016](https://tickets.metabrainz.org/browse/PICARD-1016) - Multiple images in related tracks confusing
- [PICARD-1021](https://tickets.metabrainz.org/browse/PICARD-1021) - Picard loads all pending files before quitting
- [PICARD-1024](https://tickets.metabrainz.org/browse/PICARD-1024) - Allow specifying a configuration file path
- [PICARD-1030](https://tickets.metabrainz.org/browse/PICARD-1030) - Allow to add/replace cover art images and keep existing cover art


# Version 1.4 - 2017-02-14
## Bugfixes
- [PICARD-82](https://tickets.metabrainz.org/browse/PICARD-82) - AcoustID submission fails with code 299
- [PICARD-335](https://tickets.metabrainz.org/browse/PICARD-335) - Ignoring "hip hop rap" folksonomy tags also ignores "rap", "hip hop", etc.
- [PICARD-350](https://tickets.metabrainz.org/browse/PICARD-350) - Picard downloads multiple 'front' images instead of just first one.
- [PICARD-357](https://tickets.metabrainz.org/browse/PICARD-357) - Saving hidden file with only an extension drops the extension
- [PICARD-366](https://tickets.metabrainz.org/browse/PICARD-366) - Add directory opens in "wrong" dir
- [PICARD-375](https://tickets.metabrainz.org/browse/PICARD-375) - Picard should de-duplicate work lists
- [PICARD-408](https://tickets.metabrainz.org/browse/PICARD-408) - Tree selector in Options window is partially obscured, pane too narrow
- [PICARD-419](https://tickets.metabrainz.org/browse/PICARD-419) - tag acoustid_id can not be removed or deleted in script, renaming or plugin
- [PICARD-546](https://tickets.metabrainz.org/browse/PICARD-546) - Can't remove value from field
- [PICARD-592](https://tickets.metabrainz.org/browse/PICARD-592) - Can't open Options
- [PICARD-688](https://tickets.metabrainz.org/browse/PICARD-688) - "Tags from filenames" action stays enabled even if it is unavailable.
- [PICARD-701](https://tickets.metabrainz.org/browse/PICARD-701) - Using the first image type as filename changes the name of front images
- [PICARD-706](https://tickets.metabrainz.org/browse/PICARD-706) - Fingerprint Submission Failes if AcoustID tags are present and/or invalid
- [PICARD-726](https://tickets.metabrainz.org/browse/PICARD-726) - Picard moves into the selected folder
- [PICARD-730](https://tickets.metabrainz.org/browse/PICARD-730) - Picard does not support (recording) relationship credits
- [PICARD-748](https://tickets.metabrainz.org/browse/PICARD-748) - Picard repeats/duplicates field data
- [PICARD-751](https://tickets.metabrainz.org/browse/PICARD-751) - Number of pending web requests is not decremented on exceptions in the handler
- [PICARD-753](https://tickets.metabrainz.org/browse/PICARD-753) - Divide by zero error in `_convert_folksonomy_tags_to_genre` when no tag at the release/release group level
- [PICARD-754](https://tickets.metabrainz.org/browse/PICARD-754) - Directory tree (file browser) not sorted for non-system drives under Windows
- [PICARD-759](https://tickets.metabrainz.org/browse/PICARD-759) - Crash when loading release with only zero count tags
- [PICARD-761](https://tickets.metabrainz.org/browse/PICARD-761) - No name and no window grouping in gnome-shell Alt-Tab app switcher
- [PICARD-764](https://tickets.metabrainz.org/browse/PICARD-764) - Lookup in Browser does not and can not load HTTPS version of musicbrainz.org
- [PICARD-766](https://tickets.metabrainz.org/browse/PICARD-766) - Unable to login using oauth via Picard options with Server Port set to 443
- [PICARD-775](https://tickets.metabrainz.org/browse/PICARD-775) - "AttributeError: 'MetadataBox' object has no attribute 'resize_columns'" when enabling the cover art box
- [PICARD-778](https://tickets.metabrainz.org/browse/PICARD-778) - Pre-gap tracks are not counted in absolutetracknumber
- [PICARD-780](https://tickets.metabrainz.org/browse/PICARD-780) - CAA cover art provider runs even if cover art has already been loaded
- [PICARD-782](https://tickets.metabrainz.org/browse/PICARD-782) - Toggling Embed Cover Art in Tags and restarting doesn't have the expected behavior
- [PICARD-788](https://tickets.metabrainz.org/browse/PICARD-788) - XMLWS redirects incorrectly
- [PICARD-798](https://tickets.metabrainz.org/browse/PICARD-798) - Handle empty collection-list in web server response
- [PICARD-799](https://tickets.metabrainz.org/browse/PICARD-799) - Amazon Cover Art provider does not work (and does not have a lot of debug logging enabled)
- [PICARD-801](https://tickets.metabrainz.org/browse/PICARD-801) - Cover Art from CAA release group is skipped even though it exists
- [PICARD-804](https://tickets.metabrainz.org/browse/PICARD-804) - Multiple instances of history and log dialogs
- [PICARD-805](https://tickets.metabrainz.org/browse/PICARD-805) - Empty string lookup
- [PICARD-811](https://tickets.metabrainz.org/browse/PICARD-811) - Will not load album information on any albums
- [PICARD-814](https://tickets.metabrainz.org/browse/PICARD-814) - Redirect URL is not encoded which leads to http 400 error.
- [PICARD-833](https://tickets.metabrainz.org/browse/PICARD-833) - Not compatible with latest Mutagen
- [PICARD-834](https://tickets.metabrainz.org/browse/PICARD-834) - Can't save any files.  Get: "error: invalid literal for int() with base 10"
- [PICARD-839](https://tickets.metabrainz.org/browse/PICARD-839) - Picard 1.3.2 shows cleartext username & password on status line when errors occur
- [PICARD-848](https://tickets.metabrainz.org/browse/PICARD-848) - Cannot fetch cover art from amazon link contains https scheme.
- [PICARD-851](https://tickets.metabrainz.org/browse/PICARD-851) - media-optical-modified.png icon still displayed after release save when two files match one track
- [PICARD-853](https://tickets.metabrainz.org/browse/PICARD-853) - Release that Picard will not load (due to disc with just data track?)
- [PICARD-855](https://tickets.metabrainz.org/browse/PICARD-855) - ValueError in metadata.py
- [PICARD-857](https://tickets.metabrainz.org/browse/PICARD-857) - Improper detection of Gnome as a desktop environment and no support for gnome 3
- [PICARD-858](https://tickets.metabrainz.org/browse/PICARD-858) - Apparent non-functional tagger button
- [PICARD-859](https://tickets.metabrainz.org/browse/PICARD-859) - Picard does not read Ogg/Opus files with an ".ogg" file exension
- [PICARD-865](https://tickets.metabrainz.org/browse/PICARD-865) - Setting a large value in in `$num` function as length causes picard to become unresponsive
- [PICARD-867](https://tickets.metabrainz.org/browse/PICARD-867) - id3 deletion needs to be improved
- [PICARD-868](https://tickets.metabrainz.org/browse/PICARD-868) - id3v2.3 does not properly handle TMOO ( mood tag)
- [PICARD-870](https://tickets.metabrainz.org/browse/PICARD-870) - Coverart providers duplicates on reset
- [PICARD-873](https://tickets.metabrainz.org/browse/PICARD-873) - Restore defaults broken for plugins page and tagger scripts page
- [PICARD-874](https://tickets.metabrainz.org/browse/PICARD-874) - Coverart providers erroneous save
- [PICARD-876](https://tickets.metabrainz.org/browse/PICARD-876) - The metadatabox doesn't correctly show the tag selected
- [PICARD-881](https://tickets.metabrainz.org/browse/PICARD-881) - Length tag for ID3 is no longer displayed in the metadata box
- [PICARD-882](https://tickets.metabrainz.org/browse/PICARD-882) - Removed tags are not removed from the metadatabox after saving the file
- [PICARD-884](https://tickets.metabrainz.org/browse/PICARD-884) - File Browser pane doesn't check for path type (file or folder) when setting home path/move files here
- [PICARD-885](https://tickets.metabrainz.org/browse/PICARD-885) - mov files return a +ve score for mp4 container leading to errors
- [PICARD-888](https://tickets.metabrainz.org/browse/PICARD-888) - "Restore defaults" doesn't log out the user
- [PICARD-907](https://tickets.metabrainz.org/browse/PICARD-907) - Broken 'Restore Defaults'
- [PICARD-911](https://tickets.metabrainz.org/browse/PICARD-911) - Messagebox wraps and displays title inappropriately
- [PICARD-914](https://tickets.metabrainz.org/browse/PICARD-914) - An “empty” track shouldn’t get an “excellent match” tooltip.
- [PICARD-915](https://tickets.metabrainz.org/browse/PICARD-915) - In plugins list, some plugins don't show description
- [PICARD-916](https://tickets.metabrainz.org/browse/PICARD-916) - Plugin restore defaults broken
- [PICARD-917](https://tickets.metabrainz.org/browse/PICARD-917) - Does not use UI language but locale on Windows
- [PICARD-925](https://tickets.metabrainz.org/browse/PICARD-925) - Preserve scripting splitter position
- [PICARD-926](https://tickets.metabrainz.org/browse/PICARD-926) - Having trouble submitting AcoustIDs
- [PICARD-931](https://tickets.metabrainz.org/browse/PICARD-931) - Cluster double‐click opens the Info… panel
- [PICARD-937](https://tickets.metabrainz.org/browse/PICARD-937) - Status bar not cleared when selection changed
- [PICARD-942](https://tickets.metabrainz.org/browse/PICARD-942) - Open containing folder not working for shared files over network
- [PICARD-945](https://tickets.metabrainz.org/browse/PICARD-945) - Warning: Plugin directory '…/python2.7/site-packages/contrib/plugins' doesn't exist
- [PICARD-946](https://tickets.metabrainz.org/browse/PICARD-946) - Additionnal files aren't moved anymore
- [PICARD-947](https://tickets.metabrainz.org/browse/PICARD-947) - Search window error message does not appear translated
- [PICARD-950](https://tickets.metabrainz.org/browse/PICARD-950) - Open Containing Folder duplicates
- [PICARD-958](https://tickets.metabrainz.org/browse/PICARD-958) - Errors when directory / file names contain unicode characters

## New Features
- [PICARD-42](https://tickets.metabrainz.org/browse/PICARD-42) - AIFF support (ID3)
- [PICARD-137](https://tickets.metabrainz.org/browse/PICARD-137) - Test and integrate support for "local" cover art into Picard
- [PICARD-680](https://tickets.metabrainz.org/browse/PICARD-680) - Display infos (album, artist, tracklist) for clusters without release match
- [PICARD-691](https://tickets.metabrainz.org/browse/PICARD-691) - Add download plugin functionality to existing UI
- [PICARD-738](https://tickets.metabrainz.org/browse/PICARD-738) - Fallback on album artist's tags if no tags are found for album
- [PICARD-743](https://tickets.metabrainz.org/browse/PICARD-743) - Add m2a as a supported extension
- [PICARD-756](https://tickets.metabrainz.org/browse/PICARD-756) - MusicBrainz/AcoustID entities should be hyperlinked in Picard
- [PICARD-769](https://tickets.metabrainz.org/browse/PICARD-769) - Support key tag
- [PICARD-901](https://tickets.metabrainz.org/browse/PICARD-901) - Export / import settings
- [PICARD-927](https://tickets.metabrainz.org/browse/PICARD-927) - Search releases from within a Picard dialog
- [PICARD-928](https://tickets.metabrainz.org/browse/PICARD-928) - Searching tracks and displaying similar tracks in a dialog box
- [PICARD-929](https://tickets.metabrainz.org/browse/PICARD-929) - Search for artists from dialog

## Tasks
- [PICARD-717](https://tickets.metabrainz.org/browse/PICARD-717) - Picard default name files script refinement
- [PICARD-760](https://tickets.metabrainz.org/browse/PICARD-760) - Update Picard logo/icons
- [PICARD-779](https://tickets.metabrainz.org/browse/PICARD-779) - Link to the Scripting documentation on the Scripting options page
- [PICARD-835](https://tickets.metabrainz.org/browse/PICARD-835) - Remove contrib/plugins from the repository
- [PICARD-841](https://tickets.metabrainz.org/browse/PICARD-841) - Raise the required mutagen version to 1.22
- [PICARD-861](https://tickets.metabrainz.org/browse/PICARD-861) - Renaming save_only_front_images_to_tags option to something more appropriate
- [PICARD-895](https://tickets.metabrainz.org/browse/PICARD-895) - Allow translators to finalize translations before releasing Picard 1.4
- [PICARD-904](https://tickets.metabrainz.org/browse/PICARD-904) - Raise the required Python version to 2.7.
- [PICARD-912](https://tickets.metabrainz.org/browse/PICARD-912) - Bump Picard’s copyright date
- [PICARD-982](https://tickets.metabrainz.org/browse/PICARD-982) - Add Norwegian to UI languages
- [PICARD-652](https://tickets.metabrainz.org/browse/PICARD-652) - Provide ~video variable for video tracks
- [PICARD-708](https://tickets.metabrainz.org/browse/PICARD-708) - Improve error logging on AcoustId submission

## Improvements
- [PICARD-22](https://tickets.metabrainz.org/browse/PICARD-22) - Link to Picard Scripting page under 'File Naming'
- [PICARD-116](https://tickets.metabrainz.org/browse/PICARD-116) - Restore default settings button/s
- [PICARD-133](https://tickets.metabrainz.org/browse/PICARD-133) - Speed of Ogg tag writing/updating
- [PICARD-207](https://tickets.metabrainz.org/browse/PICARD-207) - Allow adding/removing tags to be preserved from context menu in the tag diff pane
- [PICARD-210](https://tickets.metabrainz.org/browse/PICARD-210) - Make it easier to remove everything currently loaded in Picard
- [PICARD-222](https://tickets.metabrainz.org/browse/PICARD-222) - Bring back keyboard shortcuts for editing tags
- [PICARD-229](https://tickets.metabrainz.org/browse/PICARD-229) - Case sensitivity for "Move additional files" option
- [PICARD-253](https://tickets.metabrainz.org/browse/PICARD-253) - Metadata comparison box shows that it intends to write (and has written) tags unsupported by   underlyingfile format
- [PICARD-267](https://tickets.metabrainz.org/browse/PICARD-267) - Add more descriptive tooltips to buttons
- [PICARD-268](https://tickets.metabrainz.org/browse/PICARD-268) - Allow musicip_puid and acoustid_id to be cleared from tags
- [PICARD-287](https://tickets.metabrainz.org/browse/PICARD-287) - Make it possible to remove existing tags without clearing all tags
- [PICARD-291](https://tickets.metabrainz.org/browse/PICARD-291) - Disable recurse subdirectories should be added
- [PICARD-305](https://tickets.metabrainz.org/browse/PICARD-305) - display how many "pending files" left on lookup
- [PICARD-307](https://tickets.metabrainz.org/browse/PICARD-307) - Handle MP3 TSST/TIT3 (subtitle) tags better with ID3v2.3
- [PICARD-353](https://tickets.metabrainz.org/browse/PICARD-353) - Customisable toolbars
- [PICARD-359](https://tickets.metabrainz.org/browse/PICARD-359) - Ignore file extension and try to read anyway
- [PICARD-384](https://tickets.metabrainz.org/browse/PICARD-384) - Make it possible to unset all performer (etc) tags
- [PICARD-388](https://tickets.metabrainz.org/browse/PICARD-388) - Progress tracking
- [PICARD-404](https://tickets.metabrainz.org/browse/PICARD-404) - Add ability to handle multiple tagger scripts
- [PICARD-476](https://tickets.metabrainz.org/browse/PICARD-476) - the option "select all" to save
- [PICARD-514](https://tickets.metabrainz.org/browse/PICARD-514) - Option to load only audio tracks, i.e. not DVD-Video, CD-ROM tracks
- [PICARD-615](https://tickets.metabrainz.org/browse/PICARD-615) - Picard should use OAuth for authentication
- [PICARD-648](https://tickets.metabrainz.org/browse/PICARD-648) - Improvements to WMA tags
- [PICARD-678](https://tickets.metabrainz.org/browse/PICARD-678) - Only ask to "log in now" once per session
- [PICARD-683](https://tickets.metabrainz.org/browse/PICARD-683) - Show codec info for MP4 files
- [PICARD-692](https://tickets.metabrainz.org/browse/PICARD-692) - "Play File" button should be renamed to "Open in Player"
- [PICARD-695](https://tickets.metabrainz.org/browse/PICARD-695) - ID3 padding not reduced can result in large files
- [PICARD-705](https://tickets.metabrainz.org/browse/PICARD-705) - Set option 'caa_approved_only' disabled by default
- [PICARD-707](https://tickets.metabrainz.org/browse/PICARD-707) - Validate fpcalc executable in options
- [PICARD-733](https://tickets.metabrainz.org/browse/PICARD-733) - Improve File Naming options
- [PICARD-734](https://tickets.metabrainz.org/browse/PICARD-734) - Add --long-version/-V option, outputting third parties libs versions as well as Picard version
- [PICARD-740](https://tickets.metabrainz.org/browse/PICARD-740) - missing info in the help file
- [PICARD-773](https://tickets.metabrainz.org/browse/PICARD-773) - Pass command-line arguments to QtApplication
- [PICARD-777](https://tickets.metabrainz.org/browse/PICARD-777) - Use the more detailed icons in more places on windows
- [PICARD-794](https://tickets.metabrainz.org/browse/PICARD-794) - Use .ini configuration file on all platforms
- [PICARD-806](https://tickets.metabrainz.org/browse/PICARD-806) - Use python2 shebang as of PEP 0394
- [PICARD-808](https://tickets.metabrainz.org/browse/PICARD-808) - Display existing covers in File Info dialog
- [PICARD-818](https://tickets.metabrainz.org/browse/PICARD-818) - Use HTTPS for external links
- [PICARD-838](https://tickets.metabrainz.org/browse/PICARD-838) - Install a scalable icon
- [PICARD-852](https://tickets.metabrainz.org/browse/PICARD-852) - Use HTTPS for requests to the plugins API on picard.musicbrainz.org
- [PICARD-864](https://tickets.metabrainz.org/browse/PICARD-864) - Use magic numbers to determine the audio file types instead of relying on extensions
- [PICARD-883](https://tickets.metabrainz.org/browse/PICARD-883) - Multi-scripting UI is very basic
- [PICARD-887](https://tickets.metabrainz.org/browse/PICARD-887) - Allow scripting functions to have arbitrary number of arguments
- [PICARD-890](https://tickets.metabrainz.org/browse/PICARD-890) - The "Restore defaults" confirmation buttons should follow the quit confirmation dialog in style
- [PICARD-896](https://tickets.metabrainz.org/browse/PICARD-896) - Replace submit icon with AcoustID logo
- [PICARD-897](https://tickets.metabrainz.org/browse/PICARD-897) - Rename "Submit" button to "Submit AcoustIDs"
- [PICARD-898](https://tickets.metabrainz.org/browse/PICARD-898) - Use UTF-8 for ID3v2.4 by default instead of UTF-16
- [PICARD-902](https://tickets.metabrainz.org/browse/PICARD-902) - Restore defaults is slightly broken for tags option page
- [PICARD-908](https://tickets.metabrainz.org/browse/PICARD-908) - Rearrange the action toolbar icons from left to right according to the expected user-flow
- [PICARD-913](https://tickets.metabrainz.org/browse/PICARD-913) - Add tooltips to “Restore all Defaults” and “Restore Defaults”
- [PICARD-918](https://tickets.metabrainz.org/browse/PICARD-918) - Make PICARD-883 UI have adjustable widths for list of scripts and script content
- [PICARD-919](https://tickets.metabrainz.org/browse/PICARD-919) - Move Options/Advanced/Scripting to Options/Scripting
- [PICARD-921](https://tickets.metabrainz.org/browse/PICARD-921) - Move UI options page up the options tree
- [PICARD-923](https://tickets.metabrainz.org/browse/PICARD-923) - Add `$startswith` and `$endswith` string functions
- [PICARD-924](https://tickets.metabrainz.org/browse/PICARD-924) - Make list of scripts smaller than script text by default
- [PICARD-944](https://tickets.metabrainz.org/browse/PICARD-944) - Wait for save thread pool to be finished before exit
- [PICARD-970](https://tickets.metabrainz.org/browse/PICARD-970) - New guess format functionality should use explicit buffer size


# Version 1.3.2 - 2015-01-07
  - Bugfix: Fixed tags from filename dialog not opening on new installations


# Version 1.3.1 - 2014-12-20
## Bugfixes
- [PICARD-273](https://tickets.metabrainz.org/browse/PICARD-273) - Picard should use the correct Accept header when talking to web services.
- [PICARD-589](https://tickets.metabrainz.org/browse/PICARD-589) - Picard refuses to load files if any path component happens to be hidden
- [PICARD-642](https://tickets.metabrainz.org/browse/PICARD-642) - ConfigUpgradeError: Error during config upgrade from version 0.0.0dev0 to 1.0.0final0
- [PICARD-649](https://tickets.metabrainz.org/browse/PICARD-649) - Windows installer sets working directory to `%PROGRAMFILES%\MusicBrainz Picard\locale`
- [PICARD-655](https://tickets.metabrainz.org/browse/PICARD-655) - Last.fm plus tooltip help elements are all messed up
- [PICARD-661](https://tickets.metabrainz.org/browse/PICARD-661) - Regression: Tagger script for cover art filename does not work anymore
- [PICARD-662](https://tickets.metabrainz.org/browse/PICARD-662) - Retrieving collections causes AttributeError: release_list
- [PICARD-663](https://tickets.metabrainz.org/browse/PICARD-663) - Artist name makes it impossible to save

## Improvements
- [PICARD-658](https://tickets.metabrainz.org/browse/PICARD-658) - Support the new pregap and data tracks
- [PICARD-659](https://tickets.metabrainz.org/browse/PICARD-659) - Set the originalyear tag when loading a release
- [PICARD-665](https://tickets.metabrainz.org/browse/PICARD-665) - Web service calls to ports 80 and 443 do not need explicit port specification. 443 should be automatically made https.


# Version 1.3 - 2014-10-20
- The "About" window now displays the versions of libraries used by Picard
- Picard now correctly handles matching of MP3 files saved in ID3v2.3 tags
  (which is the version that Microsoft Windows and iTunes both use).
  Note: You may need to re-save your tags once to get them to match in future.
- A sort tags plugin is now provided as tag data is no longer displayed sorted by default.
- A new tag, musicbrainz_releasetrackid, containing the MusicBrainz Track MBID
  introduced in the May 2013 schema change release, is now written to files.
- [PICARD-515](https://tickets.metabrainz.org/browse/PICARD-515) - Add `%_recordingtitle%`
- [PICARD-444](https://tickets.metabrainz.org/browse/PICARD-444) - Fix plugin install bugs
- [PICARD-516](https://tickets.metabrainz.org/browse/PICARD-516) - Fix Options / File naming examples to handle primary/secondary release types
- A new advanced option is available to permanently set the starting directory
  for the file browser and "Add files/folder" buttons.
- [PICARD-337](https://tickets.metabrainz.org/browse/PICARD-337) - Requests to Musicbrainz against your own account e.g. for collections are now handled through SSL
- Refresh of Albums using Ctrl-R and selection of Other Releases are now more responsive during batch lookups.
- Main window is now emitting a "selection_updated" signal, plugin api version bumps to 1.3.0
- Append system information to user-agent string
- Compilation tag/variable functionality (for tagging & file naming) has been split into two:
  - `%compilation%` is now aligned with iTunes, and set only for Various Artists type compilations
  - `%_multiartist%` variable now indicates whether this release has tracks by multiple artists
    (in order to prepend the artist name to the filename as shown in the default file naming script)
- [PICARD-123](https://tickets.metabrainz.org/browse/PICARD-123) - autodetect the CD drive on Mac OS X
- [PICARD-528](https://tickets.metabrainz.org/browse/PICARD-528) - Ignore directories and files while indexing when show_hidden_files option is set to False
- [PICARD-528](https://tickets.metabrainz.org/browse/PICARD-528) - Add ignore_regex option which allows one to ignore matching paths, can be set in Options > Advanced
- Added an "artists" multi-value tag to track metadata, based on the one in Jaikoz, which contains the individual
  artist names from the artist credit. Also useful in scripts (joining phrases like 'feat:' are omitted) and plugins.
- Added `%_artists_sort%`, `%_albumartists%`, `%_albumartists_sort%` variables for scripts and plugins.
- [PICARD-205](https://tickets.metabrainz.org/browse/PICARD-205) - Made Picard use the country names also used on the MusicBrainz website
- New setup.py command `get_po_files` (Retrieve po files from transifex)
- New setup.py command `regen_pot_file` (Regenerate po/picard.pot)
- New Work tag (which for Classical music is often different from the track title) saved as ID3 TOAL tag.
- New Composer Sort Order tag (variable `%composersort%`).
- Improve the Other Releases list to prioritise and separate releases which match the correct number of tracks
  and your Options / Metadata / Preferred Releases settings for Country and Format.
- New `%_absolutetracknumber%` variable numbering tracks sequentially regardless of disc structure
  (so you can numbers tracks on multi-disc releases without a disc number)
- Support dropping image directly from Google image results to cover art box
- Add `%_musicbrainz_tracknumber%` to hold track # as shown on MusicBrainz release
  web-page e.g. vinyl/cassette style A1, A2, B1, B2
- [PICARD-218](https://tickets.metabrainz.org/browse/PICARD-218) - Show the ID3 version of the file in the Info... dialog (Ctrl-I)
- [PICARD-112](https://tickets.metabrainz.org/browse/PICARD-112) - Fixed a bug where Picard crashed if a MP3 file had malformed TRCK or TPOS tags
- [PICARD-566](https://tickets.metabrainz.org/browse/PICARD-566) - Add --files option to setup.py build_ui, used to force .ui to .py regeneration
- New setup.py command `update_constants` (Regenerate countries.py and attributes.py)
- Made Picard use release groups, medium formats and cover art types also used on the MusicBrainz website
- Use MusicBrainz Server translations for release groups, medium formats and cover art types
- Add checkbox to toggle debug at runtime in log/debug view dialog
- Add a plugin to add Artist Official Homepage relationships to the website tag (ID3 WOAR tag)
- Add integrated functions `$eq_any`, `$ne_all`, `$eq_all`, `$ne_any`, `$swapprefix` and `$delprefix`.
- Add `%_performance_attributes%`, containing performance attributes for the work
  e.g. live, cover, medley etc.
  Use `$inmulti` in file naming scripts i.e.
  `$if($inmulti(%_performance_attributes%,medley), (Medley),)`
- Add optional `priority` parameter to `register_album_metadata_processor()` and
  `register_track_metadata_processor()`
  Default priority is `PluginPriority.NORMAL`, plugins registered with
  `PluginPriority.HIGH` will be run first, plugins registered with
  `PluginPriority.LOW` will run last
- Add Standardise Performers plugin to convert e.g. Performer [piano and guitar] into
  Performer [piano] and Performer [guitar].
- [PICARD-418](https://tickets.metabrainz.org/browse/PICARD-418), [PICARD-53](https://tickets.metabrainz.org/browse/PICARD-53) - Add support for release group cover art fallback
- Add a clear button to search box
- [PICARD-631](https://tickets.metabrainz.org/browse/PICARD-631) - Honour preferred release formats when matching AcoustIds
- [PICARD-630](https://tickets.metabrainz.org/browse/PICARD-630) - Prevent ZeroDivisionError in some rare cases


# Version 1.2 - 2013-03-30
- Picard now requires at least Python 2.6
- Removed support for AmpliFIND/PUIDs
- Add support for the Ogg Opus file format
- It's now possible to download cover images without any plugin. Cover Art Archive images can be downloaded by image type
- Improved directory scanning performance
- Prefer already-loaded releases of the same RG when matching files
- Allow dropping new files onto specific targets
- [PICARD-84](https://tickets.metabrainz.org/browse/PICARD-84) - Add basic collections management support
- [PICARD-349](https://tickets.metabrainz.org/browse/PICARD-349) - Allow adding custom tags in the tag editing dialog
- [PICARD-393](https://tickets.metabrainz.org/browse/PICARD-393) - Fix replacing of Windows-incompatible characters
- [PICARD-240](https://tickets.metabrainz.org/browse/PICARD-240) - Save both primary and secondary release types
- [PICARD-391](https://tickets.metabrainz.org/browse/PICARD-391) - Handle errors from the AcoustID service better
- [PICARD-378](https://tickets.metabrainz.org/browse/PICARD-378) - Accept HTTPS URLs on drag-and-drop


# Version 1.1 - 2012-09-03
- [PICARD-201](https://tickets.metabrainz.org/browse/PICARD-201) - Always show basic tags in metadata comparison box, even if empty (title, artist, album, tracknumber, ~length, date)
- [PICARD-82](https://tickets.metabrainz.org/browse/PICARD-82) - Fixed AcoustID submission failure after removing files from Picard
- [PICARD-194](https://tickets.metabrainz.org/browse/PICARD-194) - Allow multi-select in new MetaDataBox for delete/remove tags
- [PICARD-104](https://tickets.metabrainz.org/browse/PICARD-104) - File browser remembers last directory/no longer crashes on OS X
- [PICARD-11](https://tickets.metabrainz.org/browse/PICARD-11) - Removed the "Run Picard" option from the Windows installer
- [PICARD-220](https://tickets.metabrainz.org/browse/PICARD-220) - Refreshing a non-album track correctly clears previous track metadata
- [PICARD-217](https://tickets.metabrainz.org/browse/PICARD-217) - Fixed the preserved tags setting for tags with uppercase characters
- Added a completion box to the preserved tags setting, and clarified how it works
- [PICARD-242](https://tickets.metabrainz.org/browse/PICARD-242) - Store lyrics language in tags instead of text representation language
- [PICARD-255](https://tickets.metabrainz.org/browse/PICARD-255), [PICARD-256](https://tickets.metabrainz.org/browse/PICARD-256) - Fix various oddities in the metadata comparison box


# Version 1.0 - 2012-06-02
- [PICARD-43](https://tickets.metabrainz.org/browse/PICARD-43) - New UI: Extended comparison of existing vs. MB metadata & tags
- Merged the renaming and moving options pages
- [PICARD-159](https://tickets.metabrainz.org/browse/PICARD-159) - Removed the VA file naming format option (there is now a single format option)
- Add `%license%` tag
- [PICARD-21](https://tickets.metabrainz.org/browse/PICARD-21) - Made `%writer%` available to tagger scripts and plugins with contents of songwriter
- [PICARD-139](https://tickets.metabrainz.org/browse/PICARD-139) - Allow two multi-valued variables to be merged in tagger scripting
- [PICARD-147](https://tickets.metabrainz.org/browse/PICARD-147) - Allow multi-valued variables to be transformed in tagger script and then set back in tags as multi-valued
- [PICARD-138](https://tickets.metabrainz.org/browse/PICARD-138) - Fix `$copy` not preserving multi-value variables as documented
- [PICARD-148](https://tickets.metabrainz.org/browse/PICARD-148) - Load/save free-text tags for ID3 as TXXX frames
- [PICARD-88](https://tickets.metabrainz.org/browse/PICARD-88) - Fix writing of MusicBrainz Work Id / musicbrainz_workid to tags
- [PICARD-27](https://tickets.metabrainz.org/browse/PICARD-27) - Handle mimetype for embedding cover art from EXIF jpegs
- Change cover art box to open MusicBrainz release rather than Amazon
- Support manual drag-and-drop of cover art onto a release via cover art box
- [PICARD-190](https://tickets.metabrainz.org/browse/PICARD-190) - Only open browser on left-click of cover art box
- [PICARD-186](https://tickets.metabrainz.org/browse/PICARD-186) - Fix Lookup in Browser (previously 'tag lookup') for clusters
- Lookup in Browser will now not use MBIDs to lookup unmatched files/clusters
- [PICARD-198](https://tickets.metabrainz.org/browse/PICARD-198) - Add Date/Country to CD Lookup results dialog
- [PICARD-4](https://tickets.metabrainz.org/browse/PICARD-4) - Fix/reset album folksonomy tag counts while refreshing releases
- Plugins actions can now create sub-menus using the MENU class attribute
- New plugin hook `register_clusterlist_action`
- [PICARD-191](https://tickets.metabrainz.org/browse/PICARD-191) - Display the port Picard is listening on at bottom right status bar
- [PICARD-33](https://tickets.metabrainz.org/browse/PICARD-33) - Make album drops from right hand pane to left default to "unmatched files" again
- [PICARD-75](https://tickets.metabrainz.org/browse/PICARD-75) - Remove .DS_Store, desktop.ini, and Thumbs.db from otherwise empty directories
- [PICARD-200](https://tickets.metabrainz.org/browse/PICARD-200) - Update artist translation to use new alias features (primary flag, sort names)
- [PICARD-165](https://tickets.metabrainz.org/browse/PICARD-165) - Deleted tags aren't indicated as changes
- [PICARD-45](https://tickets.metabrainz.org/browse/PICARD-45) - Picard log entries have inaccurate timestamp
- [PICARD-103](https://tickets.metabrainz.org/browse/PICARD-103) - Interface doesn't allow keyboard only management
- [PICARD-31](https://tickets.metabrainz.org/browse/PICARD-31) - Added option to preserve timestamps of tagged files
- [PICARD-99](https://tickets.metabrainz.org/browse/PICARD-99) - Added keyboard shortcut to reload release
- [PICARD-91](https://tickets.metabrainz.org/browse/PICARD-91) - Medium formats weren't listed in order in the "Other versions" menu
- [PICARD-74](https://tickets.metabrainz.org/browse/PICARD-74) - Couldn't select multiple directories in "Add Folder" window on OS X


# Version 0.16 - 2011-10-23
- Added AcoustID support.
- Fixed track metadata plugins.
- [PICARD-16](https://tickets.metabrainz.org/browse/PICARD-16) - Added new internal `%_totalalbumtracks%` tag field.
- [PICARD-7](https://tickets.metabrainz.org/browse/PICARD-7) - Track metadata plugins now run also on non-album tracks.
- [PICARD-5](https://tickets.metabrainz.org/browse/PICARD-5) - Fixed custom Various Artists name on the `%albumartist%` field.
- [PICARD-1](https://tickets.metabrainz.org/browse/PICARD-1) - Album artist is now correctly "translated".
- Unicode punctuation is now converted to ASCII by default.
- [PICARD-15](https://tickets.metabrainz.org/browse/PICARD-15) - WavPack correction files are moved together with the main files.
- Unicode filename normalization on OS X.
- Original release date is now saved into `%originaldate%`.
- [PICARD-17](https://tickets.metabrainz.org/browse/PICARD-17) - Allow tagging with localized artist aliases
- [PICARD-46](https://tickets.metabrainz.org/browse/PICARD-46) - Added a quit confirmation dialog.
- [PICARD-10](https://tickets.metabrainz.org/browse/PICARD-10) - Standalone recordings can be tagged with relationships now.
- [PICARD-8](https://tickets.metabrainz.org/browse/PICARD-8) - Refreshing an album will refresh its "other versions" listing.
- [PICARD-50](https://tickets.metabrainz.org/browse/PICARD-50) - "Unicode punctuation to ASCII" now works on album-level metadata.
- [PICARD-20](https://tickets.metabrainz.org/browse/PICARD-20) - DJ-mix tags should only be written to the medium where they apply.
- [PICARD-54](https://tickets.metabrainz.org/browse/PICARD-54) - Support URL redirects in web service/network request module
- [PICARD-52](https://tickets.metabrainz.org/browse/PICARD-52) - Jamendo and Archive.org cover art is displayed on web page, but not loaded by Picard plugin
- [PICARD-13](https://tickets.metabrainz.org/browse/PICARD-13) - Edits to metadata in "Details..." menu not reflected in UI
- [PICARD-14](https://tickets.metabrainz.org/browse/PICARD-14) - The status bar/new metadata box is updated when a selected file/track is changed.


# Version 0.15.1 - 2011-07-31
- "Other versions" menu now displays release labels and catalog numbers.
- Added CD-R, 8cm CD to the format mapping.
- Picard no longer fails to load releases with new or unknown media formats.
- Threading issues that could occasionally cause Picard to stop loading files have been fixed.
- Fixed album metadata processor plugins not working (#5960)
- Fixed loading of standalone recordings (#5961)
- Fixed requests stopping at midnight (#5963)
- Stopped using QDateTime for timing requests (for Qt 4.6 compatibility) (#5967)
- Fixed display of ampersands in the "other versions" menu. (#5969)
- Fixed use of numerical functions in advanced scripting.


# Version 0.15 - 2011-07-17
- Added options for using standardized track, release, and artist metadata.
- Added preferred release format support.
- Expanded preferred release country support to allow multiple countries.
- Added support for tagging non-album tracks (standalone recordings).
- Plugins can now be installed via drag and drop, or a file browser.
- Added several new tags: `%_originaldate%`, `%_recordingcomment%`, and `%_releasecomment%`
- Changes to request queuing: added separate high and low priority queues for each host.
- Tagger scripts now run after metadata plugins finish (#5850)
- The "compilation" tag can now be `$unset` or modified via tagger script.
- Added a shortcut (Ctrl+I) for Edit->Details.
- Miscellaneous bug fixes.


# Version 0.15beta1 - 2011-05-29
- Support for the NGS web service


# Version 0.14 - 2011-05-15
- Fixed a problem with network operations hanging after a network error (#5794, #5884)
- ID3v2.3 with UTF-16 is now the default ID3 version
- Option to set preferred release types for improved album matching
- Added support for sorting the album/file lists (#75)
- Fixed OptimFROG tag reading (#5859)
- Fixed colors for a white-on-black color scheme (#5846)
- Added an option to replace non-ASCII punctuation (#5834)
- Support for writing release group and work IDs, currently unused (#5805)
- Fixed saving of the release event format tag (#5250)
- Added support for the language and script tags (#943)
- Plugins can now use track-track relationships (#5849)
- Allowed external drives to be visible in the file browser panel on OS X (#5308)


# Version 0.13 - 2011-03-06
- Changed Picard icon license to CC by-sa
- Small UI consistency changes
- Albums with tracks linked to more than one file are never marked as
  "completed".
- Fixed matching of scanned files to tracks while the album is still loading.
- Support for properly embedded FLAC pictures
- Existing embedded images in APE and ASF files are removed only if there
  are new images to replace them.
- More strict tagger script validation.
- Fixed the `$truncate` tagger script function.
- Proper rounding of track durations.
- Fixed a bug with saving images larger than 64k to WMA files.
- Added a `$swapprefix` tagger script function.
- Release events with a date are preferred over the ones without a date.
- Files that are being saved as marked as pending.
- Updated .desktop file to allow opening Picard with multiple files.
- Handle the "open file" event on Mac OS X.
- Added timeouts to the HTTP web service client.
- Fixed a bug with albums missing the expand/collapse icons


# Version 0.12.1 - 2009-11-01
- Fixed deletion of all COMM frames in ID3, which was introduced with the
  iTunNORM fix in Picard 0.12.0.
- Restored native add folder dialog.


# Version 0.12 - 2009-10-25
- Live syntax checking for tagger script and naming strings.
  (Nikolai Prokoschenko)
- Support ratings. (Philipp Wolfer)
- Support for user folskonomy tags. (Lukáš Lalinský)
- Embed cover art into APEv2 tags. (Lukáš Lalinský)
- Embed cover art into WMA tags. (Philipp Wolfer)
- New high quality application icon (Carlin Mangar)
- Support for originaldate tag. (Philipp Wolfer)
- Restructured file naming options. (Nikolai Prokoschenko)
- Added option to select the user interface language. (Philipp Wolfer)
- Highlight fully matched albums. (Nikolai Prokoschenko)
- New script functions `$matchedtracks()`, `$initials()`, `$firstalphachar()`,
  `$truncate()` and `$firstwords()`
- CD drive dropdown selection on Linux. (Philipp Wolfer)
- Add disc ID to album metadata if loaded via disc lookup. (Philipp Wolfer)
- Add expand/collapse all actions to tree views. (Philipp Wolfer)
- Added DCC media format.
- Removed unncecessary and confusing PUID lookup threshold. (Philipp Wolfer)
- Fixed saving of copyright in ASF metadata. (#5419, Philipp Wolfer)
- Write TRACKTOTAL and DISCTOTAL to vorbis files. (#4088, Philipp Wolfer)
- Added keyboard shortcut to toggle file browser (#3954, Philipp Wolfer)
- Write ISRCs from MusicBrainz into tags (Philipp Wolfer)
- UI improvements on cover art box and icons (Carlin Mangar)
- New Windows installer (Carlin Mangar)
- New plugin extension point ui_init (Gary van der Merwe)
- Updated plugin options page (Carlin Mangar)
- Python 2.6 fixes. (Gary van der Merwe)
- Fix PUID generation on big endian machines. (Jon Hermansen)
- Fix lookup encoding for non latin characters. (#5233, Philip Jägenstedt)
- Fix infinite loop when using Qt 4.5. (Lukáš Lalinský)
- Ensure 16-byte memory alignment for avcodec, fixes issues with enabled SSE2
  instructions. (#5263, Philipp Wolfer)
- Use default CD device for disc ID lookups if no device was specified.
  (Philipp Wolfer)
- Preserve file information (bitrate, extension etc.) on saving.
  (#3236, Philipp Wolfer)
- Allow empty release events (#4818, Philipp Wolfer)
- Respect the option "clear existing tags" when saving WMA files.
  (Philipp Wolfer)
- Detect image format of cover images. (#4863, Philipp Wolfer)
- Don't load CD stubs. (#4251, Philipp Wolfer)
- Set match background color relative to the base color. (#4740, Philipp Wolfer)
- Fix infinite loop when using Qt 4.5. (Lukáš Lalinský)
- Fixed various issues with the PUID submission button. (Philipp Wolfer)
- Fixed copy and paste (#5428, Philipp Wolfer)
- Fixed loading of files with corrupted PUIDs (#5331, Carlin Mangar)
- Fixed redirection handling (Lukáš Lalinský)
- Fixed writng of iTunNORM tags in ID3 (Carlin Mangar)
- Always restore window position so that the window is visible (Carlin Mangar)
- Updated translations.


# Version 0.11 - 2008-12-02
- Support for new FFmpeg install locations
- Automatically remove whitespaces from MB hostname in options
- Release date from MB is now optional
- Fixed per-track folksonomy tag support
- Evaluate tagger script for album metadata
- Show donation info in the about dialog
- Support for .oga files (Ogg FLAC, Ogg Speex or Ogg Vorbis)
- Fixed loading of performer tags from Vorbis Comments
- Load embedded cover art from COVERART/COVERARTMIME Vorbis Comments
- Allow setting the "Move Files To" location from the internal file browser
- Copy&paste support in the file details dialog
- Correct handling of "; " as a separator for sort names
- Minimal support for TAK files
- Fixed parsing of the "Pseudo-Release" release status
- Fixed reading performers with empty role from ID3 tags
- Don't allow empty file naming formats
- Interactive password dialog
- Fixed checking for non-Latin characters when using sort name as the main
  artist name


# Version 0.10 - 2008-07-27
- Fixed crash when reading CD TOC on 64-bit systems
- Fixed handling of MP4 files with no metadata
- Change the hotkey for help to the right key for OS X
- Replace special characters after tagger script evaluation to allow
  special characters being replaced by tagger script
- Actually ignore 'ignored (folksonomy) tags'
- Remove dependency on Mutagen 1.13, version 1.11 is enough now
- Escape ampersand in release selection (#3748)


# Version 0.10.0rc1 - 2008-05-25
- Stop analyzing files that have been removed. (#3352, Gary van der Merwe)
- Automatically disable CD lookup if no CD device is specified.
  (Will Holcomb)
- Don't abort directory reading on invalid filename. (#2829, amckinle)
- Add an option to select multiple directories from the 'Add Directory'
  window. (#3541, Will Holcomb)
- Avoid scanning files that had been removed from the tagger.
  (#3352, Gary van der Merwe)
- Folksonomy tags/genre support. (Lukáš Lalinský)
- Added menu items (with keyboard shortcuts) for CD lookup / Scan /
  Lookup / Cluster. (Lukáš Lalinský)
- Add taggerscript function `$performer()`. (Lukáš Lalinský)
- Lower the default PUID lookup threshold to 10%. (Lukáš Lalinský)
- Compare tracknumber and totaltracks as numbers, not strings.
  (Lukáš Lalinský)
- Correctly escape special Lucene characters for searches/lookups.
  (#3448, Lukáš Lalinský)
- Use MusicIP Mixer "archived analysis" to speed up PUID lookups.
  (Lukáš Lalinský)
- Add language and script to variables. (#3635, Nikki)
- Option to initiate searches with advanced query syntax on by default.
  (#3526, Lukáš Lalinský)
- "Save Tags" item in options menu. (#3519, Lukáš Lalinský)
- Create empty "plugins" directory by default on installation.
  (#3529, Lukáš Lalinský)
- Added default release country option. (#3452, Philipp Wolfer)
- Added release format type to release selection. (#3074, Philipp Wolfer)
- Convert Vorbis tag "tracktotal" to "totaltracks" on load. (Philipp Wolfer)
- Save 'arranger' to ID3 tags. (Lukáš Lalinský)
- Store cover art in Ogg and FLAC files. (#3647, Hendrik van Antwerpen)
- Album title not updated when related 'Unkown files' are modified.
  (#3682, Hendrik van Antwerpen)
- Match selected release event to existing files.
  (#3687, Hendrik van Antwerpen)
- Allow multiple files to be linked to a single track.
  (#3729, Gary van der Merwe)
- Don't use mmap to resize files on Windows. (Lukáš Lalinský)


# Version 0.9.0 - 2007-12-16
- More custom tags in MP4 files (compatible with MediaMonkey and Jaikoz) (#3379)
- Fixed MP4 fingerprinting on Windows. (#3454, #3374)
- Fixed CD lookups on Windows. (#3462, #3362, #3386)
- Set the `%compilation%` tag correctly. (#3263)
- Fixed location of saved cover art files. (#3345)
- The Picard window now won't start as hidden. (#2104, #2429)
- Fixed reading of length of MP3 files with VBRI headers. (#3409)
- Fixed WMA saving. (#3417)
- Fixed saving of comment to ID3 tags. (#3418)
- New mapping of "chorus master" AR to "conductor" tag.
- Fixed system-wide plugin path on Linux. (#3430)
- Use the earliest release date by default. (#3456)


# Version 0.9.0beta1 - 2007-10-28
- Save ASIN to MP4 files.
- Add a `--disable-locales` option to `setup.py build`. (Santiago M. Mola)
- New threading code, should make Picard crash less and be faster.
- Replace initial dot in file and directory names. (#3204, Philipp Wolfer)
- Fixed caps in the default cover art image. (#3242, Bogdan Butnaru)
- Fixed broken naming preview. (#3214, Daniel Bumke)
- Re-enable the drag/drop target indicators. (#3106)
- Fix adding files and directories from the command line. (#3075)
- Don't show the cover art box by default.
- Lookup files individually for "Unmatched Files", not as a cluster.


# Version 0.9.0alpha14 - 2007-08-05
- Fixed PUID submissions.
- Fixed drag&drop from Finder to Picard on Mac OS X.
- Don't save files from "Unmatched Files" when saving an album.
- Renamed "Analyze" to "Scan", to avoid confusion with MusicIP Mixer analysis.
- Added plugin API versioning. Plugins now need to define constant
  `PLUGIN_API_VERSIONS`, otherwise they won't be loaded.
- Added option to overwrite cover art by default.
- Never wait more than second for the next HTTP request.
- Fixed setting of the "Move Tagged Files To" folder, if the name contains
  non-ASCII characters.


# Version 0.9.0alpha13 - 2007-07-29
## Bugfixes
- Fixed drag&drop issue on Windows Vista.
  http://forums.musicbrainz.org/viewtopic.php?id=693


# Version 0.9.0alpha12 - 2007-07-29
## Changes
- "User directory" location changed:
  - On Windows from "%HOMEPATH%\Local Settings\Application Data\MusicBrainz Picard"
    to "%HOMEPATH%\Application Data\MusicBrainz\Picard"
  - On UNIX from "~/.picard" to "$XDG_CONFIG_HOME/MusicBrainz/Picard"
    (usually "~/.config/MusicBrainz/Picard")
- Picard no longer logs every action and doesn't saves the logs. To enable
  more debug logging, use command line argument "-d" or "--debug" or
  environment variable "PICARD_DEBUG".
- For plugins:
  - `metadata["~#length"]` is now `metadata.length`
  - `metadata["~#artwork"]` is now `metadata.images`

## New Features
- Save embedded images to MP4 files.
- Added option to select release events for albums.
- Added internal log viewer.
- Track and file context menu hooks for plugins.

## Bugfixes
- Deleting files from clusters increments total time rather than
  decrementing it. (#2965)
- Update metadata boxes and cover art for selected items. (#2498)
- Display error message for tracks.
- Fixed drag-and-drop bugs on Mac OS X.
- Added `%releasecountry%` to the file renaming preview.
- Cluster multi-disc albums identified by tags, not (disc x). (#2555)


# Version 0.9.0alpha11 - 2007-05-27
## New Features
- Added "Edit" button to the tag editor.

## Bugfixes
- Fixed initialization of gettext translations.


# Version 0.9.0alpha10 - 2007-05-27
## New Features
- New TaggerScript function `$len(text)`. (#2843)
- Don't compress huge ID3 frames. (#2850)
- Move "Add Cluster As Release" to a plugin.
- Allow horizontal scrollbar in the file browser panel. (#2856)
- Removed "Basic" tab from the "Details" window, "Advanced" tab renamed to "Metadata".
- The tag editor can be used to edit multiple files. (#2893)

## Bugfixes
- F1 for Help instead of CTRL+H on Windows and Linux. (#2485, Nikolai Prokoschenko)
- Tabbing focus transition from search isn't as expected. (#2546, Nikolai Prokoschenko)
- Display an error message if launching a web browser failed.
- Fixed web-service error caused PUID submissions.
- Change function `$gt()`, `$gte()`, `$lt()`, `$lte()` to compare numbers, not strings. (#2848)
- Fixed kfmclient launching under KDE/Python 2.5.
- Fixed similarity calculation of non-latin texts. (#2891)
- Don't try to auto-analyze files with "loading" errors. (#2862)


# Version 0.9.0alpha9 - 2007-05-12
## New Features
- The tag editor now accepts free-text tag names.
- Load 'DJ-mixed by' AR data to `%djmixer%` tag.
- Load 'Mixed by' AR data to `%mixer%` tag.
- Delay the webservice client to do max. 1 request per second.
- Sort files in clusters by disc number, track number and file name. (#2547)
- Support for any text frame in special variable `%_id3:%`.
- Ignore empty ID3 text values.
- Windows installer:
  - Removed DirectX-based decoder.
  - FFmpeg compiled with AAC (faad2) support.

## Bugfixes
- Save XSOP frame to ID3v2.3 tags. (#2484)
- Use attributes like 'guest' or 'additional' also from generic performer ARs.
- Fixed capitalization of `%releasetype%` in file naming preview. (#2762)
- Fixed 'python setup.py build_ext' if py2app and setuptools are loaded.
- ID3v2.3 frame TDAT should be written in format DDMM, not MMDD. (#2770)
- Don't display an error on Ogg and FLAC files with no tags.
- Remove video files from the list of supported formats.
- Always use musicbrainz.org for PUID submissions. (#2764)
- Files/Pending Files count not reset/recalculated after removing files. (#2541)
- Removed files still get processed during fingerprinting. (#2738)
- Read only text values from APEv2 tags. (#2828)


# Version 0.9.0alpha8 - 2007-04-15
## New Features
- Notification of changed files in releases. (#2632, #2702)

## Bugfixes
- Don't open the file for analyzing twice. (#2733, #2734)
- Save ASIN and release country to ID3 tags. (#2484, #2456)
- Variable `%country%` renamed to `%releasecountry%`.
- Save release country to MP4 and WMA tags.
- Don't take unsupported tags into account when checking if the
  tags are 'complete' and the file should have 100% match. This
  fixes problems with showing the green check-marks for file
  with limited tag formats, like MP4 or WMA.
- Ignore missing tag in `$unset()`.


# Version 0.9.0alpha7 - 2007-04-14
## New Features
- Remember location in the file browser. (#2618)
- Added FFmpeg support on Windows (MP3, Vorbis,
  FLAC, WavPack and many other audio formats).
- Lowercase the extension on file renaming/moving. (#2701)
- TaggerScript function `$copy(new,old)` to copy metadata from
  variable `old` to `new`. The difference between `$set(new,%old%)`
  is that `$copy(new,old)` copies multi-value variables without
  flattening them.
- Added special purpose TaggerScript variable `%_id3:%` for direct
  setting of ID3 frames. Currently it supports only TXXX frames in format
  `%_id3:TXXX:<description>%`, for example:
  `$copy(_id3:TXXX:PERFORMERSORTORDER,artistsort)`.
- Support for WAV files. (#2537)
- Removed GStreamer-based decoder.
- Implemented `python setup.py install_locales`.

## Bugfixes
- Failed PUID submission deactivates the submit button. (#2673)
- Unable to specify album art file name mask. (#2655)
- Fixed incorrect copying of album metadata to tracks. (#2698)
- Added options to un-hide toolbars. (#2631)
- Fixed problem with saving extra performer FLAC tags
  containing non-ASCII characters. (#2719)
- Read only the first date from ID3v2.3 tags. (#2460)
- If the remembered directory for add dialogs and file browser was
  removed, try to find an existing directory in the same path.


# Version 0.9.0alpha6 - 2007-04-04
## New Features
- Added option --disable-autoupdate for 'build' and 'install' commands
  of the setup script. (#2551)
- Automatically parse track numbers from file names like 01.flac for better
  cluster->album matching with untagged files.
- Support for the new sorting tags in MP4 tags from iTunes 7.1.
- Strip white-space from directory names. (#2558)
- When replacing characters with their ascii equivalent, 'ß' should be
  replaced by 'ss'. (#2610)
- Track level performer ARs. (#2561)
- Remove leading and trailing whitespace from tags on file saving.
  (#892, #2665)
- Support for labels, catalog numbers and barcodes.

## Bugfixes
- Artist names from ARs should be translated, too.
- Freeze after answering no to "download the new version" prompt. (#2542)
- `%musicbrainz_albumid%` not working in file renaming. (#2543)
- Track time appears to display incorrectly if it's unknown on
     MusicBrainz. (#2548)
- Fixed problem with removing albums/files after submitting PUIDs (#2556)
- The user's script should be applied also to album metadata.
- Fixed moving of additional files from paths with "special" characters.

## Internals
- The browser integration HTTP server rewritten using QTcpServer.


# Version 0.9.0alpha5 - 2007-03-18
## New Features
- Replace Æ with AE in file/directory names. (#2512)
- "Add cluster as release" (#1049)
- Text labels under icon buttons. (#2476)

## Bugfixes
- Fixed fileId generator (caused problems with drag&drop
  if files with multiple formats are used).
- Original Metadata not greyed out when no tracks are attached. (#2461)
- Better detecting of the default Windows browser, with fallback to
  Internet Explorer. (#2502)
- Better album/track lookup. (#2521)
- File browser stays 'hidden' after first time use. (#2480)
- Track length changed in Original Metadata after save. (#2510)
- "Send PUIDs" button not disabled after albums are removed. (#2506)
- The Windows package now includes JPEG loader to show cover art
  images correctly. (#2478)


# Version 0.9.0alpha4 - 2007-03-09
## Bugfixes
- Fixed case-insentive file renaming. (#2457, #2513)


# Version 0.9.0alpha3 - 2007-03-08
## New Features
- Using of 'performed by' AR types (without instrument or vocal).
- The "Replace non-ASCII characters" option will try to remove
  accents first. (#2466)
- Added option to auto-analyze all files. (#2465)

## Bugfixes
- Fixed file clustering.
- Added `%albumartistsort%`, `%releasetype%` and `%releasestatus%` to the
  file naming example (#2458)
- Sanitize dates from ID3 tags. (#2460)
- Fixed page switching in the options window on error. (#2455)
- Correct case-insensitive file renaming on Windows (#1003, #2457)
- Relative paths in the "Move files to" option are relative to the
  current path of the file. (#2454)
- Added a .desktop file. (#2470)
- Release type and status should be in lower case. (#2489)


# Version 0.9.0alpha2 - 2007-03-04
## New Features
- New variable `%_extension%` (#2447)
- File naming format tester. (#2448)
- Added automatic checking for new versions.

## Bugfixes
- Fixed window position saving/restoring. (#2449)
- Fixed iTunes compilation flag saving. (#2450)


# Version 0.9.0alpha1 - 2007-03-03
- First release.
