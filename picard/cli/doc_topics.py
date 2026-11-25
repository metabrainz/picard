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


"""Documentation topics for `picard-cli docs`.

A topic is a named collection of documentation entries (for example the
scripting functions). It knows how to produce its entries as format-agnostic
data: a title and a Markdown body. Rendering to console, Markdown or HTML is
done separately (see :mod:`picard.cli.doc_formatters`), so a new topic only
has to implement :meth:`DocTopic.entries` and be added to :data:`DOC_TOPICS`.
"""

from abc import (
    ABC,
    abstractmethod,
)
from collections.abc import Iterable
from dataclasses import dataclass

from picard.extension_points.script_functions import ext_point_script_functions
from picard.i18n import gettext as _
from picard.script import script_function_names
from picard.tags.docs import (
    display_tag_full_description_markdown,
    documented_script_variables,
)


@dataclass(frozen=True, slots=True)
class DocEntry:
    """A single documentation item.

    Attributes:
        name: Identifier used to select the entry on the command line.
        title: Plain-text title, e.g. a function signature.
        body: Documentation text, in Markdown.
        code_title: True if the title is code and should be rendered as such.
        origin: Where the entry comes from, as shown to the user (for example
            "Plugin: my_plugin"), or an empty string for Picard itself.
        plugin_id: Identifier of the plugin providing the entry, if any.
    """

    name: str
    title: str
    body: str
    code_title: bool = False
    origin: str = ''
    plugin_id: str | None = None


# Module of the script functions provided by Picard itself
CORE_FUNCTIONS_MODULE = 'picard.script.functions'


def plugin_origin(plugin_id: str) -> str:
    """Return the origin label of an entry provided by a plugin."""
    # Same string as the script editor, so that it is already translated.
    # Only the plugin id is known here, the plugin manager is not available.
    return _("Plugin: {plugin_name}").format(plugin_name=plugin_id)


def function_origin(function) -> str:
    """Return the origin label of a script function, empty for Picard's own functions.

    Mirrors the script editor: functions of another module than the core one
    are labeled with the plugin if there is one, with the module otherwise.
    """
    if function.module is None or function.module == CORE_FUNCTIONS_MODULE:
        return ''
    if function.plugin_id:
        return plugin_origin(function.plugin_id)
    return function.module


class DocNotFoundError(Exception):
    """Raised when requested entries do not exist in a topic."""

    def __init__(self, names: Iterable[str]):
        self.names = tuple(names)
        super().__init__("no such entry: %s" % ', '.join(self.names))


class DocTopic(ABC):
    """A collection of documentation entries."""

    def __init__(self, name: str, title: str, help: str):
        self.name = name
        self.title = title
        self.help = help

    @abstractmethod
    def entries(self) -> list[DocEntry]:
        """Return all entries of the topic, sorted by name."""

    def normalize_name(self, name: str) -> str:
        """Return the entry name matching a name given by the user."""
        return name

    def select(self, names: Iterable[str] = ()) -> list[DocEntry]:
        """Return the entries called `names`, or all entries if `names` is empty.

        The entries are returned in the order of the topic, whatever the order
        of `names`. Duplicate names are ignored.

        Raises:
            DocNotFoundError: if one or more names do not exist.
        """
        entries = self.entries()
        wanted = {self.normalize_name(name) for name in names}
        if not wanted:
            return entries
        found = [entry for entry in entries if entry.name in wanted]
        missing = wanted.difference(entry.name for entry in found)
        if missing:
            raise DocNotFoundError(sorted(missing))
        return found


class ScriptFunctionsTopic(DocTopic):
    """Documentation of the scripting functions."""

    def __init__(self):
        super().__init__(
            name='script-functions',
            title='Script functions',
            help='scripting functions, as shown in the script editor',
        )

    def normalize_name(self, name: str) -> str:
        # Functions are written with a leading '$' in scripts
        return name.removeprefix('$')

    def entries(self) -> list[DocEntry]:
        # Same source as the script documentation of the GUI
        functions = dict(ext_point_script_functions)
        return [
            DocEntry(
                name=name,
                title=functions[name].markdown_title().strip('`') or f'${name}()',
                body=functions[name].markdown_body().strip(),
                code_title=True,
                origin=function_origin(functions[name]),
                plugin_id=functions[name].plugin_id,
            )
            for name in script_function_names(functions)
        ]


class ScriptVariablesTopic(DocTopic):
    """Documentation of the script variables."""

    def __init__(self):
        super().__init__(
            name='script-variables',
            title='Script variables',
            help='variables available to scripts, as shown in the script editor',
        )

    def normalize_name(self, name: str) -> str:
        # Variables are written between percent signs in scripts
        return name.strip('%')

    def entries(self) -> list[DocEntry]:
        return [
            DocEntry(
                name=var.script_name(),
                title=f'%{var.script_name()}%',
                body=display_tag_full_description_markdown(var),
                code_title=True,
                origin=plugin_origin(var.plugin_id) if var.plugin_id else '',
                plugin_id=var.plugin_id,
            )
            for var in documented_script_variables()
        ]


# Topic registry.
# Adding an entry here makes it available to `picard-cli docs`.
DOC_TOPICS = (ScriptFunctionsTopic(), ScriptVariablesTopic())


def get_topic(name: str) -> DocTopic:
    """Return the topic called `name`.

    Raises:
        KeyError: if there is no such topic.
    """
    for topic in DOC_TOPICS:
        if topic.name == name:
            return topic
    raise KeyError(name)
