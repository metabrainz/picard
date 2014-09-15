.. _picard-scripting:


.. role:: since
    :class: since

Scripting
#########

This page describes the simple scripting language implemented in
`MusicBrainz Picard`_.


.. _scripting-syntax:

Syntax
======

The syntax is derived from `Foobar2000's titleformat`_. There are
three base elements: **text**, **variable** and **function**.
Variables consist of alpha-numeric characters enclosed in percent
signs (e.g. `%artist%`). Functions start with a dollar sign and end
with an argument list enclosed in parentheses (e.g. `$lower(...)`).

To use parenthesis or commas as-is inside a function call you must
escape them with a backslash.



Metadata Variables
==================

See :ref:`Picard tags <picard-tags>` for list of usable variables.



Technical Variables
===================



``%_extension%``
     Extension of the file name.
     For example mp3 for file 01 Track.mp3 .



.. _scripting-functions:

Functions
=========


.. _func-if:

``$if(if,then,else)``
    If `if` is not empty, it returns `then`, otherwise it returns `else`.

.. _func-if2:

``$if2(a1,a2,a3,...)``
    Returns first non empty argument.

.. _func-lower:

``$lower(text)``
    Returns `text` in lower case.

.. _func-upper:

``$upper(text)``
    Returns `text` in upper case.

.. _func-left:

``$left(text,num)``
    Returns first `num` characters from `text`.

.. _func-matchedtracks:

``$matchedtracks()``
    Returns the number of matched tracks within a release.
    
    :since:`Added in version 0.12`

.. _func-right:

``$right(text,num)``
    Returns last `num` characters from `text`.

.. _func-num:

``$num(num,len)``
    Returns `num` formatted to `len` digits.

.. _func-replace:

``$replace(text,search,replace)``
    Replaces occurrences of `search` in `text` with value of `replace` and
    returns the resulting string.

.. _func-rsearch:

``$rsearch(text,pattern)``
    `Regular expression`_ search. This function will return the first
    matching group.

.. _func-rreplace:

``$rreplace(text,pattern,replace)``
    `Regular expression`_ replace.

.. _func-in:

``$in(x,y)``
    Returns true, if `x` contains `y`.

.. _func-inmulti:

``$inmulti(x,y)``
    Returns true, if multi-value variable `x` contains `y`.
    
    :since:`Since Picard 1.0`

.. _func-unset:

``$unset(name)``
    Unsets the variable `name`.

.. _func-set:

``$set(name, value)``
    Sets the variable `name` to `value`.

    .. note:: To create a variable which can be used for the file naming
        string, but which will not be written as a tag in the file, prefix the
        variable name with an underscore. `%something%` will create a
        "something" tag; `%_something%` will not.

.. _func-setmulti:

``$setmulti(name, value, separator="; ")``
    Sets the variable `name` to `value`, using the separator (or "; " if
    not passed) to coerce the value back into a proper multi-valued tag.
    This can be used to operate on multi-valued tags as a string, and then
    set them back as proper multi-valued tags, e.g:

    ::

      $setmulti(genre,$lower(%genre%))

    :since:`Since Picard 1.0`

.. _func-get:

``$get(name)``
    Returns the variable `name` (equivalent to `%name%`).

.. _func-copy:

``$copy(new,old)``
    Copies metadata from variable `old` to `new`. The difference between
    :ref:`$set(new,%old%) <func-set>` is that `$copy(new,old)` copies
    multi-value variables without flattening them.
    
    :since:`Since Picard 0.9`

.. _func-copymerge:

``$copymerge(new,old)``
    Merges metadata from variable `old` into `new`, removing duplicates
    and appending to the end, so retaining the original ordering. Like
    :ref:`$copy <func-copy>`, this will also copy multi-valued variables
    without flattening them.
    
    :since:`Since Picard 1.0`

.. _func-trim:

``$trim(text[,char])``
    Trims all leading and trailing whitespaces from `text`. The optional
    second parameter specifies the character to trim.

.. _func-add:

``$add(x,y)``
    Add `y` to `x`.

.. _func-sub:

``$sub(x,y)``
    Subtracts `y` from `x`.

.. _func-div:

``$div(x,y)``
    Divides `x` by `y`.

.. _func-mod:

``$mod(x,y)``
    Returns the remainder of `x` divided by `y`.

.. _func-mul:

``$mul(x,y)``
    Multiplies `x` by `y`.

.. _func-or:

``$or(x,y)``
    Returns true, if either `x` or `y` not empty.

.. _func-and:

``$and(x,y)``
    Returns true, if both `x` and `y` are not empty.

.. _func-not:

``$not(x)``
    Returns true, if `x` is empty.

.. _func-eq:

``$eq(x,y)``
    Returns true, if `x` equals `y`.

.. _func-ne:

``$ne(x,y)``
    Returns true, if `x` not equals `y`.

.. _func-lt:

``$lt(x,y)``
    Returns true, if `x` is lower than `y`.

.. _func-lte:

``$lte(x,y)``
    Returns true, if `x` is lower than or equals `y`.

.. _func-gt:

``$gt(x,y)``
    Returns true, if `x` is greater than `y`.

.. _func-gte:

``$gte(x,y)``
    Returns true, if `x` is greater than or equals `y`.

.. _func-noop:

``$noop(...)``
    Does nothing (useful for comments or disabling a block of code).

.. _func-len:

``$len(text)``
    Returns the number of characters in text.

.. _func-performer:

``$performer(pattern="",join=", ")``
    Returns the performers where the performance type (e.g. "vocal")
    matches `pattern`, joined by `join`.
    
    :since:`Since Picard 0.10`

.. _func-firstalphachar:

``$firstalphachar(text,nonalpha="#")``
    Returns the first character of `text`. If `text` is not an alphabetic
    character `nonalpha` is returned instead.
    
    :since:`Since Picard 0.12`

.. _func-initials:

``$initials(text)``
    Returns the first character of each word in `text`, if it is an
    alphabetic character.
    
    :since:`Since Picard 0.12`

.. _func-truncate:

``$truncate(text,length)``
    Truncate `text` to `length`.
    
    :since:`Since Picard 0.12`

.. _func-firstwords:

``$firstwords(text,length)``
    Like $truncate except that it will only return the complete words
    from `text` which fit within `length` characters.
    
    :since:`Since Picard 0.12`

.. _func-swapprefix:

``$swapprefix(text,*prefixes="a","the")``
    Moves the specified prefixes from the beginning to the end of text.
    If no prefix is specified 'A' and 'The' are used by default.
    
    :since:`Integrated since Picard 1.3, previously as a plugin since Picard
    0.13`

.. _func-delprefix:

``$delprefix(text,*prefixes="a","the")``
    Deletes the specified prefixes from the beginning of text. If no
    prefix is specified 'A' and 'The' are used by default.
    
    :since:`Since Picard 1.3`


Tagger Script Examples
======================

:menuselection:`Options --> Options... --> Advanced --> Scripting`

Tagger Script usually creates, modifies or deletes metadata variables.



Artist names
~~~~~~~~~~~~


::

    $if($search(%album%,(feat. conductor)), $set(artist,%orchestra%))



+ Stupid assumption that all classical albums have "feat. conductor"
  in the title, but it shows the idea. :)




Live tracks on live albums
~~~~~~~~~~~~~~~~~~~~~~~~~~


::

    $if($and($eq(%releasetype%,live),$not($in(%title%,\(live\)))),$set(title,%title% \(live\)))




Remove "feat." from track titles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


::

    $set(title,$rreplace(%title%,\\s\\\(feat. [^\)]+\\\),))




Convert triple-dot to ellipsis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


::


    $set(title,$replace(%title%,...,…))
    $set(album,$replace(%album%,...,…))


This one is useful for people concerned about correct typography and
also fixes one problem on Linux: if an album (assuming it's also a
directory) is called something like "...for you!", it is considered
hidden and therefore might be not accessible from some applications.



Remove "various artists" on compilations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, Picard marks various-artist compilations with an album
artist called "Various Artists". Even if you don't have anything by
`Torsten Pröfrock`_, it still means that you player will sort your
comps between Vangelis and VCR instead of down at the end, which you
may not want.

This is easy to fix:


::

    $if($and($eq(%compilation%,1), $eq(%albumartist%,Various Artists)), $unset(albumartist) $unset(albumartistsort))




Merge writers into both composer and lyricist tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Supported from version 1.0

Suppose you want to add anyone involved in writing to both the
composer and lyricist tags.


::


    $copymerge(composer,writer)
    $copymerge(lyricist,writer)
    $unset(writer)




File Naming Examples
====================

:menuselection:`Options --> Options... --> File naming`



Lower case filenames with underscores
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


::

    $lower($replace(%albumartist%/%album%/$num(%tracknumber%,2)%title%, ,_))




(Year) only if available
~~~~~~~~~~~~~~~~~~~~~~~~


::

    $if(%date%,\($left(%date%,4)\))




Use a different naming pattern for NATs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


::

    $if($eq([non-album tracks],%album%),[non-album tracks]/%tracknumber%.%artist% - ,%artist% - $if(%date%, $left(%date%,4) )-%album%/%tracknumber%.)%title%


Result:


+ Non-Album Tracks: [non-album tracks]/Band Name - Track Name.ext
+ Tracks in releases: Band Name - year - Release Name/##. Track
  Name.ext




Organize by alphabetical folders excluding leading The
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To keep music organized by initial letter of artist's name you must
first set the directory where saved files are to be stored in
:menuselection:`Options --> Moving Files`.
Then under :menuselection:`Options --> File Naming` check Rename files
when saving.
This script will then move saved files to your Moving Files location
using the following hierarchy:
Result:


+ A/Artist Name, The/Year - Album Name (type-status)/Album (type-
  status)-disc#-Track-Song Title


for Various Artists-Albums



+ Various Artist/Year - Album Name (type-status)/Album (type-
  status)-disc#-Track-Song Title



::


    $if($eq(%musicbrainz_albumartistid%,89ad4ac3-39f7-470e-963a-56509c546377),

    $left($if2(%albumartistsort%,%artistsort%),30)/
    $if(%date%,$left(%date%,4)) - $left(%album%,40) \(%releasestatus%-%releasetype%\)/
    $left(%album%,30) \(%releasestatus%-%releasetype%\)-$if($gt(%totaldiscs%,1),$if2(%media%,CD)%discnumber%-,)$num(%tracknumber%,2)-$left(%title%,30)

    ,
    $upper($firstalphachar($if2(%albumartistsort%,%artistsort%),#))
    /$left($if2(%albumartistsort%,%artistsort%),18)/
    $if(%date%,$left(%date%,4)) - $left(%album%,40) \(%releasestatus%-%releasetype%\)/
    $left(%album%,30) \(%releasestatus%-%releasetype%\)-$if($gt(%totaldiscs%,1),$if2(%media%,CD)%discnumber%-,)$num(%tracknumber%,2)-$left(%title%,30)

    )




.. _Foobar2000's titleformat: http://wiki.hydrogenaudio.org/index.php?title=Foobar2000:Titleformat_Reference
.. _MusicBrainz Picard: http://picard.musicbrainz.org/
.. _Regular expression: https://docs.python.org/2/library/re.html#regular-expression-syntax
.. _Torsten Pröfrock: http://musicbrainz.org/artist/4e46dd54-81a6-4a75-a666-d0e447861e3f


