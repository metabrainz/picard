#
# Copyright (C) 2026 Laurent Monin
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

"""The subjects ``help`` explains that are not a command.

Selectors, paths and tags are what people get stuck on, and they are the same
for every command, so they are explained once here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    """A subject of ``help``: its name, a line for the list, and the text."""

    name: str
    summary: str
    text: str


SELECTORS = Topic(
    'selectors',
    "How to name the objects a command acts on",
    """\
A selector names the objects a command acts on.

An object is named by its handle, a letter for its kind and a number:

  f1   a file
  c1   a cluster
  a1   an album (the standalone recordings are one too)
  t1   a track of an album
  m1   a candidate found by a lookup, see 'help cluster lookup'
  k1   a collection of releases of the user, see 'help collection ls'
  v1   another release of the release group of an album, see 'help album versions'

The commands print the handles of what they create, and 'ls' lists them. A
handle never changes and is never reused in a session, so a1 keeps naming the
same album as long as it is loaded. Only 'shell remint' mints the handles of a kind
from 1 again, when no object of that kind is left.

A selector is made of:

  a1          one object
  a*          all the objects of a kind (f* is the files that are in no cluster)
  f1-12       the objects of a kind from one number to another, those that exist
  *           everything at the top level: unclustered files, clusters, albums
  a1,c2       several of them (most commands also accept a space after the comma)
  a1.d2.t3    a path into the working set, see 'help paths'

A selector that matches nothing is reported as unresolved. When a selector is
optional, 'help <command>' tells what the command does without one.

Examples:
  ls a*
  save a1,c2
  tree c1""",
)

PATHS = Topic(
    'paths',
    "How to name a track, a disc or a file inside an album or a cluster",
    """\
A path reaches the objects inside another one: segments separated by dots, each
selecting children of the previous one.

  d<n>   disc n of an album
  t<n>   track n (of an album or of one of its discs)
  f<n>   file n (of an album, a disc, a track or a cluster)
  m<n>   candidate n of a lookup (of a cluster or a file)
  v<n>   version n of an album, a release of its release group, as 'album versions' lists them
  u      the files that are in no cluster; under an album, its unmatched files

A number can be * for all of them: a1.d*.t1 is the first track of every disc, or
a range: a1.t2-4 is tracks 2 to 4, and c1.f1-5 the first five files of a cluster.
A number of a range that does not exist is skipped.

Examples:
  a1.d2.t3    track 3 of disc 2 of album a1
  a1.t3       track 3, when the album has a single disc
  a1.f*       every file of the album, matched or not
  a1.u        the files of the album that were not matched to a track
  c1.f2       the second file of cluster c1
  c1.f1-5     the first five files of cluster c1
  c1.m2       the second candidate found for cluster c1
  a1.v3       the third version listed for album a1
  u.f*        the files that are in no cluster

Discs and tracks have the numbers the release gives them (the discnumber and
tracknumber tags), not their position, so a1.d2.t3 keeps its meaning if the
album is reloaded. If the album has several discs, the disc must be named. The
other numbers are positions in the order the listing shows.

A path says where something is now. The handle of an object (f7, t12) is what
stays the same when it moves, so keep that if you want to refer to it later.
Commands print the path next to the handle, and the Tab key completes paths.""",
)

TAGS = Topic(
    'tags',
    "How to name the tags the 'metadata' commands act on",
    """\
A tag is not an object and has no handle: it is a word after the selector, as in
'metadata show a1 artist'. For this reason the selector must be a single word
there (f1,f2 and not f1, f2).

A tag is its name, or a pattern: * matches any characters, ? one character, and
[...] one of a set. 'metadata show' and 'metadata rm' accept patterns; to set a
tag ('metadata set', 'metadata add') give its name, and its values after it.
Tags that start with ~ are variables of the scripts and cannot be set.

A tag can have several values. Each word given to 'metadata set' or 'metadata add'
is one value ('metadata set f1 genre Rock Pop' gives two), 'metadata rm-value'
takes some out, and 'metadata rm' removes the tag. 'metadata show' joins the
values with '; ' to display them, but a value is never split on it: "Rock; Pop"
is one value. The words given to a tag that holds a single value, such as
title, are one value too ('metadata set f1 title A Song'); quote a value to keep
its spaces as they are, see 'help quoting'.

  artist            the artist tag
  musicbrainz_*     all the tags that start with musicbrainz_
  performer:*       all the performers (the colon is part of the name)

Without any tag, all the tags the metadata box of the GUI would show are
listed. A pattern that matches nothing is reported.

A file has the tags it was loaded with and the ones it would be saved with, and
a tag is shown as unchanged, changed (old -> new), added (+) or removed (-).
A track, an album or a cluster stands for its files, and the values that differ
between them are grouped: 'title (different across 3 items)'.""",
)

QUOTING = Topic(
    'quoting',
    "How to write a word that contains spaces or quotes",
    """\
A command line is split into words at the spaces. To write a word that contains
spaces, put it in quotes; the quotes are not part of the word:

  metadata set f1 title "Don't Stop"
  metadata set f1 comment 'He said "yes"'
  file add "~/Music/My Albums"

On Linux and macOS, as in a shell:

  "..."      a group; inside it, \\" is a quote and \\\\ a backslash
  '...'      a group in which nothing is special (it cannot contain a single quote)
  \\x       outside quotes, the character x as it is: a\\ b is one word, \\" a quote

  metadata set f1 title "Say \\"hi\\""    sets   Say "hi"

On Windows, a backslash is the separator of a path and stays as typed
(C:\\Music\\a.flac, \\\\server\\share), unless it comes right before a double quote:

  "..."      a group; inside it, \\" is a quote
  '...'      a group in which nothing is special, when the word begins with it
             (an apostrophe elsewhere in a word is an apostrophe)

  metadata set f1 title "Say \\"hi\\""    sets   Say "hi"
  file add "C:\\My Music"                  but "C:\\My Music\\" does not end the
                                          group: leave the last backslash out

Each value is a word: 'metadata set f1 genre Rock Pop' sets two values, and
"Rock Pop" sets one. The words given to a tag that holds a single value, such as
title, are joined with a space: 'metadata set f1 title A Song' and
'metadata set f1 title "A Song"' are the same (see 'help tags'). A quote that is
not closed is reported.""",
)

TOPICS = (SELECTORS, PATHS, TAGS, QUOTING)
