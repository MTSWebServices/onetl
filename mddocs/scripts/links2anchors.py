#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""
Replace explicit Markdown links with autorefs anchor references.

Finds links of the form [Text](/some/path/) inside docstrings and replaces
them with [Text][DBR-onetl-anchor] by looking up the first { #... } anchor
in the corresponding docs MD file.

Usage:
    python links2anchors.py [--dry-run] [--path PATH] [--file FILE]
                            [--docs-dir DOCS_DIR]

Options:
    --dry-run           Print changes without writing files.
    --path PATH         Directory to process recursively (default: onetl/).
    --file FILE         Process a single file instead of a directory.
    --docs-dir DOCS_DIR Path to MkDocs docs directory
                        (default: mddocs/docs/).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Build anchor index from docs MD files
# ---------------------------------------------------------------------------

_ANCHOR_RE = re.compile(r"\{ #([^}]+) \}")


def _resolve_md_file(docs_dir: Path, url_path: str) -> Path | None:
    """Map a docs URL path like /file/file_filters/ to its MD file."""
    # Strip leading/trailing slashes, e.g. "/foo/bar/" → "foo/bar"
    rel = url_path.strip("/")
    if not rel:
        return None

    # Try <rel>.md first, then <rel>/index.md
    candidate_flat = docs_dir / (rel + ".md")
    if candidate_flat.exists():
        return candidate_flat

    candidate_index = docs_dir / rel / "index.md"
    if candidate_index.exists():
        return candidate_index

    return None


def _first_anchor(md_file: Path) -> str | None:
    """Return the first { #anchor } found in a MD file."""
    try:
        text = md_file.read_text(encoding="utf-8")
    except Exception:
        return None
    m = _ANCHOR_RE.search(text)
    return m.group(1) if m else None


def build_anchor_index(docs_dir: Path) -> dict[str, str]:
    """
    Return mapping: url_path (e.g. '/file/file_filters/') → anchor id.
    Walks all .md files and records their path-relative URL.
    """
    index: dict[str, str] = {}
    for md_file in docs_dir.rglob("*.md"):
        anchor = _first_anchor(md_file)
        if not anchor:
            continue
        rel = md_file.relative_to(docs_dir)
        parts = list(rel.parts)

        # Determine the URL path this file serves
        if parts[-1] == "index.md":
            # docs/foo/bar/index.md → /foo/bar/
            url = "/" + "/".join(parts[:-1]) + "/"
        else:
            # docs/foo/bar.md → /foo/bar/
            url = "/" + "/".join(parts[:-1] + [parts[-1][:-3]]) + "/"

        index[url] = anchor
    return index


# ---------------------------------------------------------------------------
# Transformer
# ---------------------------------------------------------------------------

# Matches [Any Text](/absolute/path/) — absolute docs links only
_LINK_RE = re.compile(r"\[([^\]]+)\]\((/[^)]*?/)\)")

# Matches [![alt](img_url)](/absolute/path/) — badge/image links
_IMAGE_LINK_RE = re.compile(r"(\[!\[[^\]]*\]\([^)]*\))\]\((/[^)]*?/)\)")


def _fix_links(text: str, anchor_index: dict[str, str]) -> tuple[str, list[str]]:
    """Replace [Text](/path/) and [![img](url)](/path/) with anchor-style refs."""
    changes: list[str] = []

    def replace(m: re.Match) -> str:
        label = m.group(1)
        path = m.group(2)
        anchor = anchor_index.get(path)
        if anchor:
            changes.append(f"link: [{label}]({path}) → [{label}][{anchor}]")
            return f"[{label}][{anchor}]"
        return m.group(0)

    def replace_image(m: re.Match) -> str:
        img_part = m.group(1)  # [![alt](img_url)]
        path = m.group(2)
        anchor = anchor_index.get(path)
        if anchor:
            changes.append(f"image-link: {img_part}({path}) → {img_part}[{anchor}]")
            return f"{img_part}[{anchor}]"
        return m.group(0)

    new_text = _IMAGE_LINK_RE.sub(replace_image, text)
    new_text = _LINK_RE.sub(replace, new_text)
    return new_text, changes


# ---------------------------------------------------------------------------
# File processor
# ---------------------------------------------------------------------------

_TRIPLE_QUOTED = re.compile(
    r'("""(?:[^"\\]|\\.|"{1,2}(?!"))*"""|'
    r"'''(?:[^'\\]|\\.|'{1,2}(?!'))*''')",
    re.DOTALL,
)


def find_docstrings(source: str) -> list[tuple[int, int]]:
    results = []
    for m in _TRIPLE_QUOTED.finditer(source):
        preceding = source[: m.start()].rstrip()
        if preceding.endswith(":") or not preceding or preceding[-1] in ("\n", "#"):
            results.append((m.start(), m.end()))
    return results


def process_file(path: Path, anchor_index: dict[str, str], dry_run: bool) -> bool:
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as e:
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
        quote = '"""' if raw.startswith('"""') else "'''"
        body = raw[3:-3]

        converted, changes = _fix_links(body, anchor_index)
        if not changes:
            continue

        new_raw = quote + converted + quote
        adj_start = start + offset
        adj_end = end + offset
        new_source = new_source[:adj_start] + new_raw + new_source[adj_end:]
        offset += len(new_raw) - len(raw)
        file_changes.extend(changes)

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
        description="Replace explicit doc links with autorefs anchor references.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing files")
    parser.add_argument("--path", default="onetl/", help="Directory to process (default: onetl/)")
    parser.add_argument("--file", help="Process a single file")
    parser.add_argument("--docs-dir", default="mddocs/docs/", help="MkDocs docs directory (default: mddocs/docs/)")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    if not docs_dir.is_dir():
        print(f"ERROR: docs-dir not found: {docs_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Building anchor index from {docs_dir}...", end=" ", flush=True)
    anchor_index = build_anchor_index(docs_dir)
    print(f"{len(anchor_index)} pages indexed.")

    mode = "dry-run" if args.dry_run else "write"

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(Path(args.path).rglob("*.py"))

    print(f"Processing {len(files)} file(s) [{mode}]...")

    changed = 0
    for f in files:
        if process_file(f, anchor_index, dry_run=args.dry_run):
            changed += 1
            if not args.dry_run:
                print(f"  ✓ {f}")

    label = "would be changed" if args.dry_run else "changed"
    print(f"\nDone: {changed}/{len(files)} files {label}.")


if __name__ == "__main__":
    main()
