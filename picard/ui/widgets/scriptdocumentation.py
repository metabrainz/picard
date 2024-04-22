# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021 Bob Swift
# Copyright (C) 2021-2022 Philipp Wolfer
# Copyright (C) 2021-2024 Laurent Monin
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

from picard.const import PICARD_URLS
from picard.i18n import gettext as _
from picard.script import script_function_documentation_all

from picard.ui import FONT_FAMILY_MONOSPACE
from picard.ui.theme import theme


DOCUMENTATION_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
<style>
dt {
    color: %(script_function_fg)s
}
dd {
    /* Qt does not support margin-inline-start, use margin-left/margin-right instead */
    margin-%(inline_start)s: 50px;
    margin-bottom: 50px;
}
code {
    font-family: %(monospace_font)s;
}
</style>
</head>
<body dir="%(dir)s">
    %(html)s
</body>
</html>
'''


class ScriptingDocumentationWidget(QtWidgets.QWidget):
    """Custom widget to display the scripting documentation.
    """
    def __init__(self, parent, include_link=True, *args, **kwargs):
        """Custom widget to display the scripting documentation.

        Args:
            parent (QWidget): Parent screen to check layoutDirection()
            include_link (bool): Indicates whether the web link should be included
        """
        super().__init__(*args, **kwargs)

        def process_html(html, function):
            if not html:
                html = ''
            template = '<dt>%s%s</dt><dd>%s</dd>'
            if function.module is not None and function.module != 'picard.script.functions':
                module = ' [' + function.module + ']'
            else:
                module = ''
            try:
                firstline, remaining = html.split("\n", 1)
                return template % (firstline, module, remaining)
            except ValueError:
                return template % ("<code>$%s()</code>" % function.name, module, html)

        funcdoc = script_function_documentation_all(
            fmt='html',
            postprocessor=process_html,
        )

        if parent.layoutDirection() == QtCore.Qt.LayoutDirection.RightToLeft:
            text_direction = 'rtl'
        else:
            text_direction = 'ltr'

        html = DOCUMENTATION_HTML_TEMPLATE % {
            'html': "<dl>%s</dl>" % funcdoc,
            'script_function_fg': theme.syntax_theme.func.name(),
            'monospace_font': FONT_FAMILY_MONOSPACE,
            'dir': text_direction,
            'inline_start': 'right' if text_direction == 'rtl' else 'left'
        }
        # Scripting code is always left-to-right. Qt does not support the dir
        # attribute on inline tags, insert explicit left-right-marks instead.
        if text_direction == 'rtl':
            html = html.replace('<code>', '<code>&#8206;')

        link = '<a href="' + PICARD_URLS['doc_scripting'] + '">' + _('Open Scripting Documentation in your browser') + '</a>'

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName('docs_verticalLayout')
        self.textBrowser = QtWidgets.QTextBrowser(self)
        self.textBrowser.setEnabled(True)
        self.textBrowser.setMinimumSize(QtCore.QSize(0, 0))
        self.textBrowser.setObjectName('docs_textBrowser')
        self.textBrowser.setHtml(html)
        self.textBrowser.show()
        self.verticalLayout.addWidget(self.textBrowser)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName('docs_horizontalLayout')
        self.scripting_doc_link = QtWidgets.QLabel(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scripting_doc_link.sizePolicy().hasHeightForWidth())
        if include_link:
            self.scripting_doc_link.setSizePolicy(sizePolicy)
            self.scripting_doc_link.setMinimumSize(QtCore.QSize(0, 20))
            self.scripting_doc_link.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.scripting_doc_link.setWordWrap(True)
            self.scripting_doc_link.setOpenExternalLinks(True)
            self.scripting_doc_link.setObjectName('docs_scripting_doc_link')
            self.scripting_doc_link.setText(link)
            self.scripting_doc_link.show()
            self.horizontalLayout.addWidget(self.scripting_doc_link)
        self.verticalLayout.addLayout(self.horizontalLayout)
