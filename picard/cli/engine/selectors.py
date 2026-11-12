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

"""Selector parsing and resolution.

A selector is a compact reference to a set of working-set entities — the same
syntax a human types at the console and an agent passes in an MCP ``selector``
argument. See ``docs/CommandEngine.md`` for the full target grammar.

This module implements a documented SUBSET of that grammar:

- a single handle: ``a1``, ``c2``, ``f3``
- a type wildcard: ``a*`` (all albums), ``c*``, ``f*``, ``t*``
- a range of ordinals: ``f1-12``, ``a1-3`` (the live entities among them)
- the universal wildcard: ``*`` (all top-level objects)
- a comma-separated union of the above: ``a1, c2, f3``
- a PATH into the working set: segments separated by ``.``, each one selecting
  children of the previous one (``a1.d2.t3``, ``c1.f*``, ``c1.f2-5``, ``u.f*``, ``c1.m2``).
  A segment is a type prefix plus an ordinal or ``*``; ``u`` (a bucket of
  unplaced files) takes no number. Paths are positions, resolved when the
  command runs; the stable identity of an entity remains its plain handle.
  What a segment means under a given parent is decided by the injected
  :class:`Navigator`, so this module stays independent of the entity types.

Not yet implemented (reserved; the parse/resolve shape leaves room for them so
they slot in without reshaping): bare-ordinal sticky prefixes (``a1,2,3``)
and exclusion (``!a2``). Attempting that syntax raises
:class:`SelectorError` rather than silently mis-parsing.

Resolution returns ``(entities, unresolved)``:
- *entities*: the live entities the selector matched (de-duplicated, order of
  first appearance).
- *unresolved*: tokens that parsed but matched no live entity (e.g. a handle
  that was never minted or whose entity has been removed). A non-empty
  ``unresolved`` means the caller under-acted; it is surfaced to the frontend
  (console warns, MCP returns it) rather than silently dropped.
"""

from collections.abc import (
    Callable,
    Iterable,
    Sequence,
)
from dataclasses import dataclass
import re
from typing import (
    Any,
    Protocol,
)


# Handle prefixes the subset recognises. Kept explicit so an unknown prefix is
# a clear error. Extend here (plus the enumerator) as entity kinds are added.
KNOWN_PREFIXES = frozenset({'f', 'c', 'a', 't', 'm', 'v', 'k', 'd', 'u'})

# Prefixes that name a single thing in their scope and so take no number: ``u``
# is the bucket of unplaced files (top level: the unclustered files; under an
# album: its unmatched files).
SINGLETON_PREFIXES = frozenset({'u'})

# Prefixes that make up the universal top-level set ``*`` (mirrors the GUI panes:
# unclustered files, clusters, albums/NAT). NOT tracks.
TOP_LEVEL_PREFIXES = ('f', 'c', 'a')


# The most ordinals a range can span, so that ``f1-999999999`` is refused rather than looked up.
MAX_RANGE_SPAN = 10000

# ``1-12``: the part of a range term that follows the prefix.
_RANGE = re.compile(r'(\d+)-(\d+)')


# An enumerator maps a handle prefix to the live entities of that kind, in a
# stable order. Injected so this module does not depend on Workspace/core.
Enumerator = Callable[[str], Iterable[Any]]

# Resolves a handle string to its entity, or None if unknown/expired
# (HandleRegistry.resolve satisfies this).
HandleResolver = Callable[[str], Any]


class SelectorError(ValueError):
    """Raised when a selector string is malformed or uses unsupported syntax."""


@dataclass(frozen=True)
class Segment:
    """One ``.``-separated step of a path: ``t3``, ``t1-3``, ``d*`` or ``u``.

    ``kind`` is ``'ordinal'`` (value: int), ``'range'`` (value: the ``(first,
    last)`` ordinals), ``'wildcard'`` or ``'single'`` (a prefix that takes no
    number, see :data:`SINGLETON_PREFIXES`).
    """

    prefix: str
    kind: str
    value: Any = None


class Navigator(Protocol):
    """Walks a path through the working set; implemented next to the entity types.

    A *node* is whatever the navigator wants to step from: usually an entity,
    but it may also be a lightweight view (e.g. one disc of an album) that
    :meth:`finish` expands into entities. ``None`` stands for the root.
    """

    def step(self, node: Any, segment: Segment) -> Iterable[Any]:
        """Return the nodes ``segment`` selects under ``node``.

        Raise :class:`SelectorError` for a segment that is not valid under
        ``node`` (so the user is told why, rather than getting nothing).
        """
        ...

    def finish(self, node: Any) -> Iterable[Any]:
        """Return the entities a path ending at ``node`` stands for."""
        ...

    def segments(self, node: Any) -> Iterable[str]:
        """Return the texts of the segments that can follow ``node`` (``t*``, ``d2``, ...)."""
        ...


@dataclass(frozen=True)
class Term:
    """One parsed selector term."""

    prefix: str  # a handle prefix, or '' for a bare universal '*'
    kind: str  # 'ordinal' | 'range' | 'wildcard' | 'single'
    value: Any  # int (ordinal) | (first, last) (range) | None (wildcard, single)
    raw: str = ''  # original token text, for unresolved reporting
    path: tuple[Segment, ...] = ()  # segments after the first, for ``a1.t3``


def parse_selector(text: 'str | Sequence[str]') -> list[Term]:
    """Parse a selector into a list of :class:`Term`.

    ``text`` is a selector string, or the whitespace-separated tokens a command
    line splits it into (``a1, c2`` arrives as ``['a1,', 'c2']``); the tokens
    are re-joined as a comma-separated union.

    Implements the subset described in the module docstring. Raises
    :class:`SelectorError` on malformed input or unsupported (reserved) syntax.
    """
    if text is None:
        raise SelectorError("selector is None")
    if not isinstance(text, str):
        text = ','.join(token.strip().strip(',') for token in text)
    terms: list[Term] = []
    for raw_token in text.split(','):
        token = raw_token.strip()
        if not token:
            raise SelectorError(f"empty selector term in {text!r}")
        terms.append(_parse_token(token))
    if not terms:
        raise SelectorError("empty selector")
    return terms


def _parse_token(token: str) -> Term:
    # Reserved syntax — reject explicitly (clearer than a confusing parse error).
    if token.startswith('!'):
        raise SelectorError(f"exclusion ('!') is not supported yet: {token!r}")

    head, *tail = token.split('.')

    # Universal wildcard.
    if head == '*':
        if tail:
            raise SelectorError(f"the universal '*' cannot be followed by a path: {token!r}")
        return Term(prefix='', kind='wildcard', value=None, raw=token)

    first = _parse_segment(head, token)
    path = tuple(_parse_segment(part, token) for part in tail)
    return Term(prefix=first.prefix, kind=first.kind, value=first.value, raw=token, path=path)


def _parse_segment(text: str, token: str) -> Segment:
    """Parse one path segment (``a1``, ``t*``, ``u``) of ``token``."""
    if not text:
        raise SelectorError(f"empty path segment in {token!r}")
    prefix, rest = _split_prefix(text)
    if prefix is None:
        raise SelectorError(f"selector term must start with a type prefix: {token!r}")
    if prefix not in KNOWN_PREFIXES:
        raise SelectorError(f"unknown selector prefix {prefix!r} in {token!r}")

    if prefix in SINGLETON_PREFIXES:
        if rest:
            raise SelectorError(f"{prefix!r} takes no number in {token!r}")
        return Segment(prefix, 'single')
    if rest == '*':
        return Segment(prefix, 'wildcard')
    if rest.isdigit():
        return Segment(prefix, 'ordinal', int(rest))
    if match := _RANGE.fullmatch(rest):
        first, last = int(match.group(1)), int(match.group(2))
        if first < 1:
            raise SelectorError(f"ordinals start at 1 in {token!r}")
        if first > last:
            raise SelectorError(f"reversed range in {token!r}, did you mean {prefix}{last}-{first}?")
        if last - first >= MAX_RANGE_SPAN:
            raise SelectorError(f"range too large in {token!r} (at most {MAX_RANGE_SPAN} ordinals)")
        return Segment(prefix, 'range', (first, last))
    if rest == '':
        raise SelectorError(f"selector term {token!r} has a prefix but no ordinal or '*'")
    # Bare-ordinal sticky prefixes are part of the full grammar, not the subset.
    raise SelectorError(f"malformed selector term: {token!r}")


def _split_prefix(token: str) -> 'tuple[str | None, str]':
    """Split a leading alphabetic prefix from the rest: ``a12`` -> ('a', '12')."""
    i = 0
    while i < len(token) and token[i].isalpha():
        i += 1
    if i == 0:
        return None, token
    return token[:i], token[i:]


def resolve_selector(
    text: 'str | Sequence[str]',
    resolve_handle: HandleResolver,
    enumerate_prefix: Enumerator,
    navigator: 'Navigator | None' = None,
) -> 'tuple[list[Any], list[str]]':
    """Resolve ``text`` to ``(entities, unresolved)``.

    ``resolve_handle(handle)`` returns the entity for a handle or None.
    ``enumerate_prefix(prefix)`` yields the live entities for a wildcard.
    ``navigator`` walks the ``.`` paths (``a1.t3``); without one, a path is a
    :class:`SelectorError`.

    Entities are de-duplicated by identity, preserving first-appearance order.
    Tokens that match no live entity are collected in ``unresolved``.
    """
    terms = parse_selector(text)

    entities: list[Any] = []
    seen: set[int] = set()
    unresolved: list[str] = []

    def add(entity: Any) -> None:
        key = id(entity)
        if key not in seen:
            seen.add(key)
            entities.append(entity)

    for term in terms:
        if term.path or term.kind == 'single':
            if navigator is None:
                raise SelectorError(f"paths are not supported here: {term.raw!r}")
            found = _resolve_path(term, resolve_handle, enumerate_prefix, navigator)
            if found is None:
                unresolved.append(term.raw)
            else:
                for entity in found:
                    add(entity)
        elif term.kind == 'ordinal':
            handle = f"{term.prefix}{term.value}"
            entity = resolve_handle(handle)
            if entity is None:
                unresolved.append(term.raw)
            else:
                add(entity)
        elif term.kind == 'range':
            found = _live_in_range(term.prefix, term.value, resolve_handle)
            if not found:
                unresolved.append(term.raw)
            for entity in found:
                add(entity)
        elif term.kind == 'wildcard':
            prefixes = (term.prefix,) if term.prefix else TOP_LEVEL_PREFIXES
            for prefix in prefixes:
                for entity in enumerate_prefix(prefix):
                    add(entity)

    return entities, unresolved


def resolve_nodes(
    text: str,
    resolve_handle: HandleResolver,
    enumerate_prefix: Enumerator,
    navigator: Navigator,
) -> list[Any]:
    """Walk a single selector term and return the nodes it ends at, unexpanded.

    Unlike :func:`resolve_selector` this does not call ``navigator.finish``: a
    path ending at a disc yields the disc itself, not its tracks. That is what
    completion needs, to ask what can follow. An unresolved term gives ``[]``.
    """
    terms = parse_selector(text)
    if len(terms) != 1:
        raise SelectorError(f"expected a single selector term, got {text!r}")
    nodes = _walk(terms[0], resolve_handle, enumerate_prefix, navigator)
    return [] if nodes is None else nodes


def _walk(
    term: Term,
    resolve_handle: HandleResolver,
    enumerate_prefix: Enumerator,
    navigator: Navigator,
) -> 'list[Any] | None':
    """Follow ``term`` and return the nodes it ends at, or None if a numbered step found nothing.

    A wildcard step that matches nothing is just an empty result; a step naming
    one ordinal that does not exist means the reference is unresolved.
    """
    try:
        if term.kind == 'ordinal':
            entity = resolve_handle(f"{term.prefix}{term.value}")
            nodes = [] if entity is None else [entity]
        elif term.kind == 'range':
            nodes = _live_in_range(term.prefix, term.value, resolve_handle)
        elif term.kind == 'wildcard':
            nodes = list(enumerate_prefix(term.prefix))
        else:
            nodes = _unique(navigator.step(None, Segment(term.prefix, 'single')))
        if term.kind in {'ordinal', 'range'} and not nodes:
            return None

        for segment in term.path:
            stepped = []
            for node in nodes:
                for single in _ordinals_of(segment):
                    stepped.extend(navigator.step(node, single))
            nodes = _unique(stepped)
            if segment.kind != 'wildcard' and not nodes:
                return None
        return nodes
    except SelectorError as e:
        raise SelectorError(f"{term.raw}: {e}") from None


def _resolve_path(
    term: Term,
    resolve_handle: HandleResolver,
    enumerate_prefix: Enumerator,
    navigator: Navigator,
) -> 'list[Any] | None':
    """Walk ``term``'s path; return the entities it stands for, or None if unresolved."""
    nodes = _walk(term, resolve_handle, enumerate_prefix, navigator)
    if nodes is None:
        return None
    entities = []
    for node in nodes:
        entities.extend(navigator.finish(node))
    return entities


def _live_in_range(prefix: str, bounds: 'tuple[int, int]', resolve_handle: HandleResolver) -> list[Any]:
    """The live entities among ``prefix<first>`` to ``prefix<last>``; a handle that matches none is skipped."""
    first, last = bounds
    entities = (resolve_handle(f"{prefix}{number}") for number in range(first, last + 1))
    return [entity for entity in entities if entity is not None]


def _ordinals_of(segment: Segment) -> list[Segment]:
    """The segments to step with for ``segment``: itself, or one per ordinal of a range."""
    if segment.kind != 'range':
        return [segment]
    first, last = segment.value
    return [Segment(segment.prefix, 'ordinal', number) for number in range(first, last + 1)]


def _unique(nodes: Iterable[Any]) -> list[Any]:
    """Drop duplicate nodes (by identity), keeping first-appearance order."""
    seen: set[int] = set()
    result = []
    for node in nodes:
        if id(node) not in seen:
            seen.add(id(node))
            result.append(node)
    return result
