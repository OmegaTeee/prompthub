#!/usr/bin/env python3
"""Check wiki markdown files for broken internal links and generate a health report.

The script scans all markdown files under docs/wiki/{concepts,entities,sources,syntheses},
extracts wikilinks in the form [[slug]], and verifies that each referenced slug
points to an existing markdown file. It outputs a JSON report summarizing the
findings, including per-file broken links and a summary of missing references.
This tool enables automated monitoring of wiki integrity and can be part of a
maintenance cadence (e.g., weekly or monthly runs)."""

import json
import re
import sys
from pathlib import Path


def find_md_files(wiki_root: Path) -> list[Path]:
    """Return a list of all markdown files under the wiki sections."""
    sections = ["concepts", "entities", "sources", "syntheses"]
    files = []
    for section in sections:
        files.extend((wiki_root / section).glob("*.md"))
    return files


def normalize_target(raw: str) -> str | None:
    """Normalize a wikilink target to a bare slug, or None if it should be ignored.

    Handles aliases (``[[slug|label]]``), anchors (``[[slug#section]]``), and
    section-qualified or relative targets (``[[concepts/foo]]``, ``[[../concepts/foo]]``)
    by returning the final path component. Targets containing ``..`` segments are
    rejected (return None) so unsafe paths can't escape the wiki tree.
    """
    target = raw.split("|", 1)[0].split("#", 1)[0].strip()
    if not target:
        return None
    parts = Path(target).parts
    if ".." in parts:
        return None
    return Path(target).name


def extract_slugs(md_text: str) -> list[str]:
    """Extract and normalize wiki slugs from markdown text (pattern ``[[slug]]``)."""
    slugs = []
    for raw in re.findall(r"\[\[([^\]]+)\]\]", md_text):
        slug = normalize_target(raw)
        if slug is not None:
            slugs.append(slug)
    return slugs


def check_links() -> dict:
    wiki_root = Path(__file__).resolve().parent.parent / "wiki"
    report = {"files": {}, "summary": {}}
    all_slugs_in_use = set()
    missing_slugs_global = set()

    for file_path in find_md_files(wiki_root):
        rel_path = str(file_path.relative_to(wiki_root))
        text = file_path.read_text(encoding="utf-8")
        slugs = extract_slugs(text)
        all_slugs_in_use.update(slugs)

        broken = []
        for slug in slugs:
            target_path = None
            for section in ["concepts", "entities", "sources", "syntheses"]:
                candidate = wiki_root / section / f"{slug}.md"
                if candidate.exists():
                    target_path = candidate
                    break
            if target_path is None:
                broken.append(slug)
                missing_slugs_global.add(slug)

        if broken:
            report["files"][rel_path] = broken

    # Populate summary
    if missing_slugs_global:
        report["summary"]["missing_global_slugs"] = sorted(missing_slugs_global)
    else:
        report["summary"]["missing_global_slugs"] = []

    return report


if __name__ == "__main__":
    report = check_links()
    print(json.dumps(report, indent=2, sort_keys=True))
    # Exit non-zero when broken links exist so CI/automation can catch regressions.
    sys.exit(1 if report["summary"]["missing_global_slugs"] else 0)