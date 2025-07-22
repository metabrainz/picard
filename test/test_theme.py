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

from picard.ui import theme_detect

@pytest.fixture
def kde_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / ".config"
    config_dir.mkdir()
    return config_dir

@pytest.mark.parametrize(
    ("key", "stdout", "expected"),
    [
        ("color-scheme", "prefer-dark", True),
        ("color-scheme", "default", False),
        ("gtk-theme", "Adwaita-dark", True),
        ("gtk-theme", "Adwaita", False),
    ],
)
def test_gsettings_detection(key: str, stdout: str, expected: bool) -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = stdout
        mock_run.return_value.returncode = 0
        if key == "color-scheme":
            assert theme_detect.detect_gnome_color_scheme_dark() is expected
        else:
            assert theme_detect.detect_gnome_gtk_theme_dark() is expected

@pytest.mark.parametrize(
    ("side_effect",),
    [
        (FileNotFoundError(),),
        (subprocess.CalledProcessError(1, "gsettings"),),
    ],
)
def test_gsettings_get_failure(side_effect) -> None:
    with patch("subprocess.run", side_effect=side_effect):
        assert theme_detect.gsettings_get("color-scheme") is None

@pytest.mark.parametrize(
    ("file_content", "expected"),
    [
        ("[General]\nColorScheme=BreezeDark\n", True),
        ("[General]\nColorScheme=Breeze\n", False),
        ("", False),
    ],
)
def test_kde_colorscheme_detection(file_content: str, expected: bool, kde_config_dir: Path) -> None:
    kdeglobals = kde_config_dir / "kdeglobals"
    kdeglobals.write_text(file_content)
    with patch("pathlib.Path.home", return_value=kde_config_dir.parent):
        assert theme_detect.detect_kde_colorscheme_dark() is expected

@pytest.mark.parametrize(
    ("color_scheme", "gtk_theme", "kde_content", "expected"),
    [
        ("prefer-dark", "Adwaita", "ColorScheme=Breeze\n", True),
        ("default", "Adwaita-dark", "ColorScheme=Breeze\n", True),
        ("default", "Adwaita", "ColorScheme=BreezeDark\n", True),
        ("default", "Adwaita", "ColorScheme=Breeze\n", False),
    ],
)
def test_detect_linux_dark_mode_integration(color_scheme: str, gtk_theme: str, kde_content: str, expected: bool, kde_config_dir: Path) -> None:
    kdeglobals = kde_config_dir / "kdeglobals"
    kdeglobals.write_text(f"[General]\n{kde_content}")
    with patch("pathlib.Path.home", return_value=kde_config_dir.parent):
        with patch("picard.ui.theme_detect.gsettings_get") as mock_gsettings:
            # Simulate gsettings: first call for color-scheme, second for gtk-theme
            mock_gsettings.side_effect = [color_scheme, gtk_theme]
            # Compose the strategies in order
            strategies = theme_detect.get_linux_dark_mode_strategies()
            result = False
            for strategy in strategies:
                if strategy():
                    result = True
                    break
            assert result is expected

# --- XFCE dark mode detection ---
@pytest.mark.parametrize(
    ("stdout", "expected"),
    [
        ("Greybird-dark", True),
        ("Greybird", False),
        ("", False),
    ],
)
def test_xfce_dark_theme_detection(stdout: str, expected: bool) -> None:
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = stdout
        mock_run.return_value.returncode = 0
        assert theme_detect.detect_xfce_dark_theme() is expected

@pytest.mark.parametrize(
    ("side_effect",),
    [
        (FileNotFoundError(),),
        (subprocess.CalledProcessError(1, "xfconf-query"),),
    ],
)
def test_xfce_dark_theme_detection_failure(side_effect) -> None:
    with patch("subprocess.run", side_effect=side_effect):
        assert theme_detect.detect_xfce_dark_theme() is False

# --- LXQt dark mode detection ---
@pytest.mark.parametrize(
    ("file_content", "expected"),
    [
        ("theme=DarkTheme\n", True),
        ("theme=LightTheme\n", False),
        ("", False),
    ],
)
def test_lxqt_dark_theme_detection(file_content: str, expected: bool, tmp_path: Path) -> None:
    lxqt_dir = tmp_path / ".config" / "lxqt"
    lxqt_dir.mkdir(parents=True)
    session_conf = lxqt_dir / "session.conf"
    session_conf.write_text(file_content)
    with patch("pathlib.Path.home", return_value=tmp_path):
        assert theme_detect.detect_lxqt_dark_theme() is expected

@pytest.mark.parametrize(
    ("file_exists", "raises"),
    [
        (True, OSError("fail")),
        (False, None),
    ],
)
def test_lxqt_dark_theme_detection_failure(file_exists: bool, raises, tmp_path: Path) -> None:
    lxqt_dir = tmp_path / ".config" / "lxqt"
    lxqt_dir.mkdir(parents=True)
    session_conf = lxqt_dir / "session.conf"
    if file_exists:
        session_conf.write_text("theme=DarkTheme\n")
    with patch("pathlib.Path.home", return_value=tmp_path):
        if file_exists and raises:
            with patch("builtins.open", side_effect=raises):
                assert theme_detect.detect_lxqt_dark_theme() is False
        elif not file_exists:
            assert theme_detect.detect_lxqt_dark_theme() is False
