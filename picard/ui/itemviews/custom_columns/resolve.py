# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 The MusicBrainz Team
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

"""Value resolution chain for scripts: object, context, then parser.

Adds support for injecting a reusable script parser and caching compiled
scripts to improve stability and performance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from picard.item import Item
from picard.log import debug
from picard.script import ScriptParser


class ValueResolver(ABC):
    """Define the abstract base class for value resolvers.

    Implements the chain-of-responsibility pattern. Subclasses decide whether
    they can resolve a value and either return a result or forward the request
    to the next resolver in the chain.

    Notes
    -----
    Use :meth:`set_next` to link resolvers together in the desired order.
    """

    def __init__(self):
        self._next_resolver: ValueResolver | None = None

    def set_next(self, resolver: ValueResolver) -> ValueResolver:
        """Set the next resolver in the chain.

        Parameters
        ----------
        resolver
            The resolver to be invoked if this resolver cannot produce
            a value.

        Returns
        -------
        ValueResolver
            The same resolver instance passed in, to support fluent
            chaining (``a.set_next(b).set_next(c)``).
        """
        self._next_resolver = resolver
        return resolver

    @abstractmethod
    def can_resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> bool:
        """Indicate whether this resolver can handle the given request.

        Parameters
        ----------
        obj
            The item for which a value is being computed.
        simple_var
            Extracted simple variable name (when ``script`` is a plain
            ``%var%``), else ``None``.
        script
            The full scripting expression.
        ctx
            The evaluation context (typically a ``Metadata`` mapping).
        file_obj
            Associated file object where applicable.

        Returns
        -------
        bool
            ``True`` if this resolver can attempt to resolve the value,
            otherwise ``False``.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str:
        """Compute the value for the given request.

        Parameters
        ----------
        obj, simple_var, script, ctx, file_obj
            See :meth:`can_resolve` for parameter semantics.

        Returns
        -------
        str
            The computed value. Should return an empty string on failure.
        """
        raise NotImplementedError

    def handle(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str | None:
        """Attempt resolution or delegate to the next resolver.

        Parameters
        ----------
        obj, simple_var, script, ctx, file_obj
            See :meth:`can_resolve` for parameter semantics.

        Returns
        -------
        str | None
            The resolved value, or ``None`` if no resolver in the chain
            produced a non-empty result.
        """
        if self.can_resolve(obj, simple_var, script, ctx, file_obj):
            try:
                result = self.resolve(obj, simple_var, script, ctx, file_obj)
                if result:
                    return result
            except (TypeError, ValueError, AttributeError, KeyError) as e:
                debug("ValueResolver.handle suppressed error: %r", e)
        if self._next_resolver:
            return self._next_resolver.handle(obj, simple_var, script, ctx, file_obj)
        return None


class ObjectColumnResolver(ValueResolver):
    """Resolve simple variables through ``obj.column``.

    This resolver applies only when the script is a simple variable and the
    object exposes a callable ``column`` attribute.
    """

    def can_resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> bool:
        """Return ``True`` if ``obj.column`` can be used for resolution."""
        return simple_var is not None and callable(getattr(obj, 'column', None))

    def resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str:
        """Return the string value from ``obj.column(simple_var)`` or ``""``."""
        column_fn = getattr(obj, 'column', None)
        if callable(column_fn):
            value = column_fn(simple_var)
            return value if isinstance(value, str) else ""
        return ""


class ContextVariableResolver(ValueResolver):
    """Resolve simple variables from the provided evaluation context."""

    def can_resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> bool:
        """Return ``True`` if ``simple_var`` is available in ``ctx``."""
        return simple_var is not None and ctx is not None

    def resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str:
        """Return the value of ``simple_var`` from ``ctx`` or ``""`` if missing."""
        return ctx[simple_var] if simple_var in ctx else ""


class ScriptParserResolver(ValueResolver):
    """Resolve using a reusable :class:`~picard.script.parser.ScriptParser`.

    A single parser instance is reused to avoid repeatedly loading global
    function state. Parsed script expressions are cached per script string to
    skip re-parsing on subsequent evaluations.

    Parameters
    ----------
    parser
        Optional parser instance to reuse for all evaluations.
    parser_factory
        Optional factory for creating the parser lazily on first use.
    """

    def __init__(self, parser: ScriptParser | None = None, parser_factory: Callable[[], ScriptParser] | None = None):
        super().__init__()
        self._parser = parser
        self._parser_factory = parser_factory
        self._compiled_by_script: dict[str, Any] = {}

    def _get_parser(self) -> ScriptParser:
        if self._parser is not None:
            return self._parser
        if self._parser_factory is not None:
            self._parser = self._parser_factory()
            return self._parser
        self._parser = ScriptParser()
        return self._parser

    def _compile_script(self, parser: ScriptParser, script: str) -> Any:
        """Load functions best-effort and parse the script.

        Any exception is handled by the caller; this method only logs failures
        when loading functions, as this is non-fatal for parsing.
        """
        try:
            parser.load_functions()
        except Exception as e:  # pragma: no cover - defensive
            debug("Failed to load script functions: %r", e)
        return parser.parse(script, True)

    def can_resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> bool:
        """Always return ``True``; parser is the last step in the chain."""
        return True

    def resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str:
        """Evaluate the script using the reusable parser.

        Parameters
        ----------
        obj, simple_var, script, ctx, file_obj
            See :meth:`ValueResolver.can_resolve` for parameter semantics.

        Returns
        -------
        str
            The evaluated value, or ``""`` if an error occurs.
        """
        parser = self._get_parser()
        try:
            # Compile once per script; parsing with functions=True requires functions already loaded.
            if script not in self._compiled_by_script:
                self._compiled_by_script[script] = self._compile_script(parser, script)

            # Set evaluation context and evaluate compiled expression
            parser.context = ctx
            parser.file = file_obj
            return self._compiled_by_script[script].eval(parser)
        except Exception as e:
            # Return empty string on any error, but log at debug for diagnostics
            debug("Script evaluation failed: %r (script=%r)", e, script)
            return ""


class ValueResolverChain:
    """Build and execute the value resolution chain.

    The chain consists of:

    1. :class:`ObjectColumnResolver` — ``obj.column`` for simple variables
    2. :class:`ContextVariableResolver` — lookup in evaluation context
    3. :class:`ScriptParserResolver` — full script evaluation

    Parameters
    ----------
    parser
        Optional parser instance to reuse for all evaluations.
    parser_factory
        Optional factory for creating the parser lazily on first use.
    """

    def __init__(self, *, parser: ScriptParser | None = None, parser_factory: Callable[[], ScriptParser] | None = None):
        obj_resolver = ObjectColumnResolver()
        ctx_resolver = ContextVariableResolver()
        script_resolver = ScriptParserResolver(parser=parser, parser_factory=parser_factory)
        obj_resolver.set_next(ctx_resolver).set_next(script_resolver)
        self._first_resolver = obj_resolver

    def resolve_value(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str:
        """Resolve the value using the configured chain.

        Parameters
        ----------
        obj, simple_var, script, ctx, file_obj
            See :meth:`ValueResolver.can_resolve` for parameter semantics.

        Returns
        -------
        str
            The resolved value, or an empty string if unresolved.
        """
        result = self._first_resolver.handle(obj, simple_var, script, ctx, file_obj)
        return str(result) if result is not None else ""
