import os
import sys


# On macOS ensure libraries such as libdiscid.dylib get loaded from app bundle
os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '%s:%s' % (
    os.path.dirname(sys.executable), os.environ.get('DYLD_FALLBACK_LIBRARY_PATH', ''))
