# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2021, 2025 Bob Swift
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
from picard.util.tags import (
    ALL_TAGS,
    TagVar,
)

from picard.ui import FONT_FAMILY_MONOSPACE
from picard.ui.colors import interface_colors


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
    def __init__(self, include_link=True, parent=None):
        """Custom widget to display the scripting documentation.

        Args:
            include_link (bool): Indicates whether the web link should be included
            parent (QWidget): Parent screen to check layoutDirection()
        """
        super().__init__(parent=parent)

        if self.layoutDirection() == QtCore.Qt.LayoutDirection.RightToLeft:
            text_direction = 'rtl'
        else:
            text_direction = 'ltr'

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

        func_html = DOCUMENTATION_HTML_TEMPLATE % {
            'html': "<dl>%s</dl>" % funcdoc,
            'script_function_fg': interface_colors.get_qcolor('syntax_hl_func').name(),
            'monospace_font': FONT_FAMILY_MONOSPACE,
            'dir': text_direction,
            'inline_start': 'right' if text_direction == 'rtl' else 'left'
        }

        def process_tag(tag: TagVar):
            template = '<dt>%s</dt><dd>%s</dd>'
            tag_title = '%' + tag.script_name() + '%'
            tag_desc = tag.full_description_content()
            return template % (f'<a id="{tag.script_name()}"><code>{tag_title}</code></a>', tag_desc)

        tagdoc = ''
        for tag in sorted(ALL_TAGS, key=lambda x: x.script_name()):
            tagdoc += process_tag(tag)

        tag_html = DOCUMENTATION_HTML_TEMPLATE % {
            'html': "<dl>%s</dl>" % tagdoc,
            'script_function_fg': interface_colors.get_qcolor('syntax_hl_func').name(),
            'monospace_font': FONT_FAMILY_MONOSPACE,
            'dir': text_direction,
            'inline_start': 'right' if text_direction == 'rtl' else 'left'
        }

        self.selected_panel = 1

        # Scripting code is always left-to-right. Qt does not support the dir
        # attribute on inline tags, insert explicit left-right-marks instead.
        if text_direction == 'rtl':
            func_html = func_html.replace('<code>', '<code>&#8206;')
            tag_html = tag_html.replace('<code>', '<code>&#8206;')

        link = '<a href="' + PICARD_URLS['doc_scripting'] + '">' + _('Open Scripting Documentation in your browser') + '</a>'

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName('docs_verticalLayout')

        self.selected_docs = QtWidgets.QLabel(self)
        self.selected_docs.setText(_('Functions:'))
        self.selected_docs.setStyleSheet('font-weight: bold;')

        self.pb_spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)

        self.pb_toggle = QtWidgets.QPushButton(self)
        self.pb_toggle.setText(_('Tags:'))
        self.pb_toggle.setEnabled(True)
        self.pb_toggle.clicked.connect(self._pb_toggle_clicked)

        self.pb_layout = QtWidgets.QHBoxLayout()
        self.pb_layout.setObjectName('docs_pb_layout')
        self.pb_layout.addWidget(self.selected_docs)
        self.pb_layout.addItem(self.pb_spacer)
        self.pb_layout.addWidget(self.pb_toggle)
        self.verticalLayout.addItem(self.pb_layout)

        self.frame_1 = QtWidgets.QFrame(parent=self)
        self.frame_1.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.frame_1.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_1.setContentsMargins(0, 0, 0, 0)
        self.frame_1.setObjectName("docs_frame_1")
        self.frame_1.show()

        self.frame_1_layout = QtWidgets.QVBoxLayout(self.frame_1)
        self.frame_1_layout.setContentsMargins(0, 0, 0, 0)

        self.textBrowser_1 = QtWidgets.QTextBrowser(self)
        self.textBrowser_1.setEnabled(True)
        self.textBrowser_1.setMinimumSize(QtCore.QSize(0, 0))
        self.textBrowser_1.setObjectName('function_docs_textBrowser')
        self.textBrowser_1.setHtml(func_html)
        self.textBrowser_1.show()
        self.frame_1_layout.addWidget(self.textBrowser_1)

        self.frame_2 = QtWidgets.QFrame(parent=self)
        self.frame_2.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_2.setContentsMargins(0, 0, 0, 0)
        self.frame_2.setObjectName("docs_frame_2")
        self.frame_2.show()

        self.frame_2_layout = QtWidgets.QVBoxLayout(self.frame_2)
        self.frame_2_layout.setContentsMargins(0, 0, 0, 0)

        self.textBrowser_2 = QtWidgets.QTextBrowser(self)
        self.textBrowser_2.setEnabled(True)
        self.textBrowser_2.setMinimumSize(QtCore.QSize(0, 0))
        self.textBrowser_2.setObjectName('tags_docs_textBrowser')
        self.textBrowser_2.setOpenExternalLinks(True)
        self.textBrowser_2.setHtml(tag_html)
        self.textBrowser_2.show()
        self.frame_2_layout.addWidget(self.textBrowser_2)

        self.verticalLayout.addWidget(self.frame_1)
        self.verticalLayout.addWidget(self.frame_2)

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
        self.display_panel()

    def display_panel(self):
        if self.selected_panel == 1:
            self.frame_1.setVisible(True)
            self.frame_2.setVisible(False)
            self.selected_docs.setText(_('Functions:'))
            self.pb_toggle.setText(_('Tags'))
        else:
            self.frame_1.setVisible(False)
            self.frame_2.setVisible(True)
            self.selected_docs.setText(_('Tags:'))
            self.pb_toggle.setText(_('Functions'))

    def _pb_toggle_clicked(self):
        self.selected_panel += 1
        if self.selected_panel > 2:
            self.selected_panel = 1
        self.display_panel()
