# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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
# along with this program; if not, see <https://www.gnu.org/licenses/>.

from unittest import mock

from picard.plugin3.api import (
    PluginApi,
    t_,
)
from picard.util.display_title_base import HasDisplayTitle


def test_should_extract_and_translate_title_attribute():
    class MyClass(HasDisplayTitle):
        TITLE = "Some title"

    with mock.patch('picard.util.display_title_base._') as mock_tr:
        mock_tr.return_value = "Ein Titel"
        title = MyClass.display_title()
        assert title == "Ein Titel"
        mock_tr.assert_called_once_with("Some title")


def test_should_fall_back_to_name():
    class MyClass(HasDisplayTitle):
        NAME = "Some title"

    assert MyClass.display_title() == "Some title"


def test_should_fall_back_to_class_name():
    class MyClass(HasDisplayTitle):
        pass

    assert MyClass.display_title() == "MyClass"


def test_should_fall_back_to_class_name_with_empty_title():
    class MyClass(HasDisplayTitle):
        NAME = None
        TITLE = ""

    assert MyClass.display_title() == "MyClass"


def test_should_translate_with_api():
    class MyClass(HasDisplayTitle):
        TITLE = t_("plugin.title", "Some title")

    api = mock.Mock(spec=PluginApi)
    api.tr.return_value = "Ein Titel"
    MyClass.api = api

    assert MyClass.display_title() == "Ein Titel"
    api.tr.assert_called_with("plugin.title")


def test_should_translate_with_api_if_pluralized():
    class MyClass(HasDisplayTitle):
        TITLE = t_("plugin.title", "Some title", "Some titles")

    api = mock.Mock(spec=PluginApi)
    api.trn.return_value = "Ein Titel"
    MyClass.api = api

    assert MyClass.display_title() == "Ein Titel"
    api.trn.assert_called_with("plugin.title", "Some title", "Some titles", n=1)
