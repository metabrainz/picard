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

"""Value resolution chain for scripts: object, context, then parser."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from picard.item import Item
from picard.script import ScriptParser


class ValueResolver(ABC):
    def __init__(self):
        self._next_resolver: ValueResolver | None = None

    def set_next(self, resolver: ValueResolver) -> ValueResolver:
        self._next_resolver = resolver
        return resolver

    @abstractmethod
    def can_resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    def resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str:
        raise NotImplementedError

    def handle(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str | None:
        if self.can_resolve(obj, simple_var, script, ctx, file_obj):
            try:
                result = self.resolve(obj, simple_var, script, ctx, file_obj)
                if result:
                    return result
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
        if self._next_resolver:
            return self._next_resolver.handle(obj, simple_var, script, ctx, file_obj)
        return None


class ObjectColumnResolver(ValueResolver):
    def can_resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> bool:
        return simple_var is not None and callable(getattr(obj, 'column', None))

    def resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str:
        column_fn = getattr(obj, 'column', None)
        if callable(column_fn):
            value = column_fn(simple_var)
            return value if isinstance(value, str) else ""
        return ""


class ContextVariableResolver(ValueResolver):
    def can_resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> bool:
        return simple_var is not None and ctx is not None

    def resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str:
        return ctx[simple_var] if simple_var in ctx else ""


class ScriptParserResolver(ValueResolver):
    def can_resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> bool:
        return True

    def resolve(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str:
        parser = ScriptParser()
        try:
            return parser.eval(script, context=ctx, file=file_obj)
        except Exception:
            return ""


class ValueResolverChain:
    def __init__(self):
        obj_resolver = ObjectColumnResolver()
        ctx_resolver = ContextVariableResolver()
        script_resolver = ScriptParserResolver()
        obj_resolver.set_next(ctx_resolver).set_next(script_resolver)
        self._first_resolver = obj_resolver

    def resolve_value(self, obj: Item, simple_var: str | None, script: str, ctx: Any, file_obj: Any) -> str:
        result = self._first_resolver.handle(obj, simple_var, script, ctx, file_obj)
        return str(result) if result is not None else ""
