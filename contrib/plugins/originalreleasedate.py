""" 
Use the earliest release to set the original release date.
"""

PLUGIN_NAME = 'Original Release Date'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = '''Set the original release date of a release by using release events and earliest release advanced relationships.'''
PLUGIN_VERSION = '0.2'
PLUGIN_API_VERSIONS = ['0.12']

from picard.metadata import register_album_metadata_processor
from picard.album import Album
from picard.util import partial
from picard.mbxml import release_to_metadata
from PyQt4.QtCore import QUrl

def _earliest_release_downloaded(album, metadata, original_id, document, http, error):
    try:
        if error:
            album.log.error("%r", unicode(http.errorString()))
        else:
            try:
                release_node = document.metadata[0].release[0]
                original_album = Album(original_id)
                release_to_metadata(release_node, original_album.metadata,
                                    config=album.config, album=original_album)
                get_earliest_release_date(original_album, metadata)
                for track in album._new_tracks:
                    track.metadata["originaldate"] = metadata["originaldate"]
            except:
                error = True
                album.log.error(traceback.format_exc())
    finally:
        album._requests -= 1
        album._finalize_loading(None)

def original_release_date(album, metadata, release_node):
    # First find the earliest release from the release event list
    get_earliest_release_date(album, metadata)
    
    # Check for earliest release ARs and load those
    if release_node.children.has_key('relation_list'):
        for relation_list in release_node.relation_list:
            if relation_list.target_type == 'Release':
                for relation in relation_list.relation:
                    try:
                        direction = relation.direction if hasattr(relation, 'direction') else ''
                        if (relation.type == 'FirstAlbumRelease' and direction == 'backward') \
                            or (relation.type == 'Remaster' and direction != 'backward'):
                            album._requests += 1
                            album.tagger.xmlws.get_release_by_id(relation.target,
                                partial(_earliest_release_downloaded, album, metadata, relation.target),
                                ['release-events'])
                    except AttributeError: pass

def get_earliest_release_date(album, metadata):
    earliest_date = metadata["originaldate"]
    for event in album.release_events:
        if not earliest_date or (event.date and event.date < earliest_date):
            earliest_date = event.date
    metadata["originaldate"] = earliest_date

register_album_metadata_processor(original_release_date)
