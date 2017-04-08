Updating Resources
==================

This directory contains all external resources, like icons, used by Picard.

Picard utilizes the PyQt5 Resource System for using these resources in
application. For more information about the PyQt5 Resource System see this
[documentation](http://pyqt.sourceforge.net/Docs/PyQt5/resources.html).

For adding a new image into existing resources, follow these steps:

1. Add image file (like .png) into `resources/images/` and source file (like .svg) into `resources/img-src`.
2. Generate new .qrc file. This would automatically detect any changes in directory.

    $ python3 makeqrc.py

3. Create binary of all resources which will be used by Picard.

    $ python3 compile.py
