# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2019-2022, 2024-2025 Philipp Wolfer
# Copyright (C) 2020-2021 Gabriel Ferreira
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

from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

from picard.ui.theme import BaseTheme


@pytest.fixture
def theme() -> BaseTheme:
    return BaseTheme()

@pytest.fixture
def kde_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / ".config"
    config_dir.mkdir()
    return config_dir

@pytest.mark.parametrize(
    "key,stdout,expected",
    [
        ("color-scheme", "prefer-dark", True),
        ("color-scheme", "default", False),
        ("gtk-theme", "Adwaita-dark", True),
        ("gtk-theme", "Adwaita", False),
    ],
)
def test_gsettings_detection(theme: BaseTheme, key: str, stdout: str, expected: bool) -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = stdout
        mock_run.return_value.returncode = 0
        if key == "color-scheme":
            assert theme._detect_gnome_color_scheme_dark() is expected
        else:
            assert theme._detect_gnome_gtk_theme_dark() is expected

@pytest.mark.parametrize(
    "side_effect",
    [
        FileNotFoundError(),
        subprocess.CalledProcessError(1, "gsettings"),
    ],
)
def test_gsettings_get_failure(theme: BaseTheme, side_effect) -> None:
    with patch("subprocess.run", side_effect=side_effect):
        assert theme._gsettings_get("color-scheme") is None

@pytest.mark.parametrize(
    "file_content,expected",
    [
        ("[General]\nColorScheme=BreezeDark\n", True),
        ("[General]\nColorScheme=Breeze\n", False),
        ("", False),
    ],
)
def test_kde_colorscheme_detection(theme: BaseTheme, file_content: str, expected: bool, kde_config_dir: Path) -> None:
    kdeglobals = kde_config_dir / "kdeglobals"
    kdeglobals.write_text(file_content)
    with patch("pathlib.Path.home", return_value=kde_config_dir.parent):
        assert theme._detect_kde_colorscheme_dark() is expected

@pytest.mark.parametrize(
    "color_scheme,gtk_theme,kde_content,expected",
    [
        ("prefer-dark", "Adwaita", "ColorScheme=Breeze\n", True),
        ("default", "Adwaita-dark", "ColorScheme=Breeze\n", True),
        ("default", "Adwaita", "ColorScheme=BreezeDark\n", True),
        ("default", "Adwaita", "ColorScheme=Breeze\n", False),
    ],
)
def test_detect_linux_dark_mode(theme: BaseTheme, color_scheme: str, gtk_theme: str, kde_content: str, expected: bool, kde_config_dir: Path) -> None:
    kdeglobals = kde_config_dir / "kdeglobals"
    kdeglobals.write_text(f"[General]\n{kde_content}")
    with patch("pathlib.Path.home", return_value=kde_config_dir.parent):
        with patch.object(theme, "_gsettings_get") as mock_gsettings:
            mock_gsettings.side_effect = [color_scheme, gtk_theme]
            assert theme._detect_linux_dark_mode() is expected
