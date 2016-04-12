Updating Resources
==================

This directory contains all external resources, like icons, used by Picard.

Picard utilizes PyQt4 Resource System for using these resources in application. For more information about PyQt4 Resource System see this [documentation](http://pyqt.sourceforge.net/Docs/PyQt4/resources.html).

For adding a new image into existing resources, follow these steps:

1. Add image file (like .png) into `resources/images/` and source file (like .svg) into `resources/img-src`.
2. Generate new .qrc file. This would automatically detect any changes in directory.

    $ python2 makeqrc.py

3. Create binary of all resources which will be used by Picard.

    $ python2 compile.py
