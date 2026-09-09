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
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from PyQt6 import QtWidgets

from picard.config import (
    FloatOption,
    IntOption,
    Option,
    TextOption,
)

import pytest

from picard.ui.options import OptionsPage


@pytest.fixture()
def page(qapp):
    return OptionsPage.__new__(OptionsPage)


@pytest.fixture(autouse=True)
def clean_registry():
    saved = dict(Option.registry)
    Option.registry = {}
    try:
        yield
    finally:
        Option.registry = saved


def test_apply_bounds_int(page):
    IntOption('setting', 'opt', 5, bounds=(2, 10))
    spinbox = QtWidgets.QSpinBox()
    page.apply_option_bounds(spinbox, 'opt')
    assert spinbox.minimum() == 2
    assert spinbox.maximum() == 10


def test_apply_bounds_scale(page):
    # A 0.0..1.0 float option shown as a 0..100 percentage.
    FloatOption('setting', 'opt', 0.5, bounds=(0.0, 1.0))
    spinbox = QtWidgets.QSpinBox()
    page.apply_option_bounds(spinbox, 'opt', scale=100)
    assert spinbox.minimum() == 0
    assert spinbox.maximum() == 100


def test_apply_bounds_rounds_min_up_max_down(page):
    # Scaling fractional bounds: minimum rounds up, maximum rounds down, so the
    # widget range never exceeds the option's true bounds.
    FloatOption('setting', 'opt', 0.5, bounds=(0.005, 0.995))
    spinbox = QtWidgets.QSpinBox()
    page.apply_option_bounds(spinbox, 'opt', scale=100)
    assert spinbox.minimum() == 1  # ceil(0.5)
    assert spinbox.maximum() == 99  # floor(99.5)


def test_apply_bounds_only_minimum(page):
    IntOption('setting', 'opt', 5, bounds=(2, None))
    spinbox = QtWidgets.QSpinBox()
    spinbox.setMaximum(12345)
    page.apply_option_bounds(spinbox, 'opt')
    assert spinbox.minimum() == 2
    # Maximum is left untouched when the option has no upper bound.
    assert spinbox.maximum() == 12345


@pytest.mark.parametrize(
    "register",
    [
        pytest.param(lambda: TextOption('setting', 'opt', 'x'), id="non-numeric option"),
        pytest.param(lambda: None, id="unregistered option"),
    ],
)
def test_apply_bounds_noop(page, register):
    register()
    spinbox = QtWidgets.QSpinBox()
    spinbox.setMinimum(3)
    spinbox.setMaximum(7)
    page.apply_option_bounds(spinbox, 'opt')
    assert spinbox.minimum() == 3
    assert spinbox.maximum() == 7
