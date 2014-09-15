Plugin API
##########



Metadata Processors
===================

MusicBrainz metadata can be post-processed at two levels, album and
track.



Album metadata example:
~~~~~~~~~~~~~~~~~~~~~~~


::


          PLUGIN_NAME = "Disc Numbers"
          PLUGIN_AUTHOR = "Lukas Lalinsky"
          PLUGIN_DESCRIPTION = "Moves disc numbers from album titles to tags."

          from picard.metadata import register_album_metadata_processor
          import re

          def remove_discnumbers(metadata, release):
              matches = re.search(r"\(disc (\d+)\)", metadata["album"])
              if matches:
                  metadata["discnumber"] = matches.group(1)
                  metadata["album"] = re.sub(r"\(disc \d+\)", "", metadata["album"])

          register_album_metadata_processor(remove_discnumbers)




Track metadata example:
~~~~~~~~~~~~~~~~~~~~~~~


::


          PLUGIN_NAME = "Feat. Artists"
          PLUGIN_AUTHOR = "Lukas Lalinsky"
          PLUGIN_DESCRIPTION = "Removes feat. artists from track titles."

          from picard.metadata import register_track_metadata_processor
          import re

          def remove_featartists(metadata, release, track):
              metadata["title"] = re.sub(r"\(feat. [^)]*\)", "", metadata["title"])

          register_track_metadata_processor(remove_featartists)




File Formats
============

Example:


::


          PLUGIN_NAME = "..."
          PLUGIN_AUTHOR = "..."
          PLUGIN_DESCRIPTION = "..."

          from picard.file import File
          from picard.formats import register_format

          class MyFile(File):
              EXTENSIONS = [".foo"]
              NAME = "Foo Audio"
              def read(self):
                  ....
              def save(self):
                  ....

          register_format(MyFile)




Tagger Script Functions
=======================

To define new :ref:`tagger script <picard-scripting>` function use
`register_script_function(function, name=None)` from module
`picard.script`.

Example:


::


          PLUGIN_NAME = "Initials"
          PLUGIN_AUTHOR = "Lukas Lalinsky"
          PLUGIN_DESCRIPTION = "Provides tagger script function $initials(text)."

          from picard.script import register_script_function

          def initials(parser, text):
              return "".join(a[:1] for a in text.split(" ") if a[:1].isalpha())

          register_script_function(initials)


`register_script_function` supports two optional arguments:


+ **eval_args**: If this is **False**, the arguments will not be
  evaluated before being passed to **function**.
+ **check_argcount**: If this is **False** the number of arguments
  passed to the function will not be verified.


The default value for both of them is **True**.



Context Menu Actions
====================

Right-click context menu actions can be added to albums, tracks, files
in Unmatched Files, Clusters and the ClusterList (parent folder of
Clusters).

Example:


::


          PLUGIN_NAME = u'Remove Perfect Albums'
          PLUGIN_AUTHOR = u'ichneumon, hrglgrmpf'
          PLUGIN_DESCRIPTION = u'''Remove all perfectly matched albums from the selection.'''
          PLUGIN_VERSION = '0.2'
          PLUGIN_API_VERSIONS = ['0.15']

          from picard.album import Album
          from picard.ui.itemviews import BaseAction, register_album_action

          class RemovePerfectAlbums(BaseAction):
              NAME = 'Remove perfect albums'

              def callback(self, objs):
                  for album in objs:
                      if isinstance(album, Album) and album.is_complete() and album.get_num_unmatched_files() == 0\
                         and album.get_num_matched_tracks() == len(list(album.iterfiles()))\
                         and album.get_num_unsaved_files() == 0 and album.loaded == True:
                          self.tagger.remove_album(album)

          register_album_action(RemovePerfectAlbums())


Use register_x_action where x is album, track, file, cluster or
clusterlist.


