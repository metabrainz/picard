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


from html import escape

from PyQt6 import QtCore, QtWidgets

from picard.i18n import gettext as _
from picard.util import get_url


# Schemes we are willing to turn into a clickable link. Mirrors the manifest
# validator's allowed schemes for ``report_bugs_to``.
_ALLOWED_LINK_SCHEMES = ('https://', 'http://', 'mailto:')


def _valid_link(value: str | None) -> str:
    """Return a stripped URL if it uses an allowed scheme, else an empty string.

    This guards against injecting arbitrary (or malformed) manifest content
    into the rich-text dialog as a link target.
    """
    if not value:
        return ''
    value = value.strip()
    if value.startswith(_ALLOWED_LINK_SCHEMES):
        return value
    return ''


def _report_info_holder(plugin: object | None) -> object | None:
    """Find the object carrying ``report_bugs_to`` / ``homepage`` for a plugin.

    The bug-reporting info can live in different places depending on the
    plugin's state:
      - on the plugin's ``manifest`` (installed plugins),
      - on a registry entry stored as ``_registry_plugin`` (plugins being
        installed, not yet on disk),
      - or directly on the object itself (a manifest/registry entry passed in).

    The first candidate that exposes a non-empty ``report_bugs_to`` or
    ``homepage`` wins; otherwise the object itself is returned so the caller
    can still fall back to Picard's tracker.
    """
    if plugin is None:
        return None
    candidates = (
        plugin,
        getattr(plugin, 'manifest', None),
        getattr(plugin, '_registry_plugin', None),
    )
    for candidate in candidates:
        if candidate is None:
            continue
        if getattr(candidate, 'report_bugs_to', '') or getattr(candidate, 'homepage', ''):
            return candidate
    return plugin


def plugin_report_link(plugin: object | None) -> tuple[str, bool]:
    """Return the best "report this issue" URL for a plugin error.

    Preference order:
      1. the plugin's ``report_bugs_to``
      2. the plugin's ``homepage``
      3. Picard's own bug tracker (fallback)

    ``plugin`` may be an installed plugin, a plugin being installed, a manifest
    or a registry entry; the report info is extracted from whichever holds it.

    Returns a tuple ``(url, is_plugin_specific)`` where ``is_plugin_specific``
    is True when the URL came from the plugin, so callers can adjust the
    wording (report to the plugin author vs. to Picard).
    """
    source = _report_info_holder(plugin)
    if source is not None:
        report_bugs_to = _valid_link(getattr(source, 'report_bugs_to', ''))
        if report_bugs_to:
            return report_bugs_to, True
        homepage = _valid_link(getattr(source, 'homepage', ''))
        if homepage:
            return homepage, True
    return get_url('bugtracker'), False


def _plugin_display_name(plugin: object | None) -> str:
    """Best-effort display name for a plugin-ish object.

    Handles the different shapes passed to the error dialogs: installed
    plugins, plugins being installed (installable/registry entries) and
    manifests. Returns an empty string if no name can be determined.
    """
    if plugin is None:
        return ''
    # get_display_name(): installable/registry entries.
    # name_i18n(): manifest / registry (locale-aware).
    # name(): installed plugin (no-arg) and manifest (defaulted locale).
    for attr in ('get_display_name', 'name_i18n', 'name'):
        candidate = getattr(plugin, attr, None)
        if callable(candidate):
            try:
                value = candidate()
            except Exception:
                continue
            if value:
                return str(value)
    # Fall back to a plain ``name`` attribute (installable base class).
    value = getattr(plugin, 'name', None)
    if isinstance(value, str) and value:
        return value
    return ''


def show_plugin_error(
    parent: QtWidgets.QWidget | None,
    title: str,
    message: str,
    error: str | None = None,
    plugin: object | None = None,
    name: str | None = None,
) -> None:
    """Show a critical plugin error dialog with a "report this issue" link.

    The dialog is laid out as::

        Plugin "<name>":
        <message>

        Error reported by the plugin:
            <error>

        <report link>

    where ``<name>`` is derived from ``plugin`` (or the explicit ``name``
    override), and the raw ``error`` is shown in its own block so it is easy to
    distinguish and copy when reporting a bug.

    The report link points at the plugin's ``report_bugs_to`` (or
    ``homepage``) when that info is available, otherwise at Picard's bug
    tracker.

    Args:
        parent: Parent widget for the dialog.
        title: Dialog window title.
        message: Human-readable context (e.g. 'Failed to enable plugin.').
        error: The raw error text reported by the plugin, if any.
        plugin: The offending plugin (installed plugin, plugin being installed,
            manifest, or registry entry), if known.
        name: Explicit plugin display name, used when it cannot be derived from
            ``plugin``.
    """
    url, is_plugin_specific = plugin_report_link(plugin)
    if is_plugin_specific:
        report_text = _("If this looks like a plugin problem, report it to the plugin author: %s") % (
            '<a href="%s">%s</a>' % (escape(url, quote=True), escape(url))
        )
    else:
        report_text = _("Please report this issue on the %s.") % (
            '<a href="%s">%s</a>' % (escape(url, quote=True), _("MusicBrainz bug tracker"))
        )

    display_name = name or _plugin_display_name(plugin)

    # All caller-supplied text is HTML-escaped before being placed into the
    # RichText body so it cannot inject markup.
    if display_name:
        header = _('Plugin "%s":') % escape(display_name)
        parts = ['<p><b>%s</b><br>%s</p>' % (header, escape(message))]
    else:
        parts = ['<p>%s</p>' % escape(message)]
    if error:
        parts.append('<p>%s</p>' % escape(_("Error reported by the plugin:")))
        # Render the raw error in a monospace block, preserving line breaks.
        error_html = escape(error).replace('\n', '<br>')
        parts.append('<pre style="margin-left: 1em; white-space: pre-wrap;">%s</pre>' % error_html)
    parts.append('<p>%s</p>' % report_text)

    box = QtWidgets.QMessageBox(parent)
    box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
    box.setWindowTitle(title)
    box.setTextFormat(QtCore.Qt.TextFormat.RichText)
    box.setText(''.join(parts))
    box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    box.exec()
