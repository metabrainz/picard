import glob
import os.path

import sip

sip.setapi("QString", 2)
sip.setapi("QVariant", 2)

for filename in glob.glob(os.path.join(os.path.dirname(__file__), "test_*.py")):
    __import__("test." + os.path.basename(filename)[:-3])
