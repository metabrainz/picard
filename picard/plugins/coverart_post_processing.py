PLUGIN_NAME = "CoverArt Post Processing"
PLUGIN_AUTHOR = "Pranay"
PLUGIN_DESCRIPTION = """
Post Processing Features for the CoverArt Images.
Ignore images smaller than specified width and height.
Resize the image if larger than specified dimensions.
"""
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['2.2']
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from PIL import Image
from io import BytesIO
from picard.util import imageinfo
from picard import config, log
from picard.metadata import (register_album_metadata_processor,
                           register_track_metadata_processor)
from picard.plugin import PluginPriority

MAX_DIMENSION = 420  # Set maximum allowable dimensions of image in pixels
MIN_DIMENSION = 400  # Set minimum allowable dimensions of image in pixels
    
def ignore_image(img_data):
    """Ignore The image file if the dimensions are smaller than a predefined"""
    
    (width, height, mimetype, extension,
             datalength) = imageinfo.identify(img_data)
    if width < MIN_DIMENSION or height < MIN_DIMENSION:
        return True
    return False

def resize_image(image_data, max_size=MAX_DIMENSION):
    """Resize the image to max_size and center crop if larger than max_size."""
    try:
        with Image.open(BytesIO(image_data)) as img:
            width, height = img.size
            if width > max_size or height > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                img = img.resize((new_width, new_height), resample=Image.LANCZOS)
                left = (new_width - max_size) / 2
                top = (new_height - max_size) / 2
                right = left + max_size
                bottom = top + max_size
                img = img.crop((left, top, right, bottom))
            output_buffer = BytesIO()
            img.save(output_buffer, format='JPEG')
            return output_buffer.getvalue()
    except Exception as ex:
        log.error("{0}: Error: {1}".format(PLUGIN_NAME, ex,))

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
                else:
                    img_data_edited = resize_image(image_data)
                    metadata.images[id].set_data(img_data_edited)
                    
                    log.debug("Cover art image processed: %r [%s]" % (
                        image,
                        image.imageinfo_as_string())
                    )
   except Exception as ex:
        log.error("{0}: Error: {1}".format(PLUGIN_NAME, ex,))

# Register the plugin to run at a HIGH priority so that other plugins will
# not have an opportunity to modify the contents of the metadata provided.
register_track_metadata_processor(Track_images, priority=PluginPriority.HIGH)