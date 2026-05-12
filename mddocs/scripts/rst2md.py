# SPDX-FileCopyrightText: 2025-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""
Convert RST syntax in Python docstrings to Markdown (MkDocs / mkdocstrings).

Handles:
  - inline code:       ``code``          → `code`
  - hyperlinks:        `text <url>`_     → [text](url)
  - cross-references:  :obj:`name`       → [name][]
                       :obj:`~name`      → [shortname][]
                       :obj:`D <path>`   → [D][path]
                       :class:`...`      → same as :obj:
                       :ref:`label`      → [label][]
                       :ref:`D <label>`  → [D][label]
  - admonitions:       .. note::         → !!! note
                       .. warning::      → !!! warning
                       .. DANGER::       → !!! danger
                       .. seealso::      → !!! info "See also"
                       .. versionadded::   X → !!! success "Added in X"
                       .. versionchanged:: X → !!! info "Changed in X"
                       .. deprecated::     X → !!! warning "Deprecated since X"
                       .. note :: inline text → block form
  - code blocks:       .. code:: lang    → ```lang
                       .. code-block::   → ```lang title="..."
  - tabs:              .. tabs:: / .. code-tab:: / .. tab::  → === "..."
  - dropdown:          .. dropdown:: T   → ??? note "T"
  - substitutions:     |support_hooks|   → inline badge (shields.io)
  - ext. domain:       :etl-entities:`D <path.html>` → [D](https://etl-entities.readthedocs.io/en/stable/path.html)
  - doctest blocks:    >>> code          → ```python fenced block
  - admonition bodies: normalises indentation to 4 spaces (MkDocs requirement)

Usage:
    python rst2md.py [--dry-run] [--path PATH] [--file FILE]

Options:
    --dry-run       Print changes without writing files.
    --path PATH     Directory to process recursively (default: onetl/).
    --file FILE     Process a single file instead of a directory.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level constants for inline transformations
# ---------------------------------------------------------------------------

_EXTERNAL_PREFIXES = ("pyspark.", "os.", "datetime.", "pathlib.", "ssl.", "typing.", "contextlib.")
_BUILTIN_TYPES = {"str", "int", "float", "bool", "bytes", "None"}
_ETL_ENTITIES_BASE = "https://etl-entities.readthedocs.io/en/stable/"
_SUPPORT_HOOKS_BADGE = "[![support hooks](https://img.shields.io/badge/%20-support%20hooks-blue)](/hooks/)"


# ---------------------------------------------------------------------------
# Inline transformations (regex-based, order matters)
# ---------------------------------------------------------------------------


def _apply_inline(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []

    def sub(pattern, repl, t, desc, flags=0):
        new = re.sub(pattern, repl, t, flags=flags)
        if new != t:
            changes.append(desc)
        return new

    # 1. Inline code: ``code`` → `code`
    # Negative lookaround prevents matching ``` fenced-block markers.
    text = sub(r"(?<!`)``(?!`)(.+?)(?<!`)``(?!`)", r"`\1`", text, "inline code: ``…`` → `…`")

    # 1b. Empty inline code at end of line: ``\n → ` `\n  (empty string default in RST)
    # Must run after the main inline code pass so closing `` of pairs is already consumed.
    text = sub(r"(?<!`)``(?!`)(\s*$)", r"` `\1", text, "inline code empty: `` → ` `", re.MULTILINE)

    # 2. Hyperlinks: `Display Text <https://...>`_  → [Display Text](https://...)
    text = sub(
        r"`([^`<]+?)\s+<(https?://[^>]+)>`_",
        r"[\1](\2)",
        text,
        "hyperlink: `text <url>`_ → [text](url)",
    )

    # 3. Cross-references — most specific first

    # :obj:`~a.b.c`  →  [c][]   (tilde: show only last segment)
    def tilde_ref(m):
        last = m.group(1).split(".")[-1]
        return f"[{last}][]"

    new = re.sub(r":(?:obj|class):`~([\w.]+)`", tilde_ref, text)
    if new != text:
        changes.append("cross-ref tilde: :obj:`~name` → [shortname][]")
        text = new

    # :obj:`Display <full.path>`  →  [Display][full.path]
    text = sub(
        r":(?:obj|class):`([^`<]+?)\s+<([^>`]+)>`",
        r"[\1][\2]",
        text,
        "cross-ref display: :obj:`D <path>` → [D][path]",
    )

    # :obj:`name`  →  `name` for external types, [name][] for internal
    _seen_external = False
    _seen_internal = False

    def _obj_or_code(m):
        nonlocal _seen_external, _seen_internal
        name = m.group(1)
        if any(name.startswith(p) for p in _EXTERNAL_PREFIXES) or name in _BUILTIN_TYPES:
            _seen_external = True
            return f"`{name}`"
        _seen_internal = True
        return f"[{name}][]"

    text = re.sub(r":(?:obj|class):`([\w.]+)`", _obj_or_code, text)
    if _seen_external:
        changes.append("cross-ref external: :obj:`name` → `name`")
    if _seen_internal:
        changes.append("cross-ref: :obj:`name` → [name][]")

    # :ref:`Display <label>`  →  [Display][label]
    text = sub(r":ref:`([^`<]+?)\s+<([^>`]+)>`", r"[\1][\2]", text, "ref display: :ref:`D <l>` → [D][l]")

    # :ref:`label`  →  [label][]
    text = sub(r":ref:`([\w.-]+)`", r"[\1][]", text, "ref: :ref:`label` → [label][]")

    # 4. External Sphinx domain :etl-entities: → plain Markdown link
    # Configured in docs/conf.py as intersphinx alias with base URL:
    #   https://etl-entities.readthedocs.io/en/stable/%s
    # Pattern: :etl-entities:`Display <path.html>`  →  [Display](base/path.html)
    def _etl_entities_link(m):
        display, path = m.group(1).strip(), m.group(2).strip()
        return f"[{display}]({_ETL_ENTITIES_BASE}{path})"

    new = re.sub(r":etl-entities:`([^`<]+?)\s+<([^>`]+)>`", _etl_entities_link, text)
    if new != text:
        changes.append("etl-entities: :etl-entities:`D <path>` → [D](url)")
        text = new

    # 5. RST substitutions → inline badge
    # |support_hooks| is defined in docs/conf.py as a shields.io badge image.
    # Inlined directly because mkdocstrings renders docstrings independently
    # of the mkdocs-macros plugin, so {{ support_hooks }} would not be expanded.
    text = sub(
        r"\|support_hooks\|",
        _SUPPORT_HOOKS_BADGE,
        text,
        "substitution: |support_hooks| → badge",
    )

    return text, changes


# ---------------------------------------------------------------------------
# Code block conversion
# ---------------------------------------------------------------------------


def _convert_code_blocks(lines: list[str]) -> tuple[list[str], list[str]]:
    """Replace .. code[(-block)]:: directives with fenced Markdown blocks."""
    changes: list[str] = []
    result: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\s*)\.\. code(?:-block)?::\s*(\w*).*$", line)
        if not m:
            result.append(line)
            i += 1
            continue

        indent = m.group(1)
        lang = m.group(2) or ""
        i += 1

        # Collect directive options (:caption:, :linenos:, etc.)
        title = ""
        while i < len(lines) and re.match(r"^\s+:\w", lines[i]):
            cap = re.match(r"\s*:caption:\s*(.+)", lines[i])
            if cap:
                title = cap.group(1).strip()
            i += 1

        # Skip single blank line separating options from body
        if i < len(lines) and lines[i].strip() == "":
            i += 1

        # Collect body: lines indented more than the directive itself
        min_body_indent = len(indent) + 4
        body: list[str] = []
        while i < len(lines):
            cl = lines[i]
            stripped = cl.lstrip()
            current_indent = len(cl) - len(stripped)
            if stripped == "" and cl and len(cl) < min_body_indent:
                # Whitespace-only line with less indent than body — trailing
                # indentation before closing """, not part of this block.
                break
            if stripped == "":
                body.append("")
                i += 1
            elif current_indent >= min_body_indent:
                body.append(cl[min_body_indent:])
                i += 1
            else:
                break

        # Strip trailing blank lines from body
        while body and body[-1] == "":
            body.pop()

        title_part = f' title="{title}"' if title else ""
        result.append(f"{indent}```{lang}{title_part}")
        result.extend(f"{indent}{bl}" for bl in body)
        result.append(f"{indent}```")
        changes.append(f"code block: .. code:: {lang} → ```{lang}{title_part}")

    return result, changes


# ---------------------------------------------------------------------------
# Tabs conversion
# ---------------------------------------------------------------------------


def _convert_tabs(lines: list[str]) -> tuple[list[str], list[str]]:
    """Replace sphinx-tabs directives with pymdownx.tabbed syntax."""
    changes: list[str] = []
    result: list[str] = []
    i = 0
    tabs_indent = ""  # indent of the enclosing .. tabs:: directive

    while i < len(lines):
        line = lines[i]

        # Remove .. tabs:: wrapper, remember its indent
        m_tabs = re.match(r"^(\s*)\.\. tabs::\s*$", line)
        if m_tabs:
            tabs_indent = m_tabs.group(1)
            changes.append("removed: .. tabs::")
            i += 1
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            continue

        # .. code-tab:: py Title  →  === "Title" + fenced code block
        m = re.match(r"^(\s*)\.\. code-tab::\s+\w+\s+(.+)$", line)
        if m:
            indent, title = m.group(1), m.group(2).strip()
            # Strip the tabs directive indent so === aligns with surrounding text
            out_indent = indent[len(tabs_indent) :]
            result.append(f'{out_indent}=== "{title}"')
            changes.append(f'code-tab: .. code-tab:: → === "{title}"')
            i += 1
            if i < len(lines) and lines[i].strip() == "":
                i += 1

            # Collect body
            min_body = len(indent) + 4
            body: list[str] = []
            while i < len(lines):
                cl = lines[i]
                stripped = cl.lstrip()
                if stripped == "" and cl and len(cl) < min_body:
                    # Whitespace-only line with less indent than body — trailing
                    # indentation before closing """, not part of this block.
                    break
                if stripped == "":
                    body.append("")
                    i += 1
                elif len(cl) - len(stripped) >= min_body:
                    body.append(cl[min_body:])
                    i += 1
                else:
                    break
            while body and body[-1] == "":
                body.pop()

            result.append(f"{out_indent}    ```python")
            result.extend(f"{out_indent}    {bl}" for bl in body)
            result.append(f"{out_indent}    ```")
            continue

        # .. tab:: Title  →  === "Title"
        m = re.match(r"^(\s*)\.\. tab::\s+(.+)$", line)
        if m:
            indent, title = m.group(1), m.group(2).strip()
            out_indent = indent[len(tabs_indent) :]
            result.append(f'{out_indent}=== "{title}"')
            changes.append(f'tab: .. tab:: → === "{title}"')
            i += 1
            continue

        result.append(line)
        i += 1

    return result, changes


# ---------------------------------------------------------------------------
# Admonitions
# ---------------------------------------------------------------------------

_SIMPLE_ADMONITIONS = {
    "note": "note",
    "warning": "warning",
    "danger": "danger",
    "DANGER": "danger",
    "seealso": 'info "See also"',
    "important": "important",
    "tip": "tip",
}


def _collect_admonition_body(
    lines: list[str],
    i: int,
    directive_indent: str,
) -> tuple[list[str], int]:
    """Consume body lines of an admonition, normalising indentation to directive_indent + 4 spaces.

    Preserves relative indentation within the body (e.g. nested code blocks).
    Returns (normalised_body_lines, updated_line_index).
    """
    expected_indent = len(directive_indent) + 4

    # Collect raw body lines first
    raw: list[str] = []
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if stripped == "" or len(line) - len(stripped) > len(directive_indent):
            raw.append(line)
            i += 1
        else:
            break

    # Find the base indentation (minimum indent among non-blank lines)
    body_base: int | None = None
    for line in raw:
        stripped = line.lstrip()
        if stripped:
            indent = len(line) - len(stripped)
            if body_base is None or indent < body_base:
                body_base = indent

    if body_base is None:
        return raw, i

    # Re-emit with normalised indentation, preserving relative depth
    normalised: list[str] = []
    for line in raw:
        stripped = line.lstrip()
        if not stripped:
            normalised.append(line)  # blank/whitespace-only — preserve as-is
        else:
            relative = len(line) - len(stripped) - body_base
            normalised.append(" " * (expected_indent + relative) + stripped)

    return normalised, i


def _convert_admonitions(lines: list[str]) -> tuple[list[str], list[str]]:
    changes: list[str] = []
    result: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Inline admonition: .. note :: Some text  →  !!! note\n    Some text
        m = re.match(r"^(\s*)\.\.\s+(\w+) ::\s+(.+)$", line)
        if m:
            indent, kind, body_text = m.group(1), m.group(2).lower(), m.group(3)
            result.append(f"{indent}!!! {kind}")
            result.append(f"{indent}    {body_text}")
            changes.append(f"inline admonition: .. {kind} :: text → block form")
            i += 1
            continue

        # Version admonitions with text on the same line (more specific — check first)
        m = re.match(
            r"^(\s*)\.\.\s+(versionadded|versionchanged|deprecated)::\s*([\d.]+)\s+(.+)$",
            line,
        )
        if m:
            indent, kind, ver, text = m.group(1), m.group(2), m.group(3), m.group(4)
            mapping = {
                "versionadded": f'success "Added in {ver}"',
                "versionchanged": f'info "Changed in {ver}"',
                "deprecated": f'warning "Deprecated since {ver}"',
            }
            md_type = mapping[kind]
            result.append(f"{indent}!!! {md_type}")
            result.append(f"{indent}    {text}")
            changes.append(f"{kind}: .. {kind}:: {ver} text → !!! {md_type}")
            i += 1
            body, i = _collect_admonition_body(lines, i, indent)
            body, ch = _convert_admonitions(body)
            result.extend(body)
            changes.extend(ch)
            continue

        # Version admonitions (no inline text)
        m = re.match(
            r"^(\s*)\.\.\s+(versionadded|versionchanged|deprecated)::\s*([\d.]+)\s*$",
            line,
        )
        if m:
            indent, kind, ver = m.group(1), m.group(2), m.group(3)
            mapping = {
                "versionadded": f'success "Added in {ver}"',
                "versionchanged": f'info "Changed in {ver}"',
                "deprecated": f'warning "Deprecated since {ver}"',
            }
            md_type = mapping[kind]
            result.append(f"{indent}!!! {md_type}")
            changes.append(f"{kind}: .. {kind}:: {ver} → !!! {md_type}")
            i += 1
            body, i = _collect_admonition_body(lines, i, indent)
            body, ch = _convert_admonitions(body)
            result.extend(body)
            changes.extend(ch)
            continue

        # Dropdown
        m = re.match(r"^(\s*)\.\.\s+dropdown::\s+(.+)$", line)
        if m:
            indent, title = m.group(1), m.group(2).strip()
            result.append(f'{indent}??? note "{title}"')
            changes.append(f'dropdown: .. dropdown:: → ??? note "{title}"')
            i += 1
            body, i = _collect_admonition_body(lines, i, indent)
            body, ch = _convert_admonitions(body)
            result.extend(body)
            changes.extend(ch)
            continue

        # Simple admonitions
        matched = False
        for rst_kind, md_kind in _SIMPLE_ADMONITIONS.items():
            m = re.match(rf"^(\s*)\.\.\s+{re.escape(rst_kind)}\s*::(\s*)$", line)
            if m:
                indent = m.group(1)
                result.append(f"{indent}!!! {md_kind}")
                changes.append(f"admonition: .. {rst_kind}:: → !!! {md_kind}")
                matched = True
                i += 1
                body, i = _collect_admonition_body(lines, i, indent)
                body, ch = _convert_admonitions(body)
                result.extend(body)
                changes.extend(ch)
                break

        if not matched:
            result.append(line)
            i += 1

    return result, changes


# ---------------------------------------------------------------------------
# Doctest blocks
# ---------------------------------------------------------------------------


def _convert_doctests(lines: list[str]) -> tuple[list[str], list[str]]:
    """Wrap standalone >>> doctest blocks in ```python fenced code blocks.

    Only acts outside already-fenced code blocks.
    """
    changes: list[str] = []
    result: list[str] = []
    i = 0
    in_fence = False

    while i < len(lines):
        line = lines[i]

        # Track fenced code blocks
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
            result.append(line)
            i += 1
            continue

        # Detect start of a doctest block outside a fenced block
        m = re.match(r"^(\s*)>>>", line)
        if m and not in_fence:
            indent = m.group(1)
            # Collect all non-blank lines as the doctest block
            block: list[str] = []
            while i < len(lines) and lines[i].strip() != "":
                block.append(lines[i])
                i += 1
            result.append(f"{indent}```python")
            result.extend(block)
            result.append(f"{indent}```")
            changes.append("doctest: >>> block → ```python fenced block")
            continue

        result.append(line)
        i += 1

    return result, changes


# ---------------------------------------------------------------------------
# Top-level converter
# ---------------------------------------------------------------------------


def convert_docstring(body: str) -> tuple[str, list[str]]:
    """Convert RST markup inside a docstring body to Markdown."""
    all_changes: list[str] = []

    # Line-based passes
    lines = body.split("\n")
    lines, ch = _convert_code_blocks(lines)
    all_changes.extend(ch)
    lines, ch = _convert_tabs(lines)
    all_changes.extend(ch)
    lines, ch = _convert_admonitions(lines)
    all_changes.extend(ch)
    lines, ch = _convert_doctests(lines)
    all_changes.extend(ch)
    text = "\n".join(lines)

    # Inline passes (regex over full text)
    text, ch = _apply_inline(text)
    all_changes.extend(ch)

    return text, all_changes


# ---------------------------------------------------------------------------
# Docstring finder
# ---------------------------------------------------------------------------

# Matches single-line single-quoted string literals used as member docstrings
# (e.g. enum member descriptions).  Only " variant — ' is rare in this codebase.
_SINGLE_QUOTED_DOCSTR = re.compile(r'"([^"\\\n]+)"')

# Matches both """ and ''' triple-quoted strings (with optional r/b/f/u prefix),
# including escaped quotes inside.
_TRIPLE_QUOTED = re.compile(
    r'([rRbBuUfF]?"""(?:[^"\\]|\\.|"{1,2}(?!"))*"""|'
    r"[rRbBuUfF]?'''(?:[^'\\]|\\.|'{1,2}(?!'))*''')",
    re.DOTALL,
)

# Only treat a triple-quoted string as a docstring if it follows:
#   - start of file / after a decorator / after class or def statement
_DOCSTRING_CONTEXT = re.compile(
    r"(?:^|(?:class|def)\s[^\n]*:\s*\n\s*|@\w[^\n]*\n\s*)",
    re.MULTILINE,
)


def find_docstrings(source: str) -> list[tuple[int, int]]:
    """Return (start, end) positions of all docstrings in *source*."""
    results = []
    for m in _TRIPLE_QUOTED.finditer(source):
        # Check that what precedes the match looks like a docstring context.
        preceding = source[: m.start()].rstrip()
        # Strip trailing inline comment (e.g. a ruff/flake8 suppression) before checking.
        preceding_no_comment = re.sub(r"\s*#[^\n]*$", "", preceding)
        # Heuristic: last non-whitespace char is ':', or the string is at
        # module level (start of file or after a blank/comment line).
        if preceding_no_comment.endswith(":") or not preceding or preceding[-1] in ("\n", "#"):
            results.append((m.start(), m.end()))
            continue
        # Also catch field docstrings: triple-quoted string on its own line
        # immediately after a field assignment (with or without Field(...)).
        # e.g.:  field: Type = Field(...)\n    """description"""
        #        field: Type = SomeDefault\n    """description"""
        #        field: Type = Field(\n            ...\n        )\n    """description"""
        last_line = preceding_no_comment.rsplit("\n", 1)[-1].rstrip()
        if (
            last_line.endswith(")")  # closing ) of Field(...)
            or (
                re.match(r"^\s*[\w\]]+\s*[=:]", last_line) and "=" in last_line
            )  # assignment (simple or after Literal[])
        ):
            results.append((m.start(), m.end()))
    return results


# ---------------------------------------------------------------------------
# File processor
# ---------------------------------------------------------------------------


def process_file(path: Path, *, dry_run: bool) -> bool:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  ERROR reading {path}: {e}", file=sys.stderr)
        return False

    docstrings = find_docstrings(source)
    if not docstrings:
        return False

    offset = 0
    new_source = source
    file_changes: list[str] = []

    for start, end in docstrings:
        raw = source[start:end]

        # Handle optional string prefix (r, b, f, u, etc.)
        prefix_m = re.match(r'^([rRbBuUfF]?)("""|\'\'\')', raw)
        prefix = prefix_m.group(1)
        quote = prefix_m.group(2)
        q_len = len(prefix) + len(quote)

        body = raw[q_len : -len(quote)]
        converted, changes = convert_docstring(body)

        if not changes:
            continue

        new_raw = prefix + quote + converted + quote
        adj_start = start + offset
        adj_end = end + offset
        new_source = new_source[:adj_start] + new_raw + new_source[adj_end:]
        offset += len(new_raw) - len(raw)
        file_changes.extend(changes)

    # Second pass: single-line member docstrings (e.g. enum member descriptions)
    # that contain RST inline patterns.  Only _apply_inline is needed here.
    lines = new_source.splitlines(keepends=True)
    new_lines = []
    for idx, line in enumerate(lines):
        # A member docstring is a line consisting only of a single-quoted string,
        # immediately preceded by an assignment line (e.g. MEMBER = value).
        m = re.match(r'^(\s*)"([^"\\\n]+)"(\s*)$', line)
        if m and idx > 0:
            prev = lines[idx - 1].rstrip()
            prev_no_comment = re.sub(r"\s*#[^\n]*$", "", prev)
            if re.match(r"^\s*[\w\]]+\s*=", prev_no_comment):
                body = m.group(2)
                converted, changes = _apply_inline(body)
                if changes:
                    new_line = f'{m.group(1)}"{converted}"{m.group(3)}'
                    file_changes.extend(changes)
                    new_lines.append(new_line)
                    continue
        new_lines.append(line)
    new_source = "".join(new_lines)

    if not file_changes:
        return False

    if dry_run:
        print(f"\n  {path}")
        seen = set()
        for c in file_changes:
            if c not in seen:
                print(f"    · {c}")
                seen.add(c)
    else:
        path.write_text(new_source, encoding="utf-8")

    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert RST docstrings to Markdown for MkDocs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing files")
    parser.add_argument("--path", default="onetl/", help="Directory to process (default: onetl/)")
    parser.add_argument("--file", help="Process a single file")
    args = parser.parse_args()

    mode = "dry-run" if args.dry_run else "write"

    files = [Path(args.file)] if args.file else sorted(Path(args.path).rglob("*.py"))

    print(f"Processing {len(files)} file(s) [{mode}]...")

    changed = 0
    for f in files:
        if process_file(f, dry_run=args.dry_run):
            changed += 1
            if not args.dry_run:
                print(f"  ✓ {f}")

    label = "would be changed" if args.dry_run else "changed"
    print(f"\nDone: {changed}/{len(files)} files {label}.")


if __name__ == "__main__":
    main()
