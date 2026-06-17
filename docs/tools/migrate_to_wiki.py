#!/usr/bin/env python3
"""Migrate an archive markdown file into the PromptHub wiki.

Usage:
    python docs/tools/migrate_to_wiki.py <archive-file> <section> <slug> <title>

Example:
    python docs/tools/migrate_to_wiki.py docs/archive/2026-02-03-agents-md-treatment.md syntheses agents-md-treatment "Agents.md Treatment"
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def main() -> None:
    parser = argparse.ArgumentParser(description="Move an archive file into the LLM Wiki.")
    parser.add_argument("archive_file", type=Path, help="Path to the archive markdown file")
    parser.add_argument("section", choices=["concepts", "entities", "sources", "syntheses"], help="Target wiki section")
    parser.add_argument("slug", help="Wiki slug for the new file")
    parser.add_argument("title", help="Human-readable title")
    args = parser.parse_args()

    wiki_root = Path(__file__).resolve().parents[2] / "docs" / "wiki"
    target_dir = wiki_root / args.section
    target_file = target_dir / f"{args.slug}.md"

    if not args.archive_file.exists():
        raise FileNotFoundError(f"Archive file not found: {args.archive_file}")
    if target_file.exists():
        raise FileExistsError(f"Target wiki file already exists: {target_file}")

    content = args.archive_file.read_text(encoding="utf-8")
    frontmatter = (
        "---\n"
        f"slug: {args.slug}\n"
        f"section: {args.section}\n"
        "status: archived-to-wiki\n"
        f"original_file: ../archive/{args.archive_file.name}\n"
        "---\n\n"
        f"# {args.title}\n\n"
    )

    target_dir.mkdir(parents=True, exist_ok=True)
    target_file.write_text(frontmatter + content, encoding="utf-8")

    # Move the original archive file to a staging folder instead of deleting it.
    staging_dir = args.archive_file.parent / ".to-delete"
    staging_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(args.archive_file), str(staging_dir / args.archive_file.name))

    print(f"Migrated: {args.archive_file.name} -> docs/wiki/{args.section}/{args.slug}.md")
    print(f"Original moved to: docs/archive/.to-delete/{args.archive_file.name}")


if __name__ == "__main__":
    main()
