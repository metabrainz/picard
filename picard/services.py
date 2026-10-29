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

"""Access to the long-lived "services" the tagging core depends on.

The tagging pipeline needs a handful of long-lived infrastructure objects —
the web service and its API helpers, the file-format registry, the AcoustID
client/manager and the ISRC submit manager. Historically these live as
attributes on the GUI ``Tagger`` object and core code reaches them via
``self.tagger.<service>`` (i.e. ``tagger_instance()``), which does not exist in
headless/CLI mode.

This module introduces a single, UI-independent accessor, :func:`services`,
that core code uses instead of reaching into ``Tagger``. It is the first step
of separating "services" (long-lived infrastructure) from the GUI application
object, so the same core code can run under the GUI, the headless
``picard-cli``, or a future web frontend.

The accessor is a thin, read-only *view* over its provider. By default it
resolves from ``app_instance()``: in GUI mode that is the ``Tagger`` (which
already owns these attributes), so this introduces no duplication and no
behaviour change. A dedicated headless provider (the CLI's
``HeadlessTagger``) installs itself via :func:`set_services_provider`; tests
install the mock ``Tagger`` the same way.
"""

from picard import app_instance


# The attribute names the services view exposes, as they currently exist on
# the Tagger application object. Keeping the list explicit documents exactly
# what counts as a "service" (vs. per-session working-set state, which is
# handled separately).
_SERVICE_ATTRS = (
    'webservice',
    'mb_api',
    'format_registry',
    'acoustidmanager',
    'isrc_submit_manager',
)


class TaggingServices:
    """Read-only view over the long-lived tagging services.

    The services are resolved lazily from a *provider* object (by default the
    application instance). Attribute access is delegated to the provider, so
    in GUI mode this transparently exposes the ``Tagger``'s existing service
    attributes without copying or re-wiring anything.
    """

    __slots__ = ('_provider',)

    def __init__(self, provider=None):
        # Provider may be None; it is resolved lazily so that importing this
        # module never requires an application instance to exist yet.
        self._provider = provider

    def _resolve_provider(self):
        if self._provider is not None:
            return self._provider
        return app_instance()

    def __getattr__(self, name):
        if name in _SERVICE_ATTRS:
            provider = self._resolve_provider()
            if provider is None:
                raise RuntimeError(
                    f"Tagging service {name!r} is not available: no application instance "
                    "and no services provider installed."
                )
            return getattr(provider, name)
        raise AttributeError(name)

    @property
    def available(self) -> bool:
        """Return True if a provider (app instance or installed) is present."""
        return self._resolve_provider() is not None


_services = TaggingServices()


def services() -> TaggingServices:
    """Return the process-wide tagging services accessor."""
    return _services


def set_services_provider(provider) -> None:
    """Install the object that backs the services view.

    Passing ``None`` reverts to resolving services from ``app_instance()``.
    Intended for headless/CLI setups that build their own services holder.
    """
    _services._provider = provider
