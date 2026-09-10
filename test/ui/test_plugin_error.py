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


from types import SimpleNamespace

from picard.util import get_url

import pytest

from picard.ui.dialogs.plugin_error import (
    plugin_report_link,
    show_plugin_error,
)


def _plugin(report_bugs_to='', homepage=''):
    """A plugin-like object that exposes the report fields directly."""
    return SimpleNamespace(report_bugs_to=report_bugs_to, homepage=homepage)


def test_report_link_prefers_report_bugs_to():
    plugin = _plugin(report_bugs_to='https://example.com/issues', homepage='https://example.com')
    url, is_plugin_specific = plugin_report_link(plugin)
    assert url == 'https://example.com/issues'
    assert is_plugin_specific is True


def test_report_link_falls_back_to_homepage():
    plugin = _plugin(report_bugs_to='', homepage='https://example.com')
    url, is_plugin_specific = plugin_report_link(plugin)
    assert url == 'https://example.com'
    assert is_plugin_specific is True


def test_report_link_accepts_mailto():
    plugin = _plugin(report_bugs_to='mailto:dev@example.com')
    url, is_plugin_specific = plugin_report_link(plugin)
    assert url == 'mailto:dev@example.com'
    assert is_plugin_specific is True


def test_report_link_extracts_from_manifest():
    # An installed plugin carries the info on its manifest.
    plugin = SimpleNamespace(manifest=_plugin(report_bugs_to='https://example.com/issues'))
    url, is_plugin_specific = plugin_report_link(plugin)
    assert url == 'https://example.com/issues'
    assert is_plugin_specific is True


def test_report_link_extracts_from_registry_entry():
    # A plugin being installed carries the info on its registry entry.
    plugin = SimpleNamespace(_registry_plugin=_plugin(homepage='https://example.com'))
    url, is_plugin_specific = plugin_report_link(plugin)
    assert url == 'https://example.com'
    assert is_plugin_specific is True


def test_report_link_falls_back_to_picard_tracker_when_no_plugin():
    url, is_plugin_specific = plugin_report_link(None)
    assert url == get_url('bugtracker')
    assert is_plugin_specific is False


def test_report_link_rejects_non_url_scheme():
    # A field that is not an allowed URL scheme must not be used as a link
    # target; fall back to Picard's tracker instead.
    plugin = _plugin(report_bugs_to='javascript:alert(1)', homepage='not a url')
    url, is_plugin_specific = plugin_report_link(plugin)
    assert url == get_url('bugtracker')
    assert is_plugin_specific is False


def test_report_link_ignores_empty_and_whitespace():
    plugin = _plugin(report_bugs_to='   ', homepage='')
    url, is_plugin_specific = plugin_report_link(plugin)
    assert url == get_url('bugtracker')
    assert is_plugin_specific is False


@pytest.mark.parametrize(
    'plugin,expected_snippet',
    [
        (_plugin(report_bugs_to='https://example.com/issues'), 'https://example.com/issues'),
        (None, get_url('bugtracker')),
    ],
)
def test_show_plugin_error_builds_dialog_with_link(qapp, monkeypatch, plugin, expected_snippet):
    captured = {}

    def fake_exec(self):
        captured['text'] = self.text()
        return 0

    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.exec', fake_exec)
    show_plugin_error(None, "Test Failure", "boom", plugin=plugin)
    assert expected_snippet in captured['text']
    # The raw error message is HTML-escaped and present.
    assert 'boom' in captured['text']


def test_show_plugin_error_separates_message_and_error(qapp, monkeypatch):
    captured = {}

    def fake_exec(self):
        captured['text'] = self.text()
        return 0

    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.exec', fake_exec)
    show_plugin_error(None, "Plugin Error", "Failed to enable the plugin.", error="ImportError: boom", plugin=None)
    text = captured['text']
    assert 'Failed to enable the plugin.' in text
    assert 'Error reported by the plugin:' in text
    assert 'ImportError: boom' in text
    # The raw error is rendered in its own <pre> block.
    assert '<pre' in text


def test_show_plugin_error_without_error_has_no_error_block(qapp, monkeypatch):
    captured = {}

    def fake_exec(self):
        captured['text'] = self.text()
        return 0

    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.exec', fake_exec)
    show_plugin_error(None, "Plugin Error", "Something failed.", plugin=None)
    text = captured['text']
    assert 'Error reported by the plugin:' not in text
    assert '<pre' not in text


def test_show_plugin_error_uses_explicit_name(qapp, monkeypatch):
    captured = {}

    def fake_exec(self):
        captured['text'] = self.text()
        return 0

    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.exec', fake_exec)
    show_plugin_error(None, "Plugin Error", "Failed to enable the plugin.", name="My Plugin", plugin=None)
    assert 'My Plugin' in captured['text']


def test_show_plugin_error_derives_name_from_plugin(qapp, monkeypatch):
    captured = {}

    def fake_exec(self):
        captured['text'] = self.text()
        return 0

    # Installed-plugin shape: name() method returns the display name.
    plugin = SimpleNamespace(name=lambda: "Derived Name", report_bugs_to='', homepage='')
    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.exec', fake_exec)
    show_plugin_error(None, "Plugin Error", "Failed to enable the plugin.", plugin=plugin)
    assert 'Derived Name' in captured['text']


def test_show_plugin_error_derives_name_from_get_display_name(qapp, monkeypatch):
    captured = {}

    def fake_exec(self):
        captured['text'] = self.text()
        return 0

    # Installable/registry shape: get_display_name() is preferred.
    plugin = SimpleNamespace(get_display_name=lambda: "Registry Name", report_bugs_to='', homepage='')
    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.exec', fake_exec)
    show_plugin_error(None, "Plugin Error", "Failed to install the plugin.", plugin=plugin)
    assert 'Registry Name' in captured['text']


def test_show_plugin_error_escapes_error_message(qapp, monkeypatch):
    captured = {}

    def fake_exec(self):
        captured['text'] = self.text()
        return 0

    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.exec', fake_exec)
    show_plugin_error(None, "Test", "context", error="<b>evil</b> & stuff", plugin=None)
    # The raw error must be escaped, not injected as markup.
    assert '<b>evil</b>' not in captured['text']
    assert '&lt;b&gt;evil&lt;/b&gt;' in captured['text']
    assert '&amp; stuff' in captured['text']


def test_show_plugin_error_escapes_script_and_name(qapp, monkeypatch):
    # A malicious plugin name and a hostile raw error must both be escaped.
    captured = {}

    def fake_exec(self):
        captured['text'] = self.text()
        return 0

    monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.exec', fake_exec)
    error = "boom <img src=x onerror=alert(2)>"
    show_plugin_error(
        None,
        "Plugin Error",
        "Failed to enable the plugin.",
        error=error,
        name='<script>alert(1)</script>',
    )
    text = captured['text']
    # No raw tags survive.
    assert '<script>' not in text
    assert '<img' not in text
    # They appear escaped instead.
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in text
    assert '&lt;img src=x onerror=alert(2)&gt;' in text
