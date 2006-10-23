import glob
import os.path

for filename in glob.glob(os.path.join(os.path.dirname(__file__), "test_*.py")):
    __import__("test." + os.path.basename(filename)[:-3])
