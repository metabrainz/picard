### Custom Columns API (for programmers)

Public API to define, register, sort, and persist custom columns for Picard’s File and Album views.

---

### Overview and flow

Motivation: Extend Picard’s File/Album views with columns that compute values dynamically (from tags, scripts, or code) and integrate with sorting, sizing and visibility like built-ins.

Lifecycle at a glance:
- Create: Build a `CustomColumn` via factory helpers in `picard.ui.itemviews.custom_columns.factory` (e.g., `make_field_column`, `make_script_column`, `make_callable_column`, `make_transformed_column`) or construct `CustomColumn` with your own provider.
- Register: Add the column to live views with `registry.register(column, add_to_file_view=..., add_to_album_view=..., insert_after_key=...)`. This inserts into the mutable column collections used by the File/Album widgets.
- Persist (optional): Store UI-defined columns as specs using `picard.ui.itemviews.custom_columns.storage`. Use `CustomColumnSpec` + `register_and_persist(spec)` to save to config and auto-register; `load_persisted_columns_once()` restores saved columns on startup.
- Paint (Qt): Once registered, the column participates like any other. Values come from the provider’s `evaluate(item)`. The header and sections are owned by the Qt views; width/resize hints are applied during registration (see `registry._apply_column_width_to_headers`). Painting is handled by the standard header; only image columns overlay custom paint.

Key modules:
- `custom_columns.__init__`: public API surface (factories, adapters, registry).
- `column.CustomColumn`: column type bridging providers to Picard’s `Column`.
- `factory`: helpers to create columns and infer sort behavior.
- `registry`: insertion/removal into File/Album views and live header updates.
- `providers`: reusable value providers and transforms.
- `sorting_adapters`: add `.sort_key` for `ColumnSortType.SORTKEY` sorting.
- `storage`: persist/load/register UI-defined column specs.

### Imports

```python
from picard.ui.columns import ColumnAlign, ColumnSortType
from picard.ui.itemviews.custom_columns import (
    CustomColumn,
    make_field_column,
    make_script_column,
    make_transformed_column,
    make_provider_column,
    make_callable_column,
    registry,
    # Sorting adapters
    CasefoldSortAdapter,
    DescendingCasefoldSortAdapter,
    NumericSortAdapter,
    DescendingNumericSortAdapter,
    LengthSortAdapter,
    RandomSortAdapter,
    ArticleInsensitiveAdapter,
    CompositeSortAdapter,
    NullsLastAdapter,
    NullsFirstAdapter,
    CachedSortAdapter,
    ReverseAdapter,
)
```

---

### Quick start

Field reference column:
```python
col = make_field_column(
    title="Bitrate",
    key="~bitrate",  # same key you would pass to obj.column(key)
    width=80,
    align=ColumnAlign.RIGHT,
)
registry.register(col, add_to_file_view=True, add_to_album_view=False, insert_after_key="length")
```

Script column:
```python
script = "$if(%title%,$if2(%artist%,Unknown Artist) - $if2(%title%,Unknown Title),$if2(%albumartist%,Unknown Artist) - $if2(%album%,Unknown Album))"
col = make_script_column(
    title="Artist – Title",
    key="artist_title_script",
    script=script,
    width=280,
    align=ColumnAlign.LEFT,
)
registry.register(col, add_to_album_view=True, insert_after_key="title")
```

Transformed base field:
```python
from picard.ui.itemviews.custom_columns.providers import FieldReferenceProvider

upper_title = make_transformed_column(
    title="TITLE (UPPER)",
    key="title_upper",
    base=FieldReferenceProvider("title"),
    transform=lambda s: s.upper(),
)
registry.register(upper_title)
```

Callable-backed column:
```python
from picard.item import Item

def file_ext(item: Item) -> str:
    return item.column("~extension")

col = make_callable_column("Ext", key="ext", func=file_ext, sort_type=ColumnSortType.TEXT)
registry.register(col)
```

---

### Registration

```python
registry.register(column,
                  add_to_file_view=True,
                  add_to_album_view=True,
                  insert_after_key="title")
```
- Inserts into live UI collections (`FILEVIEW_COLUMNS`, `ALBUMVIEW_COLUMNS`).
- `insert_after_key` places the column after an existing key; falls back to append if not found.
- Idempotent per `key` (re-registration replaces existing instances). Use `registry.unregister(key)` to remove.

---

### Sorting

- Default sort type is text. To supply a computed sort key, wrap the provider with an adapter that implements `sort_key` and use `ColumnSortType.SORTKEY`.

Case-insensitive sort for a script column:
```python
base = make_script_column("Artist – Title", key="artist_title_script", script=script)
sorted_provider = CasefoldSortAdapter(base.provider)  # provides .sort_key
sorted_col = CustomColumn(
    title=base.title,
    key=base.key,
    provider=sorted_provider,
    width=base.width,
    align=base.align,
    sort_type=ColumnSortType.SORTKEY,
)
registry.register(sorted_col, insert_after_key="title")
```

Available adapters (imported from `picard.ui.itemviews.custom_columns`):
- CasefoldSortAdapter: case-insensitive (str.casefold) text sort
- DescendingCasefoldSortAdapter: descending case-insensitive text sort
- NumericSortAdapter: numeric sort using parser (default float)
- DescendingNumericSortAdapter: descending numeric (negated value)
- LengthSortAdapter: sort by string length
- RandomSortAdapter: deterministic pseudo-random by value and seed
- ArticleInsensitiveAdapter: ignore leading articles (e.g. a, an, the)
- CompositeSortAdapter: tuple sort from multiple key functions
- NullsFirstAdapter: empty/whitespace values sort first
- NullsLastAdapter: empty/whitespace values sort last
- CachedSortAdapter: cache sort keys for performance
- ReverseAdapter: invert existing sort key (numeric or string)

You can also create a custom provider that implements `sort_key` to participate in `SORTKEY` sorting.

---

### Providers

Protocols (typing only):
```python
from picard.ui.itemviews.custom_columns import ColumnValueProvider, SortKeyProvider
```

Built-ins:
- `FieldReferenceProvider(key: str)`: returns `obj.column(key)`; safe on missing keys.
- `TransformProvider(base: ColumnValueProvider, transform: Callable[[str], str])`: applies a string transform.
- `CallableProvider(func: Callable[[Item], str])`: wraps a Python callable.
- Script provider is created via `make_script_column(...)` (do not instantiate directly).

Factory helpers return a `CustomColumn` and infer a sane `sort_type` when possible:
- `make_field_column(...)`
- `make_script_column(...)` (tunable: `max_runtime_ms`, `cache_size`, optional parser or factory)
- `make_transformed_column(...)`
- `make_callable_column(...)`
- `make_provider_column(...)`

`CustomColumn` signature:
```python
CustomColumn(title: str,
             key: str,
             provider: ColumnValueProvider,
             width: int | None = None,
             align: ColumnAlign = ColumnAlign.LEFT,
             sort_type: ColumnSortType = ColumnSortType.TEXT,
             always_visible: bool = False)
```

---

### Persistence utilities

Serialize specs to config and (optionally) auto-register columns.

```python
from picard.ui.itemviews.custom_columns.storage import (
    CustomColumnSpec, CustomColumnKind, TransformName,
    build_column_from_spec,
    load_specs_from_config, save_specs_to_config,
    add_or_update_spec, delete_spec_by_key, get_spec_by_key,
    register_and_persist, unregister_and_delete,
    load_persisted_columns_once,
)

# Create and persist a script spec
spec = CustomColumnSpec(
    title="Artist – Title",
    key="artist_title_script",
    kind=CustomColumnKind.SCRIPT,
    expression=script,
    width=280,
    align="LEFT",
    add_to_file_view=False,
    add_to_album_view=True,
    insert_after_key="title",
)
register_and_persist(spec)  # saves to config and registers in views

# Load and register all saved specs once (idempotent)
load_persisted_columns_once()

# Remove and delete
unregister_and_delete("artist_title_script")
```

Notes:
- `CustomColumnSpec.align` accepts "LEFT" or "RIGHT" (mapped to `ColumnAlign`).
- `CustomColumnSpec.kind`: `FIELD`, `SCRIPT`, or `TRANSFORM`.
- `TRANSFORM` specs use `expression` as the base field and optional `transform: TransformName`.
- Registry insertion uses the spec’s `add_to_file_view`, `add_to_album_view`, and `insert_after_key`.

---

### Field keys and scripting

- Field keys are the same strings used with `obj.column(key)` and Picard variables without percent signs (e.g. `title`, `albumartist`, `~bitrate`).
- Script expressions use the standard Picard scripting language (e.g. `$if()`, `$if2()`, `%artist%`).
- See `picard.const.tags.ALL_TAGS` for the authoritative list of variables.

---

### Runtime & safety

- Script provider has configurable `max_runtime_ms` and internal caching; errors return empty strings rather than raising.
- `registry.register` is UI-safe after the main window has initialized; re-entrant calls replace existing keys.
- `registry.unregister(key)` removes from both views (if present).
