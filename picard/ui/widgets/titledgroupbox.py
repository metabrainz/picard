# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2026 Laurent Monin
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from PyQt6 import (
    QtCore,
    QtWidgets,
)
from PyQt6.QtGui import QHelpEvent


class TitledGroupBox(QtWidgets.QGroupBox):
    """A QGroupBox that only shows its tooltip when hovering over the title.

    By default, QGroupBox.setToolTip() shows the tooltip over the entire
    widget area, including child widgets.  This subclass intercepts the
    ToolTip event and uses the style engine's hit-testing to restrict the
    tooltip to the title label region only.

    Based on: https://stackoverflow.com/a/72517163
    """

    # Parameter name 'a0' matches the Qt base class stub signature;
    # renaming it would trigger an invalid-method-override error in ty.
    def event(self, a0: QtCore.QEvent | None) -> bool:
        if a0 is not None and a0.type() == QtCore.QEvent.Type.ToolTip:
            style = self.style()
            if style is not None and isinstance(a0, QHelpEvent):
                options = QtWidgets.QStyleOptionGroupBox()
                self.initStyleOption(options)
                control = style.hitTestComplexControl(
                    QtWidgets.QStyle.ComplexControl.CC_GroupBox,
                    options,
                    a0.pos(),
                )
                if control != QtWidgets.QStyle.SubControl.SC_GroupBoxLabel:
                    QtWidgets.QToolTip.hideText()
                    return True
        return super().event(a0)
