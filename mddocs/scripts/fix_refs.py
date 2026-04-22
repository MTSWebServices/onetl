# SPDX-FileCopyrightText: 2025-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
"""
Fix unresolved doc-anchor references in converted docstrings.

Replaces two kinds of unresolved cross-references:
  1. [label][]  — converted from RST :ref:, resolved via REF_MAP
  2. [text][onetl.module.ClassName]  — Python-path refs that autorefs cannot
     resolve (because show_root_heading: false suppresses anchor generation),
     resolved via PYTHON_PATH_MAP

Both mapping tables are the single source of truth. Update them when doc pages
are renamed, reorganised, or when new unresolved references appear.

Usage:
    python fix_refs.py [--dry-run] [--path PATH] [--file FILE] [--docs-path PATH]

Options:
    --dry-run        Print changes without writing files.
    --path PATH      Directory to process recursively (default: onetl/).
    --file FILE      Process a single file instead of a directory.
    --docs-path PATH Also fix broken links in docs .md files under PATH.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Mapping: RST :ref: label → (link text, absolute docs path)
#
# Paths are absolute from the docs root (as served by MkDocs).
# Update this table when doc pages are renamed or reorganised.
# ---------------------------------------------------------------------------

REF_MAP: dict[str, tuple[str, str]] = {
    # Core classes
    "db-reader": ("DB Reader", "/db/reader/"),
    "file-downloader": ("File Downloader", "/file/file_downloader/"),
    "file-uploader": ("File Uploader", "/file/file_uploader/"),
    "file-mover": ("File Mover", "/file/file_mover/"),
    # Strategies
    "strategy": ("Read Strategies", "/strategy/"),
    # Connections
    "db-connections": ("DB Connections", "/connection/db_connection/"),
    "file-connections": ("File Connections", "/connection/file_connection/"),
    "file-df-connections": ("File DF Connections", "/connection/file_df_connection/"),
    # File utilities
    "file-filters": ("File Filters", "/file/file_filters/"),
    "file-limits": ("File Limits", "/file/file_limits/"),
    # HWM
    "hwm": ("HWM", "/hwm_store/"),
    # Hooks
    "hooks-design": ("Hooks design", "/hooks/design/"),
    "slot-decorator": ("@slot decorator", "/hooks/slot/"),
    "slot": ("@slot", "/hooks/slot/"),
    # Installation
    "install-files": ("File connections install", "/install/files/"),
    "install-spark": ("Spark install", "/install/spark/"),
    "install-kerberos": ("Kerberos support", "/install/kerberos/"),
    # Prerequisites per connector
    "kafka-prerequisites": ("Kafka prerequisites", "/connection/db_connection/kafka/prerequisites/"),
    "clickhouse-prerequisites": ("Clickhouse prerequisites", "/connection/db_connection/clickhouse/prerequisites/"),
    "greenplum-prerequisites": ("Greenplum prerequisites", "/connection/db_connection/greenplum/prerequisites/"),
    "hive-prerequisites": ("Hive prerequisites", "/connection/db_connection/hive/prerequisites/"),
    "iceberg-prerequisites": ("Iceberg prerequisites", "/connection/db_connection/iceberg/prerequisites/"),
    "mongodb-prerequisites": ("MongoDB prerequisites", "/connection/db_connection/mongodb/prerequisites/"),
    "mssql-prerequisites": ("MSSQL prerequisites", "/connection/db_connection/mssql/prerequisites/"),
    "mysql-prerequisites": ("MySQL prerequisites", "/connection/db_connection/mysql/prerequisites/"),
    "oracle-prerequisites": ("Oracle prerequisites", "/connection/db_connection/oracle/prerequisites/"),
    "postgres-prerequisites": ("Postgres prerequisites", "/connection/db_connection/postgres/prerequisites/"),
    "spark-hdfs-prerequisites": (
        "Spark HDFS prerequisites",
        "/connection/file_df_connection/spark_hdfs/prerequisites/",
    ),
    "spark-s3-prerequisites": ("Spark S3 prerequisites", "/connection/file_df_connection/spark_s3/prerequisites/"),
    # Slots
    "hdfs-slots": ("HDFS Slots", "/connection/file_connection/hdfs/slots/"),
    "spark-hdfs-slots": ("Spark HDFS Slots", "/connection/file_df_connection/spark_hdfs/slots/"),
    # Other
    "kafka": ("Kafka", "/connection/db_connection/kafka/"),
}


# ---------------------------------------------------------------------------
# Mapping: Python dotted path → absolute docs URL (with anchor)
#
# Used for [text][onetl.module.ClassName] cross-references that autorefs
# cannot resolve because show_root_heading: false suppresses anchor generation
# for documented root objects.
# ---------------------------------------------------------------------------

PYTHON_PATH_MAP: dict[str, str] = {
    # Strategies
    "onetl.strategy.incremental_strategy.IncrementalStrategy": "/strategy/incremental_strategy/#DBR-onetl-strategy-incremental-strategy",
    "onetl.strategy.snapshot_strategy.SnapshotStrategy": "/strategy/snapshot_strategy/#DBR-onetl-strategy-snapshot-strategy",
    "onetl.strategy.snapshot_strategy.SnapshotBatchStrategy": "/strategy/snapshot_batch_strategy/#DBR-onetl-strategy-snapshot-batch-strategy",
    # DB
    "onetl.db.db_reader.db_reader.DBReader": "/db/reader/#DBR-onetl-db-reader",
    "onetl.connection.file_connection.hdfs.connection.HDFS": "/connection/file_connection/hdfs/connection/#DBR-onetl-connection-file-connection-hdfs-connection-0",
    "onetl.connection.file_connection.s3.S3": "/connection/file_connection/s3/#DBR-onetl-connection-file-connection-s3-connection",
    # File downloader
    "onetl.file.file_downloader.file_downloader.FileDownloader": "/file/file_downloader/file_downloader/#DBR-onetl-file-downloader-0",
    "onetl.file.file_downloader.options.FileDownloaderOptions": "/file/file_downloader/options/#DBR-onetl-file-downloader-options",
    "onetl.file.file_downloader.file_downloader.FileDownloader.Options.delete_source": "/file/file_downloader/options/#onetl.file.file_downloader.options.FileDownloaderOptions.delete_source",
    "onetl.file.file_downloader.file_downloader.FileDownloader.Options.mode": "/file/file_downloader/options/#DBR-onetl-file-downloader-options",
    # File mover / uploader
    "onetl.file.file_mover.options.FileMoverOptions": "/file/file_mover/options/#DBR-onetl-file-mover-options",
    "onetl.file.file_uploader.options.FileUploaderOptions": "/file/file_uploader/options/#DBR-onetl-file-uploader-options",
    # File DF
    "onetl.file.file_df_reader.file_df_reader.FileDFReader": "/file_df/file_df_reader/file_df_reader/#DBR-onetl-file-df-reader-filedf-reader-0",
    "onetl.file.file_df_writer.file_df_writer.FileDFWriter": "/file_df/file_df_writer/file_df_writer/#DBR-onetl-file-df-writer-filedf-writer-0",
    # Filters
    "onetl.file.filter.exclude_dir.ExcludeDir": "/file/file_filters/exclude_dir/#DBR-onetl-file-filters-exclude-dir-excludedir",
    "onetl.file.filter.glob.Glob": "/file/file_filters/glob/#DBR-onetl-file-filters-glob",
    "onetl.file.filter.regexp.Regexp": "/file/file_filters/regexp/#DBR-onetl-file-filters-regexp",
    # Formats
    "onetl.file.format.jsonline.JSONLine": "/file_df/file_formats/jsonline/#DBR-onetl-file-df-file-formats-jsonline",
    # Limits
    "onetl.file.limit.max_files_count.MaxFilesCount": "/file/file_limits/max_files_count/#DBR-onetl-file-limits-max-files-count-maxfilescount",
    # Postgres options (wrong python path used in docstrings → correct anchor)
    "onetl.connection.db_connection.postgres.Postgres.ReadOptions.fetchsize": "/connection/db_connection/postgres/read/#onetl.connection.db_connection.postgres.options.PostgresReadOptions.fetchsize",
}


# ---------------------------------------------------------------------------
# Mapping: short class name label → absolute docs URL with anchor
#
# Used for [text][ShortClassName] cross-references where the label is a plain
# class name (not a full onetl.* path and not a kebab-case REF_MAP key).
# ---------------------------------------------------------------------------

LABEL_MAP: dict[str, str] = {
    "MongoDBReadOptions": "/connection/db_connection/mongodb/read/#onetl.connection.db_connection.mongodb.options.MongoDBReadOptions",
}


# ---------------------------------------------------------------------------
# Mapping: Python dotted path → (display text, DBR anchor label)
#
# Used for [onetl.path][] cross-references where the target is documented
# via a { #DBR-... } anchor (not a mkdocstrings ::: directive).
# Output format: [display text][DBR-anchor]
# ---------------------------------------------------------------------------

ANCHOR_REF_MAP: dict[str, tuple[str, str]] = {
    # Python path → (display text, DBR anchor)
    # Use for [onetl.path][] refs where target is a { #DBR-... } anchor in .md files.
    # NOTE: do NOT use for NumPy parameter type fields — griffe parses them as
    # Python expressions and mangles [text][anchor] into subscript with spaces.
}


# ---------------------------------------------------------------------------
# Mapping: Python dotted path → inline code name
#
# Used for [onetl.path][] cross-references where the target is NOT documented
# and cannot be linked. Output: `ClassName` (inline code, no link).
# ---------------------------------------------------------------------------

CODE_PATH_MAP: dict[str, str] = {
    # Exceptions — keep full dotted path (used in Raises sections)
    "onetl.exception.DirectoryNotFoundError": "onetl.exception.DirectoryNotFoundError",
    "onetl.exception.DirectoryNotEmptyError": "onetl.exception.DirectoryNotEmptyError",
    "onetl.exception.NotAFileError": "onetl.exception.NotAFileError",
    "onetl.exception.FileSizeMismatchError": "onetl.exception.FileSizeMismatchError",
    "onetl.exception.NoDataError": "onetl.exception.NoDataError",
    # Hooks — methods without their own anchor in generated docs
    "onetl.hooks.slot.Slot.bind": "Slot.bind",
    # Interface/abstract types — keep full path (used as type annotations)
    "onetl.hooks.hook.HookPriority": "onetl.hooks.hook.HookPriority",
    "onetl.connection.BaseDBConnection": "onetl.connection.BaseDBConnection",
    "onetl.connection.DBConnection": "onetl.connection.DBConnection",
    "onetl.connection.BaseDBConnection.ReadOptions": "onetl.connection.BaseDBConnection.ReadOptions",
    "onetl.connection.BaseDBConnection.WriteOptions": "onetl.connection.BaseDBConnection.WriteOptions",
    # Protocol/option types — use short name
    "onetl.base.PathWithStatsProtocol": "PathWithStatsProtocol",
    "onetl.base.path_protocol.PathProtocol": "PathProtocol",
    "onetl.base.base_file_filter.BaseFileFilter": "BaseFileFilter",
    "onetl.base.base_file_limit.BaseFileLimit": "BaseFileLimit",
}


# ---------------------------------------------------------------------------
# Mapping: Python dotted path (wrong/legacy) → plain name
#
# Used for [text][onetl.path] where the path is incorrect or the target
# should be rendered as a plain ExprName (let griffe/autorefs resolve it).
# Output: just the name, no brackets.
# ---------------------------------------------------------------------------

PLAIN_REF_MAP: dict[str, str] = {
    # Wrong path in docstring → plain name (griffe resolves ExprName via canonical path)
    "onetl.file.file_downloader.download_result.DownloadResult": "DownloadResult",
    # Base types — griffe resolves these via canonical path
    "onetl.base.base_file_df_connection.BaseFileDFConnection": "BaseFileDFConnection",
    "onetl.base.base_file_format.BaseReadableFileFormat": "BaseReadableFileFormat",
    "onetl.base.base_file_format.BaseWritableFileFormat": "BaseWritableFileFormat",
    "onetl.base.base_file_filter.BaseFileFilter": "BaseFileFilter",
    "onetl.base.base_file_limit.BaseFileLimit": "BaseFileLimit",
    "onetl.base.path_protocol.PathProtocol": "PathProtocol",
    # Options/result types
    "onetl.file.file_df_reader.options.FileDFReaderOptions": "FileDFReaderOptions",
    "onetl.file.file_df_writer.options.FileDFWriterOptions": "FileDFWriterOptions",
    "onetl.file.file_mover.move_result.MoveResult": "MoveResult",
    "onetl.file.file_uploader.upload_result.UploadResult": "UploadResult",
    # Connection types where display text differs from last path component
    "onetl.connection.db_connection.kafka.kafka_plaintext_protocol.KafkaPlaintextProtocol": "KafkaPlaintextProtocol",
    "onetl.connection.db_connection.kafka.connection.Kafka": "Kafka",
}


# ---------------------------------------------------------------------------
# Mapping: short [Name][] refs not in onetl.* namespace
#
# Used for [Name][] where Name is a simple identifier or dotted non-onetl path.
# Values wrapped in backticks become inline code; plain strings become plain text.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Mapping: broken relative links in docs .md files → correct replacement
#
# Used for links that cannot be resolved by MkDocs because the target file
# is outside the docs/ directory (e.g. pyproject.toml in the repo root).
# ---------------------------------------------------------------------------

DOCS_BROKEN_LINKS: dict[str, str] = {
    "../../pyproject.toml": "https://github.com/MTSWebServices/onetl/blob/develop/pyproject.toml",
}


SHORTNAME_MAP: dict[str, str] = {
    # Method refs in body text → inline code
    "execute": "`execute`",
    "check": "`check`",
    "sql": "`sql`",
    "HDFS": "`HDFS`",
    "HWM": "[HWM](/hwm_store/)",
    # Connection class refs
    "SparkHDFS": "[SparkHDFS](/connection/file_df_connection/spark_hdfs/connection/#DBR-onetl-connection-file-df-connection-spark-hdfs-connection)",
    # Field refs that have no anchor in generated docs → inline code
    "escape": "`escape`",
    # Hook slot methods → links to docs pages
    "skip_hooks": "[skip_hooks](/hooks/support_hooks/#onetl.hooks.support_hooks.skip_hooks)",
    "suspend_hooks": "[suspend_hooks](/hooks/support_hooks/#onetl.hooks.support_hooks.suspend_hooks)",
    "resume_hooks": "[resume_hooks](/hooks/support_hooks/#onetl.hooks.support_hooks.resume_hooks)",
    "stop_all_hooks": "[stop_all_hooks](/hooks/global_state/#onetl.hooks.hooks_state.stop_all_hooks)",
    "resume_all_hooks": "[resume_all_hooks](/hooks/global_state/#onetl.hooks.hooks_state.resume_all_hooks)",
    # Type refs in parameter type fields → plain name (mkdocstrings resolves them)
    "IcebergCatalog": "IcebergCatalog",
    "IcebergWarehouse": "IcebergWarehouse",
    "Options": "Options",
    "re.Pattern": "re.Pattern",
}


# ---------------------------------------------------------------------------
# Transformer
# ---------------------------------------------------------------------------


def _fix_refs(text: str) -> tuple[str, list[str]]:  # noqa: C901, PLR0915
    """Replace [label][] and [text][onetl.*] with explicit Markdown links."""
    changes: list[str] = []

    def replace_ref(m: re.Match) -> str:
        label = m.group(1)
        if label in REF_MAP:
            link_text, path = REF_MAP[label]
            changes.append(f"ref: [{label}][] → [{link_text}]({path})")
            return f"[{link_text}]({path})"
        return m.group(0)

    def replace_text_ref(m: re.Match) -> str:
        link_text, label = m.group(1), m.group(2)
        if label in REF_MAP:
            _, path = REF_MAP[label]
            changes.append(f"ref: [{link_text}][{label}] → [{link_text}]({path})")
            return f"[{link_text}]({path})"
        return m.group(0)

    def replace_label_ref(m: re.Match) -> str:
        link_text, label = m.group(1), m.group(2)
        if label in LABEL_MAP:
            url = LABEL_MAP[label]
            changes.append(f"label: [{link_text}][{label}] → [{link_text}]({url})")
            return f"[{link_text}]({url})"
        return m.group(0)

    def replace_python_path(m: re.Match) -> str:
        link_text, python_path = m.group(1), m.group(2)
        if python_path in PLAIN_REF_MAP:
            name = PLAIN_REF_MAP[python_path]
            changes.append(f"pyref: [{link_text}][{python_path}] → {name}")
            return name
        if python_path in PYTHON_PATH_MAP:
            url = PYTHON_PATH_MAP[python_path]
            changes.append(f"pyref: [{link_text}][{python_path}] → [{link_text}]({url})")
            return f"[{link_text}]({url})"
        return m.group(0)

    def replace_python_path_self(m: re.Match) -> str:
        """Handle [onetl.module.ClassName][] where the path is also the display text."""
        python_path = m.group(1)
        if python_path in CODE_PATH_MAP:
            name = CODE_PATH_MAP[python_path]
            changes.append(f"pyref: [{python_path}][] → {name}")
            return name
        if python_path in ANCHOR_REF_MAP:
            link_text, anchor = ANCHOR_REF_MAP[python_path]
            changes.append(f"pyref: [{python_path}][] → [{link_text}][{anchor}]")
            return f"[{link_text}][{anchor}]"
        if python_path in PYTHON_PATH_MAP:
            url = PYTHON_PATH_MAP[python_path]
            # Use the last component (ClassName) as display text
            link_text = python_path.rsplit(".", 1)[-1]
            changes.append(f"pyref: [{python_path}][] → [{link_text}]({url})")
            return f"[{link_text}]({url})"
        return m.group(0)

    def replace_shortname(m: re.Match) -> str:
        name = m.group(1)
        if name in SHORTNAME_MAP:
            changes.append(f"shortname: [{name}][] → {SHORTNAME_MAP[name]}")
            return SHORTNAME_MAP[name]
        return m.group(0)

    def fix_numpy_type(m: re.Match) -> str:
        """Remove RST-style backticks from NumPy parameter type fields."""
        prefix, type_str = m.group(1), m.group(2)
        # `T` or `T2` → T | T2  (both sides backticked)
        fixed = re.sub(r"`([^`]+)`\s+or\s+`([^`]+)`", r"\1 | \2", type_str)
        # remaining `T` → T  (covers single types and default values)
        fixed = re.sub(r"`([^`]+)`", r"\1", fixed)
        # T or T2 → T | T2  (residual after backtick removal, or pre-existing)
        fixed = re.sub(r"(\S)\s+or\s+(\S)", r"\1 | \2", fixed)
        # list/Iterable of X → list[X] / Iterable[X]
        fixed = re.sub(
            r"\b(list|List|Iterable) of ([^\s,]+)", lambda mm: f"{mm.group(1).lower()}[{mm.group(2)}]", fixed
        )
        # typing.X → X  (griffe cannot parse fully-qualified typing module refs)
        fixed = re.sub(r"\btyping\.(\w+)", r"\1", fixed)
        if fixed != type_str:
            changes.append(f"type: {type_str!r} → {fixed!r}")
            return prefix + fixed
        return m.group(0)

    def fix_see_list(m: re.Match) -> str:
        """Ensure blank line between 'See:' and the following bullet list.

        Handles two cases:
          1. Items over-indented by 4 spaces (RST style) → normalize to See: indent.
          2. No blank line before items → add one.
        """
        see_indent = m.group(1)  # indentation of 'See:'
        item_indent = m.group(2)  # indentation of first '*'
        rest = m.group(3)  # everything from '*' to end of list block

        # Normalize item indent to match See: indent
        if len(item_indent) > len(see_indent):
            # Re-indent all list items to See: indent level
            def reindent(mm: re.Match) -> str:
                return see_indent + "* " + mm.group(1)

            rest = re.sub(r"[ \t]+\* (.+)", reindent, rest)
            item_indent = see_indent

        changes.append("see-list: added blank line before list after 'See:'")
        return f"{see_indent}See:\n\n{item_indent}* {rest}"

    def fix_label_list(m: re.Match) -> str:
        """Ensure blank line between any indented label ending with ':' and a bullet list."""
        changes.append(f"label-list: added blank line after '{m.group(1).strip()}'")
        return m.group(1) + "\n\n" + m.group(2)

    def fix_numpy_params(txt: str) -> str:  # noqa: C901
        """Remove extra indentation from numpy-style Parameters/Returns/etc. sections.

        Griffe expects:
            Parameters
            ----------
            param : type
                description

        But some docstrings have 4 extra spaces before each param and its description:
            Parameters
            ----------

                param : type

                    description

        This function normalizes them to the expected format.
        """
        lines = txt.split("\n")
        out: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Look for section header + underline
            header_match = re.match(r"^( *)\S", line)
            if header_match and i + 1 < len(lines):
                underline = lines[i + 1]
                if re.match(r"^ *-{3,}\s*$", underline) and line.rstrip() and not line.lstrip().startswith("-"):
                    base_indent = len(header_match.group(1))
                    expected_param_indent = base_indent
                    # Scan ahead to find actual param indent
                    j = i + 2
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if j < len(lines):
                        first_param = lines[j]
                        actual_indent = len(first_param) - len(first_param.lstrip())
                        extra = actual_indent - expected_param_indent
                        if extra > 0 and first_param.strip():
                            # Collect section block and de-indent by extra spaces
                            out.append(line)
                            out.append(underline)
                            i += 2
                            fixed_any = False
                            while i < len(lines):
                                bl = lines[i]
                                bl_stripped = bl.lstrip()
                                bl_indent = len(bl) - len(bl_stripped) if bl_stripped else 0
                                # Section ends when a non-blank line is at base_indent level (new section or end)
                                if bl_stripped and bl_indent <= base_indent and not re.match(r"-{3,}", bl_stripped):
                                    break
                                if bl_stripped and bl[:extra] == " " * extra:
                                    out.append(bl[extra:])
                                    fixed_any = True
                                else:
                                    out.append(bl)
                                i += 1
                            if fixed_any:
                                changes.append(f"numpy-params: de-indented {extra}sp in section '{line.strip()}'")
                            continue
            out.append(line)
            i += 1
        return "\n".join(out)

    def fix_over_indented_lists(txt: str) -> str:  # noqa: C901, PLR0915
        """De-indent bullet list blocks that are over-indented relative to their label.

        Targets blocks like:
            Label:\n\n        * item   (items 4+ spaces deeper than label)
        and normalizes item indent to match label indent.
        Handles multi-paragraph list items (continues past blank lines within the block).
        Terminates the block when a non-blank line at the SAME indent as items is not
        a list item (e.g. an admonition or new paragraph at the same level).
        Idempotent: no-op if item indent already equals label indent.
        """
        lines = txt.split("\n")
        out: list[str] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            s = line.rstrip()
            label_indent = len(s) - len(s.lstrip()) if s.strip() else 0

            # Check: indented line ending with ':', followed by a blank line
            if s and label_indent > 0 and s[-1] == ":" and i + 1 < len(lines) and not lines[i + 1].strip():
                # Skip the blank line(s) to find the list
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1

                if j < len(lines):
                    nxt = lines[j]
                    nxt_s = nxt.lstrip()
                    nxt_indent = len(nxt) - len(nxt_s)
                    extra = nxt_indent - label_indent

                    # Only fix when items are strictly deeper than label
                    if extra > 0 and nxt_s and nxt_s[0] in "*-+":
                        # Collect block continuing past blank lines.
                        # Terminate when a non-blank line satisfies:
                        #   - indent < nxt_indent  (de-indented past items), OR
                        #   - indent == nxt_indent AND not a list item (new sibling block)
                        block: list[str] = []
                        k = j
                        while k < len(lines):
                            bl = lines[k]
                            if not bl.strip():
                                # Blank line: look ahead to decide if block continues
                                m = k + 1
                                while m < len(lines) and not lines[m].strip():
                                    m += 1
                                if m >= len(lines):
                                    break  # end of text
                                nb = lines[m]
                                nb_s = nb.lstrip()
                                nb_indent = len(nb) - len(nb_s)
                                if nb_indent < nxt_indent:
                                    break  # de-indented: end of block
                                if nb_indent == nxt_indent and not (nb_s and nb_s[0] in "*-+" and nb_s[1:2] == " "):
                                    break  # same-level non-list content: end of block
                                block.append(bl)
                                k += 1
                                continue
                            bi = len(bl) - len(bl.lstrip())
                            if bi < nxt_indent:
                                break
                            block.append(bl)
                            k += 1

                        # De-indent each block line by `extra` spaces
                        new_block = [bl[extra:] if bl[:extra] == " " * extra else bl for bl in block]
                        changes.append(f"label-list: de-indented {extra}sp after '{s.strip()}'")
                        out.append(line)
                        # Preserve blank lines between label and block
                        out.extend(lines[i + 1 : j])
                        out.extend(new_block)
                        i = k
                        continue

            out.append(line)
            i += 1
        return "\n".join(out)

    new_text = re.sub(r"\[([a-z][a-z0-9]*(?:-[a-z0-9]+)*)\]\[\]", replace_ref, text)
    new_text = re.sub(r"\[([^\]]+)\]\[([a-z][a-z0-9]*(?:-[a-z0-9]+)*)\]", replace_text_ref, new_text)
    new_text = re.sub(r"\[([^\]]+)\]\[([A-Z][A-Za-z0-9]*)\]", replace_label_ref, new_text)
    new_text = re.sub(r"\[([^\]]+)\]\[(onetl\.[a-zA-Z0-9_.]+)\]", replace_python_path, new_text)
    new_text = re.sub(r"\[(onetl\.[a-zA-Z0-9_.]+)\]\[\]", replace_python_path_self, new_text)
    new_text = re.sub(r"\[([A-Za-z][\w.]*)\]\[\]", replace_shortname, new_text)
    # Global: List of X → list[X] (Returns sections and body text)
    new_text = re.sub(r"\bList of ([^\s,]+)", r"list[\1]", new_text)
    new_text = re.sub(r"^( {1,}\w+ : )(.+)$", fix_numpy_type, new_text, flags=re.MULTILINE)
    # Fix See: blocks: ensure blank line before bullet list, normalize over-indented items.
    # Only fires when there is NO blank line between See: and the first * (i.e. \n followed
    # immediately by optional spaces + *), leaving already-correct blocks untouched.
    new_text = re.sub(
        r"^( *)See:\n(?!\n)( *)\* (.+(?:\n(?!\n)[ \t]*\* .+)*)",
        fix_see_list,
        new_text,
        flags=re.MULTILINE,
    )
    # Fix any indented label ending with ':' that is immediately followed by a bullet list
    # (no blank line between them). Applied after fix_see_list so 'See:' blocks are already
    # handled and won't be double-processed.
    new_text = re.sub(
        r"^( +\w[^\n]*:)\n(?!\n)( +[*-] )",
        fix_label_list,
        new_text,
        flags=re.MULTILINE,
    )
    # De-indent over-indented list blocks (items deeper than label → code block in Python-Markdown)
    new_text = fix_over_indented_lists(new_text)
    # Fix over-indented numpy Parameters/Returns/etc. sections (griffe cannot parse them)
    new_text = fix_numpy_params(new_text)
    return new_text, changes


# ---------------------------------------------------------------------------
# File processor (same structure as rst2md.py)
# ---------------------------------------------------------------------------

_TRIPLE_QUOTED = re.compile(
    r'([rRbBuUfF]?"""(?:[^"\\]|\\.|"{1,2}(?!"))*"""|'
    r"[rRbBuUfF]?'''(?:[^'\\]|\\.|'{1,2}(?!'))*''')",
    re.DOTALL,
)


_NOQA_RE = re.compile(r"\s*#\s*noqa[^\n]*$")


def find_docstrings(source: str) -> list[tuple[int, int]]:
    # Characters that indicate we're mid-expression (function call, list, etc.)
    _expr_chars = frozenset("(,[{+-*/%&|^~\\")
    results = []
    for m in _TRIPLE_QUOTED.finditer(source):
        preceding = _NOQA_RE.sub("", source[: m.start()].rstrip()).rstrip()
        # Standard positions: module start, after 'def foo():', 'class Foo:', etc.
        if preceding.endswith(":") or not preceding or preceding[-1] in ("\n", "#"):
            results.append((m.start(), m.end()))
            continue
        # Field docstring: """ starts at the beginning of an indented line
        # (only whitespace before it on the current line) and we're not mid-expression.
        line_start = source.rfind("\n", 0, m.start()) + 1
        if source[line_start : m.start()].strip() == "" and preceding[-1] not in _expr_chars:
            results.append((m.start(), m.end()))
    return results


def process_file(path: Path, *, dry_run: bool) -> bool:
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
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

        converted, changes = _fix_refs(body)
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
# Docs .md file processor
# ---------------------------------------------------------------------------


def process_md_file(path: Path, *, dry_run: bool) -> bool:
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"  ERROR reading {path}: {e}", file=sys.stderr)
        return False

    new_source = source
    file_changes: list[str] = []

    for old, new in DOCS_BROKEN_LINKS.items():
        if old in new_source:
            new_source = new_source.replace(old, new)
            file_changes.append(f"broken-link: {old!r} → {new!r}")

    if not file_changes:
        return False

    if dry_run:
        print(f"\n  {path}")
        for c in file_changes:
            print(f"    · {c}")
    else:
        path.write_text(new_source, encoding="utf-8")

    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix doc-anchor cross-references in converted docstrings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing files")
    parser.add_argument("--path", default="onetl/", help="Directory to process (default: onetl/)")
    parser.add_argument("--file", help="Process a single file")
    parser.add_argument("--docs-path", help="Also fix broken links in docs .md files under PATH")
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

    if args.docs_path:
        md_files = sorted(Path(args.docs_path).rglob("*.md"))
        print(f"\nProcessing {len(md_files)} docs .md file(s) [{mode}]...")
        md_changed = 0
        for f in md_files:
            if process_md_file(f, dry_run=args.dry_run):
                md_changed += 1
                if not args.dry_run:
                    print(f"  ✓ {f}")
        print(f"Done: {md_changed}/{len(md_files)} docs files {label}.")


if __name__ == "__main__":
    main()
