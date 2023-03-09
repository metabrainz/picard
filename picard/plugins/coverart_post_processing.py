PLUGIN_NAME = "Cover Art Post Processing"
PLUGIN_AUTHOR = "Pranay"
PLUGIN_DESCRIPTION = """
Post Processing Features for the CoverArt Images.
Ignore images smaller than specified width and height.
"""
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['2.2']
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from io import BytesIO
from picard.util import imageinfo
from picard import config, log
from picard.metadata import (register_album_metadata_processor,
                           register_track_metadata_processor)
from picard.plugin import PluginPriority

MIN_DIMENSION = 400  # Set minimum allowable dimensions of image in pixels
    
def ignore_image(img_data):
    """Ignore The image file if the dimensions are smaller than a predefined"""
    
    (width, height, mimetype, extension,
             datalength) = imageinfo.identify(img_data)
    if width < MIN_DIMENSION or height < MIN_DIMENSION:
        return True
    return False

def Track_images(album, metadata, track, release):
   try:
    for id,image in enumerate(metadata.images):
            image_data = image.data
            if image_data is not None:
                if ignore_image(image_data):
                    # Removing the image
                    log.debug("Cover art image removed from metadata: %r [%s]" % (
                        image,
                        image.imageinfo_as_string())
                    )
                    metadata.images.pop(id)
   except Exception as ex:
        log.error("{0}: Error: {1}".format(PLUGIN_NAME, ex,))

# Register the plugin to run at a HIGH priority so that other plugins will
# not have an opportunity to modify the contents of the metadata provided.
register_track_metadata_processor(Track_images, priority=PluginPriority.HIGH)