import os
import os.path
import sys

from picard import (
    PICARD_APP_NAME,
    PICARD_ORG_NAME,
)
import picard.const


# The portable version stores all data in a folder beside the executable
configdir = '{}-{}'.format(PICARD_ORG_NAME, PICARD_APP_NAME)
basedir = os.path.join(os.path.dirname(sys.executable), configdir)
os.makedirs(basedir, exist_ok=True)

# Setup config file if not specified as command line argument
if '--config-file' not in sys.argv and '-c' not in sys.argv:
    sys.argv.append('--config-file')
    sys.argv.append(os.path.join(basedir, 'Config.ini'))

# Setup plugin folder
picard.const.USER_PLUGIN_DIR = os.path.join(basedir, 'Plugins')

# Set standard cache location
cachedir = os.path.join(basedir, 'Cache')
os.makedirs(cachedir, exist_ok=True)
picard.const.CACHE_DIR = cachedir
