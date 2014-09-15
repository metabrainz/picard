.. _basics:


.. _basics-basics:

Basics
######

You will need to `download MusicBrainz Picard`_ first. You can also
check out a tutorial :ref:`on how to tag files <guide>`.


.. _basics-clustering:

Clustering
==========

Start with opening individual music files or directories by dragging
them into the left-hand pane. Picard will read the metadata from each
of the files and unless they have been tagged before, the files will
be deposited into the "Unmatched files" folder. Files that have been
tagged before and contain MusicBrainz track identifiers will open up
in the right-hand pane as a part of its release.

Once Picard finishes processing the files, press the "Cluster" button.
Picard will attempt to group the files into album clusters by
examining the metadata and clustering files that appear to belong to
the same album. Files that are not matched into album clusters will
remain in the "Unmatched files" folder.


.. _basics-lookup:

Lookup & querying MusicBrainz
=============================



Automatic lookup
~~~~~~~~~~~~~~~~

Select the cluster or file you want to lookup and use the "Lookup"
button in the toolbar.

Picard will query MusicBrainz with your existing metadata and attempt
to find the best possible match.



Scanning (fingerprinting) files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of using release-oriented and metadata-dependent lookups,
Picard can try and tag your files as single files (rather than a
cluster) based on their `audio fingerprint`_. If you select a set of
files in the left-hand pane and click "Scan", Picard will find
`AcoustIDs`_ for your files and query MusicBrainz to find a track that
matches them.



Manual lookup
~~~~~~~~~~~~~

If you want granular control over how your files are being tagged, or
the above methods provided inaccurate results (or no results), the
alternative is to manually lookup and choose the correct release(s)
for your files.

Select the cluster or file you want to lookup and use one of the lower
"Lookup" buttons in Picard. This opens the MusicBrainz website with a
list of possible matches for your files along with details on what
sets them apart, you can also disregard the lookup results and
manually search for the appropriate album using the search box. Once
you've found the correct album, click on the icon in the album title
and Picard will load that album and its tracks into the right-hand
pane for you to drag clusters/files onto.


.. _basics-maching:

Matching files & saving
=======================

The tracks in the right-hand pane will start out with a musical note
icon, and as the tracks become associated with your files the icons
will change to one of the following:


+ a small rectangle ranging from red to green indicates the quality of
  the match, where red is a bad match and green is a good match
+ a red error triangle means Picard encountered an error (e.g.
  permission error), click the file and read the status bar in the
  bottom of the Picard window to see the error
+ a green check mark indicates the track is up to date and saved


You can drag whole directories, multiple files or album clusters onto
albums and Picard will attempt to match the dragged files to the
album. Any track that doesn't match up well enough, will be added to
an "Unmatched Files" sub-folder specific to that album. You can drag
files out of this folder and into the right slots in the album to fix
up the files that Picard couldn't get right.

Once you've finished matching up your files to albums in the right-
hand pane, right click the album and select the `release event`_ that
corresponds to your specific release and then click the 'Save' button
to save that track/album. Depending on your settings this may move the
track to a new directory and/or rename the track according to its
metadata. Take a look at the options dialog to fine tune your
settings.

Once a file is in the right-hand pane the metadata that will be
written by Picard can be viewed and edited if necessary. Left click
the file and use the metadata comparison table at the bottom to view
and, if necessary, edit the metadata. Remember to re-save the file(s)
if you edit the metadata!

Once you've saved an album and/or want to remove it from view, right
click the album in the right-hand pane and click 'Remove'.


.. _basics-options:

Picard configuration and options
================================
See :ref:`options`.


.. _basics-more:

Isn't there more to MusicBrainz Picard?
=======================================

Yes there is!

Picard is very flexible and can be customized using :ref:`scripts <picard-scripting>`
and `plugins`_ to do things such as:


+ Rename and reorganise your collection using the
  :ref:`functions <scripting-functions>` provided in the scripting language
+ Customize how Picard applies the MusicBrainz :ref:`metadata <mappings>`
  to your files
+ Encapsulate scripting, download cover art, and add other
  functionality to Picard


A lot of Picard's power is in its extensive drag and drop features.
Try some of these operations:


+ Drag a file from the file browser to an album track.
+ Drag a file from the file browser to an album -- this attempts to
  match the file to the album automatically.
+ Drag a directory from the file browser to an album -- this attempts
  to match all the files from the dir to the album.
+ Drag an album cluster onto an album to match the cluster to the
  album.
+ Drag one album onto another to match all the files from one to the
  other.
+ Drag an album cluster into unmatched files to move the cluster back
  to unmatched.
+ Drag unmatched files from an album onto another album or back to
  unmatched files.


.. _AcoustIDs: http://musicbrainz.org/doc/AcoustID
.. _audio fingerprint: http://musicbrainz.org/doc/Audio_Fingerprint
.. _download MusicBrainz Picard: http://picard.musicbrainz.org/downloads/
.. _plugins: http://picard.musicbrainz.org/plugins/
.. _release event: http://musicbrainz.org/doc/Release_Event
.. _scripts: http://picard.musicbrainz.org/docs/scripting/


