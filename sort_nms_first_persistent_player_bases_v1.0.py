#!/usr/bin/env python3
"""
sort_nms_first_persistent_player_bases.py

Sorts the FIRST PersistentPlayerBases section in a No Man's Sky save JSON export,
preserving each base object as raw text and leaving the SECOND PersistentPlayerBases
section untouched.

Validated workflow target:
- The FIRST PersistentPlayerBases section controls the in-game Terminus / My Bases order.
- The SECOND PersistentPlayerBases section appears to be sync/internal persistence data and
  should not be edited for teleporter ordering.

Input may be either:
- a .zip containing one JSON-like save export file, or
- a raw .json/.hg text export.

Outputs:
- <input_stem>_first_bases_sorted_by_name_raw_preserved.json
- <input_stem>_first_bases_sorted_by_name_raw_preserved.zip
- <input_stem>_sorted_first_PersistentPlayerBases.txt

The original input file is never modified.

The included .bat file contains the following command line:

py sort_nms_first_persistent_player_bases.py save.hg.zip

py invokes Python, followed by the py scriptname, followed by the zip filename containing your
JSON export from your gamesave file.

You can change any of those values to something you like better, and/or you can simply type the
command line that fits your reality in the terminal prompt or PowerShell prompt.


"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

SECTION_NAME = '"PersistentPlayerBases"'


@dataclass(frozen=True)
class SectionBounds:
    key_start: int          # start index of "PersistentPlayerBases"
    array_start: int        # index of [
    array_end: int          # index of matching ]
    section_end: int        # one char after matching ]


@dataclass(frozen=True)
class BaseBlock:
    prefix: str             # whitespace/comments before the object, usually newline+indent
    object_text: str        # raw object text, from { through matching }
    suffix: str             # separator after object, usually comma or trailing whitespace
    name: str               # parsed top-level Name value
    original_index: int


def read_input(path: Path) -> Tuple[str, str, bool]:
    """Return (text, inner_name, input_was_zip)."""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            if not names:
                raise ValueError(f"ZIP contains no files: {path}")

            # Prefer JSON/HG-looking files, otherwise fall back to the first file.
            preferred = [n for n in names if n.lower().endswith((".json", ".hg", ".txt"))]
            inner_name = preferred[0] if preferred else names[0]
            data = zf.read(inner_name)
    else:
        inner_name = path.name
        data = path.read_bytes()

    # Preserve text as much as possible. NMS exports are usually UTF-8.
    text = data.decode("utf-8-sig")
    return text, inner_name, path.suffix.lower() == ".zip"


def find_matching_bracket(text: str, open_index: int, open_char: str, close_char: str) -> int:
    """Find matching bracket/brace, respecting JSON strings and escapes."""
    depth = 0
    in_string = False
    escape = False

    for i in range(open_index, len(text)):
        ch = text[i]

        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return i

    raise ValueError(f"No matching {close_char!r} found for {open_char!r} at index {open_index}")


def find_persistent_player_bases_sections(text: str) -> List[SectionBounds]:
    sections: List[SectionBounds] = []
    pos = 0

    while True:
        key_start = text.find(SECTION_NAME, pos)
        if key_start == -1:
            break

        colon = text.find(":", key_start + len(SECTION_NAME))
        if colon == -1:
            raise ValueError("Found PersistentPlayerBases key without a colon.")

        array_start = text.find("[", colon + 1)
        if array_start == -1:
            raise ValueError("Found PersistentPlayerBases key without an array start.")

        array_end = find_matching_bracket(text, array_start, "[", "]")
        sections.append(SectionBounds(key_start, array_start, array_end, array_end + 1))
        pos = array_end + 1

    return sections


def iter_top_level_objects_with_separators(array_body: str) -> List[BaseBlock]:
    """
    Split an array body into raw top-level object blocks while preserving the text around each object.

    array_body is the text between [ and ]. For this section it should contain JSON objects separated
    by commas and whitespace.
    """
    blocks: List[BaseBlock] = []
    cursor = 0
    index = 0

    while True:
        obj_start = array_body.find("{", cursor)
        if obj_start == -1:
            trailing = array_body[cursor:]
            if trailing.strip():
                raise ValueError("Unexpected non-whitespace text after final base object.")
            break

        prefix = array_body[cursor:obj_start]
        obj_end = find_matching_bracket(array_body, obj_start, "{", "}")
        object_text = array_body[obj_start:obj_end + 1]

        # Capture separator after the object through the comma if present, plus following whitespace.
        sep_start = obj_end + 1
        sep_end = sep_start
        while sep_end < len(array_body) and array_body[sep_end].isspace():
            sep_end += 1
        if sep_end < len(array_body) and array_body[sep_end] == ",":
            sep_end += 1
            while sep_end < len(array_body) and array_body[sep_end].isspace():
                sep_end += 1

        suffix = array_body[sep_start:sep_end]
        name = extract_base_name(object_text)
        blocks.append(BaseBlock(prefix=prefix, object_text=object_text, suffix=suffix,
                                name=name, original_index=index))
        index += 1
        cursor = sep_end

    return blocks


def extract_base_name(object_text: str) -> str:
    """Parse only the single base object and return its top-level Name field."""
    try:
        obj = json.loads(object_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse one base object as JSON near: {object_text[:120]!r}") from exc

    value = obj.get("Name", "")
    if value is None:
        return ""
    return str(value)


def natural_key(value: str) -> Tuple:
    """Case-insensitive natural-ish sort key, so G002 sorts before G010."""
    parts = re.split(r"(\d+)", value.casefold())
    key = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part)))
        else:
            key.append((1, part))
    return tuple(key)


def rebuild_array_body_preserving_layout(blocks: List[BaseBlock], sorted_blocks: List[BaseBlock]) -> str:
    """
    Rebuild array body by reusing the positional prefix/suffix layout from the original array,
    while inserting sorted raw object_text blocks into those slots.

    This keeps indentation/comma style aligned with the original export.
    """
    if len(blocks) != len(sorted_blocks):
        raise ValueError("Block count changed during sort; refusing to rebuild.")

    pieces = []
    for original_layout, sorted_block in zip(blocks, sorted_blocks):
        pieces.append(original_layout.prefix)
        pieces.append(sorted_block.object_text)
        pieces.append(original_layout.suffix)
    return "".join(pieces)


def make_outputs(input_path: Path, original_text: str, inner_name: str, modified_text: str,
                 sorted_section_text: str) -> Tuple[Path, Path, Path]:
    stem = input_path.stem if input_path.suffix.lower() == ".zip" else input_path.with_suffix("").name
    out_base = input_path.with_name(f"{stem}_first_bases_sorted_by_name_raw_preserved")
    # Do not use Path.with_suffix() here because stems like "save7.hg" contain dots.
    json_path = Path(str(out_base) + ".json")
    zip_path = Path(str(out_base) + ".zip")
    section_path = input_path.with_name(f"{stem}_sorted_first_PersistentPlayerBases.txt")

    json_path.write_text(modified_text, encoding="utf-8", newline="")
    section_path.write_text(sorted_section_text, encoding="utf-8", newline="")

    # Store the modified JSON using the original inner filename when possible.
    zip_inner_name = Path(inner_name).name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(zip_inner_name, modified_text.encode("utf-8"))

    return json_path, zip_path, section_path


def sort_first_persistent_player_bases(text: str) -> Tuple[str, str, dict]:
    sections = find_persistent_player_bases_sections(text)
    if len(sections) < 1:
        raise ValueError("No PersistentPlayerBases sections found.")

    target = sections[0]
    array_body = text[target.array_start + 1:target.array_end]
    blocks = iter_top_level_objects_with_separators(array_body)

    if not blocks:
        raise ValueError("First PersistentPlayerBases section contains no base records.")

    # Blank names are kept after named bases. They may exist as internal/stale records,
    # but putting them first would be counterproductive for the visible Terminus list.
    sorted_blocks = sorted(blocks, key=lambda b: (b.name.strip() == "", natural_key(b.name), b.original_index))
    new_array_body = rebuild_array_body_preserving_layout(blocks, sorted_blocks)

    modified_text = text[:target.array_start + 1] + new_array_body + text[target.array_end:]
    sorted_section_text = text[target.key_start:target.array_start + 1] + new_array_body + text[target.array_end:target.section_end]

    # Integrity checks.
    original_object_set = sorted(b.object_text for b in blocks)
    new_blocks = iter_top_level_objects_with_separators(new_array_body)
    new_object_set = sorted(b.object_text for b in new_blocks)

    if original_object_set != new_object_set:
        raise ValueError("Integrity check failed: sorted output does not contain the exact same raw base objects.")

    if len(modified_text) != len(text):
        # This should normally remain identical because object text is merely permuted into same slots.
        # Not fatal, but signal it clearly.
        size_note = "changed"
    else:
        size_note = "identical"

    # Verify second section text, if present, is untouched.
    untouched_second = True
    if len(sections) >= 2:
        second = sections[1]
        # Recalculate bounds in modified text by finding sections again.
        modified_sections = find_persistent_player_bases_sections(modified_text)
        untouched_second = (
            len(modified_sections) >= 2 and
            text[second.key_start:second.section_end] ==
            modified_text[modified_sections[1].key_start:modified_sections[1].section_end]
        )

    if len(sections) >= 2 and not untouched_second:
        raise ValueError("Integrity check failed: second PersistentPlayerBases section was modified.")

    info = {
        "sections_found": len(sections),
        "first_section_records": len(blocks),
        "second_section_records": None,
        "first_name_before": blocks[0].name,
        "first_name_after": sorted_blocks[0].name,
        "last_name_after": sorted_blocks[-1].name,
        "file_size": size_note,
        "second_section_untouched": untouched_second,
    }

    if len(sections) >= 2:
        second_body = text[sections[1].array_start + 1:sections[1].array_end]
        try:
            info["second_section_records"] = len(iter_top_level_objects_with_separators(second_body))
        except Exception:
            info["second_section_records"] = "not counted"

    return modified_text, sorted_section_text, info


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sort the FIRST NMS PersistentPlayerBases section by Name while preserving raw base objects."
    )
    parser.add_argument("input", help="Path to NMS exported save ZIP or raw JSON/HG text file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"ERROR: Input file does not exist: {input_path}", file=sys.stderr)
        return 2

    try:
        text, inner_name, was_zip = read_input(input_path)
        modified_text, sorted_section_text, info = sort_first_persistent_player_bases(text)
        json_path, zip_path, section_path = make_outputs(input_path, text, inner_name, modified_text, sorted_section_text)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("NMS PersistentPlayerBases sort complete.")
    print()
    print("Input:")
    print(f"  {input_path}")
    print(f"  Source inside ZIP/file: {inner_name}")
    print()
    print("Validated actions:")
    print("  Targeted FIRST PersistentPlayerBases section only.")
    print(f"  PersistentPlayerBases sections found: {info['sections_found']}")
    print(f"  First section records sorted: {info['first_section_records']}")
    if info.get("second_section_records") is not None:
        print(f"  Second section records: {info['second_section_records']}")
    print(f"  Second section untouched: {info['second_section_untouched']}")
    print("  Raw base object text preserved; objects were reordered, not re-serialized.")
    print(f"  File size after reorder: {info['file_size']}")
    print()
    print("Sort check:")
    print(f"  First base before sort: {info['first_name_before']}")
    print(f"  First base after sort:  {info['first_name_after']}")
    print(f"  Last base after sort:   {info['last_name_after']}")
    print()
    print("Generated files:")
    print(f"  Full modified JSON:     {json_path}")
    print(f"  Full modified ZIP:      {zip_path}")
    print(f"  Sorted section only:    {section_path}")
    print()
    print("Original input was not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
