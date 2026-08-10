#!/usr/bin/env python3
"""Validate that a Markdown file is well-formed OKF. Exit 0 = valid."""
import sys, pathlib
try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

REQUIRED = {"type", "resource", "tags", "timestamp"}

def main(path: str) -> int:
    p = pathlib.Path(path)
    text = p.read_text(encoding="utf-8")
    if not text.startswith("---"):
        print(f"FAIL {p.name}: no YAML frontmatter"); return 1
    _, fm, _ = text.split("---", 2)
    meta = yaml.safe_load(fm) or {}
    missing = REQUIRED - set(meta)
    if missing:
        print(f"FAIL {p.name}: missing keys {sorted(missing)}"); return 1
    if meta["resource"] != p.stem:
        print(f"FAIL {p.name}: resource '{meta['resource']}' != filename stem '{p.stem}'"); return 1
    print(f"OK   {p.name}: valid OKF ({meta['type']})"); return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
