#
# Picard, the next-generation MusicBrainz tagger
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

"""The commands that point to the MusicBrainz website: ``url`` and ``open``.

Both build the addresses with :class:`picard.browser.mburls.MusicBrainzUrls`,
as the graphical interface does to look an item up in the browser, from the
server of the configuration.
"""

from typing import Any
import webbrowser

from picard.album import NatAlbum
from picard.browser.mburls import MusicBrainzUrls
from picard.cli.engine.builtins.helpers import (
    arg_words,
    entity_item,
)
from picard.cli.engine.builtins.registry import command
from picard.cli.engine.commands import (
    EngineSession,
    UsageError,
)
from picard.cli.engine.result import (
    EngineItemResult,
    EngineResult,
)
from picard.cluster import Cluster
from picard.file import File
from picard.util.mbentity import parse_mb_entity


def _page_url(urls: MusicBrainzUrls, entity: Any, data: dict[str, Any]) -> 'str | None':
    """The address of the page of ``entity``, or None if it has none.

    An object that points at a MusicBrainz entity (an album, a track, a
    candidate, ...: ``data`` has its type and MBID) has the page of that entity.
    A file or a cluster that does not has the tag lookup of the website, as in the
    graphical interface. The container of the standalone recordings has none.
    """
    if isinstance(entity, NatAlbum):
        return None
    if data.get('entity_type') and data.get('mbid'):
        return urls.entity(data['entity_type'], data['mbid'])
    if isinstance(entity, (Cluster, File)):
        return urls.tag_lookup_item(entity)
    return None


def _pages(session: EngineSession, words: list[str]) -> EngineResult:
    """One item for the page of each object or MusicBrainz reference of ``words``, its address in ``url``."""
    urls = MusicBrainzUrls.from_config()
    references = [parse_mb_entity(word) for word in words]
    selector_words = [word for word, ref in zip(words, references, strict=True) if ref is None]
    # The MusicBrainz references come first, then the objects of the selector.
    items: list[EngineItemResult] = []
    for ref in references:
        if ref is not None:
            data = {'entity_type': ref.entity, 'mbid': ref.id, 'url': urls.entity(ref.entity, ref.id)}
            items.append(EngineItemResult(handle='', status='listed', data=data))
    entities, unresolved = session.resolve(selector_words) if selector_words else ([], [])
    for entity in entities:
        item = entity_item(session, entity, 'listed')
        url = _page_url(urls, entity, item.data)
        if url is None:
            item.status = 'unsupported'
        else:
            item.data['url'] = url
        items.append(item)
    return EngineResult(items=items, resolved=[item.handle for item in items if item.handle], unresolved=unresolved)


@command(
    'url',
    usage='url <selector|mbid>...',
    help="Print the address of the MusicBrainz page of objects.",
    args=('target',),
    arg_kinds=('selector',),
)
def _cmd_url(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Print the address of the page of objects on the MusicBrainz website.

    The server is the one of the configuration ('option get server_host'). An
    album has the page of its release, a track or a file that is matched the page
    of its recording, a lookup candidate or a release version the page of its
    release, a collection its own page. A file or a cluster that is not matched has
    the page of the tag lookup of the website, as 'Lookup in Browser' does in the
    graphical interface. The container of the standalone recordings has none, it is
    reported as unsupported.

    A MusicBrainz reference can be given instead of an object: a bare MBID,
    'release:<mbid>' or the address of a page.

    Examples:
      url a1
      url c1.f2
      url release:<mbid>
    """
    words = arg_words(args.get('target'))
    if not words:
        raise UsageError
    return _pages(session, words)


@command(
    'open',
    usage='open <selector|mbid>...',
    help="Open the MusicBrainz page of objects in a web browser.",
    args=('target',),
    arg_kinds=('selector',),
)
def _cmd_open(session: EngineSession, args: dict[str, Any]) -> EngineResult:
    """Open the page of objects on the MusicBrainz website in a web browser.

    It takes the same arguments as 'url', which only prints the addresses and is
    what to use on a machine without a browser (over ssh, say). If no browser can
    be started, the addresses are shown. The most pages opened at once is the
    setting open_max (see 'shell get').

    Examples:
      open a1
      open c1
    """
    words = arg_words(args.get('target'))
    if not words:
        raise UsageError
    result = _pages(session, words)
    pages = [item for item in result.items if item.data.get('url')]
    limit = session.settings.limit('open_max')
    if limit is not None and len(pages) > limit:
        return EngineResult.failure(
            f"open: {len(pages)} pages, at most {limit} are opened at once "
            f"(use 'url' to list their addresses, or 'shell set open_max')",
            unresolved=result.unresolved,
        )
    opened_any = False
    for item in pages:
        try:
            opened = webbrowser.open(item.data['url'])
        except webbrowser.Error:
            opened = False
        item.status = 'opened' if opened else 'open_failed'
        opened_any = opened_any or opened
    if pages and not opened_any:
        result.message = "no web browser could be started, the addresses are above ('url' prints them)"
    return result
