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


"""Output formats for `picard-cli docs`.

Each formatter turns the entries of a topic into a string. The entries carry
Markdown, so the Markdown formatter is the reference and the others derive
from it: HTML by converting it, the console one by rendering the few Markdown
constructs used in Picard documentation (code spans, bold, links, indented
code blocks) with terminal colors.
"""

from collections.abc import (
    Callable,
    Sequence,
)
from html import escape
import json
import re
import shutil
import textwrap

from picard.cli.doc_topics import (
    DocEntry,
    DocTopic,
)
from picard.cli.output import CliOutput


try:
    from markdown import markdown
except ImportError:
    markdown = None  # type: ignore[assignment]


class DocFormatError(Exception):
    """Raised when documentation cannot be rendered in the requested format."""


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
code {{ font-family: monospace; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""

# Inline Markdown constructs, matched in a single pass so that the content of
# a code span is never interpreted as bold, link or escape.
_INLINE_RE = re.compile(
    r'`(?P<code>[^`]+)`'
    r'|\*\*(?P<bold>.+?)\*\*'
    r'|\[(?P<text>[^\]]+)\]\((?P<url>[^)]+)\)'
    r'|\\(?P<escaped>[\\`*{}\[\]()$])'
)
_CODE_INDENT = '    '
# Constructs that must not be broken across lines when wrapping a paragraph
_UNBREAKABLE_RE = re.compile(r'`[^`]+`|\*\*.+?\*\*|\[[^\]]+\]\([^)]+\)')
_NBSP = '\u00a0'
MAX_WIDTH = 100
# A line made only of emphasized text, e.g. "_Since Picard 2.8_"
_EMPHASIS_LINE_RE = re.compile(r'^_(?P<text>[^_].*[^_]|[^_])_$')


def _entry_markdown(entry: DocEntry) -> str:
    """Return the body of an entry, followed by its origin if it is not Picard itself."""
    if not entry.origin:
        return entry.body
    # Written as the "Since" lines of the documentation, so rendered the same way
    return f'{entry.body}\n\n_{entry.origin}_'.lstrip('\n')


def render_markdown(topic: DocTopic, entries: Sequence[DocEntry], output: CliOutput) -> str:
    """Render entries as a Markdown document."""
    parts = [f'# {topic.title}']
    for entry in entries:
        title = f'`{entry.title}`' if entry.code_title else entry.title
        parts.append(f'## {title}\n\n{_entry_markdown(entry)}'.rstrip())
    return '\n\n'.join(parts) + '\n'


def render_json(topic: DocTopic, entries: Sequence[DocEntry], output: CliOutput) -> str:
    """Render entries as JSON, for use by other tools."""
    data = {
        'topic': topic.name,
        'title': topic.title,
        'entries': [
            {
                'name': entry.name,
                'title': entry.title,
                'body': entry.body,
                'code_title': entry.code_title,
                'origin': entry.origin,
                'plugin_id': entry.plugin_id,
            }
            for entry in entries
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + '\n'


def render_html(topic: DocTopic, entries: Sequence[DocEntry], output: CliOutput) -> str:
    """Render entries as a standalone HTML document."""
    if markdown is None:
        raise DocFormatError("the 'markdown' Python module is required for HTML output")
    body = markdown(render_markdown(topic, entries, output))
    return HTML_TEMPLATE.format(title=escape(topic.title), body=body)


def _render_inline(text: str, output: CliOutput) -> str:
    """Render the inline Markdown constructs of a line of text."""

    def replace(match: re.Match) -> str:
        # Without colors, keep the Markdown markers so that code and emphasis
        # are still distinguishable from the surrounding text.
        if match['code'] is not None:
            return output.cyan(match['code']) if output.color else match[0]
        if match['bold'] is not None:
            return output.bold(match['bold']) if output.color else match[0]
        if match['text'] is not None:
            return f'{match["text"]} ({output.d_url(match["url"])})'
        return match['escaped']

    return _INLINE_RE.sub(replace, text)


def _wrap(text: str, width: int) -> list[str]:
    """Wrap a paragraph, keeping code spans, bold text and links on one line."""
    protected = _UNBREAKABLE_RE.sub(lambda match: match[0].replace(' ', _NBSP), text)
    lines = textwrap.wrap(protected, width, break_long_words=False, break_on_hyphens=False)
    return [line.replace(_NBSP, ' ') for line in lines]


def _render_paragraph(lines: list[str], output: CliOutput, width: int) -> list[str]:
    """Render the lines of a paragraph, reflowed to `width`."""
    text = ' '.join(line.strip() for line in lines)
    emphasis = _EMPHASIS_LINE_RE.match(text)
    if emphasis and output.color:
        return [output.dim(emphasis['text'])]
    return [_render_inline(line, output) for line in _wrap(text, width)]


def _render_body(body: str, output: CliOutput, width: int) -> str:
    """Render a Markdown body for the console.

    Paragraphs are reflowed to `width`, as a Markdown renderer would do, since
    the line breaks of the source text are arbitrary. Code blocks (indented by
    4 spaces after a blank line) are kept as is.
    """
    rendered: list[str] = []
    paragraph: list[str] = []

    def flush():
        if paragraph:
            rendered.extend(_render_paragraph(paragraph, output, width))
            paragraph.clear()

    previous = ''
    in_code = False
    for line in body.splitlines():
        if line.startswith(_CODE_INDENT) and (in_code or not previous.strip()):
            flush()
            in_code = True
            rendered.append(output.dim(line))
        else:
            in_code = False
            if line.strip():
                paragraph.append(line)
            else:
                flush()
                rendered.append('')
        previous = line
    flush()
    return '\n'.join(rendered)


def render_console(topic: DocTopic, entries: Sequence[DocEntry], output: CliOutput, width: int | None = None) -> str:
    """Render entries for a terminal, using colors if `output` has them enabled.

    Text is wrapped to `width`, by default the terminal width up to MAX_WIDTH.
    """
    width = width or min(shutil.get_terminal_size().columns, MAX_WIDTH)
    parts = []
    for entry in entries:
        title = output.d_command(entry.title) if entry.code_title else output.d_name(entry.title)
        parts.append(f'{title}\n\n{_render_body(_entry_markdown(entry), output, width)}'.rstrip())
    return '\n\n'.join(parts) + '\n'


Formatter = Callable[[DocTopic, Sequence[DocEntry], CliOutput], str]

# Format registry.
# Adding an entry here makes the format available to `picard-cli docs show`.
FORMATTERS: dict[str, Formatter] = {
    'console': render_console,
    'markdown': render_markdown,
    'html': render_html,
    'json': render_json,
}
