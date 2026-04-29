#!/usr/bin/env python3
"""
Insert conservative mapping notes above fenced code blocks that contain historical model tokens.
- Does NOT modify the code block contents.
- Adds a blockquote NOTE before the fenced block if the block contains any of the tokens.
- Skips files that already contain the mapping parenthetical in proximate lines.

Run from repo root:
    python3 scripts/insert_mapping_notes.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "docs/archive/2026-01-30-integration-fixes.md",
    "docs/architecture/ADR-007-cloud-fallback.md",
    "docs/superpowers/plans/2026-03-24-lm-studio-backend.md",
    "docs/notes/models/model-profiles-settings.md",
]

MAPPINGS = {
    "gemma3": "gemma3 (now qwen3-4b-instruct-2507)",
    "llama3.2": "llama3.2 (now qwen3-4b-instruct-2507)",
    "qwen2.5-coder": "qwen2.5-coder (now qwen3-4b-instruct-2507)",
    "qwen3:14b": "qwen3:14b (now qwen3-4b-thinking-2507)",
}
TOKEN_RE = re.compile(r"(" + "|".join(re.escape(k) for k in MAPPINGS.keys()) + r")", re.IGNORECASE)

NOTE_TEMPLATE = "> **NOTE:** Historical model token `{token}` appears in the following code block; prefer mapping: {mapping}. Do not change the code block without a manual review.\n\n"


def process(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"SKIP read error: {path}: {e}")
        return False

    lines = text.splitlines(keepends=True)
    out_lines = []
    changed = False
    in_fence = False
    fence_start_idx = None

    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            if not in_fence:
                # fence opening
                in_fence = True
                fence_start_idx = len(out_lines)
                out_lines.append(line)
            else:
                # fence closing; check the block content between fence_start_idx+1 and current out_lines end
                in_fence = False
                # gather block content from original lines between fence boundaries
                # find indices in original lines
                # We can get block text from lines slice
                # Determine original fence start and end in lines
                # For simplicity, reconstruct block using the lines between previous '```' and this one
                # Find backwards in 'lines' for the matching opening fence
                # We'll search back from i-1
                j = i - 1
                while j >= 0 and not lines[j].strip().startswith('```'):
                    j -= 1
                block_text = ''.join(lines[j+1:i])
                m = TOKEN_RE.search(block_text)
                if m:
                    token = m.group(1)
                    mapping = MAPPINGS.get(token.lower(), MAPPINGS.get(token, token))
                    # check preceding 3 output lines to avoid duplicate notes
                    prev_context = ''.join(out_lines[max(0, fence_start_idx-3):fence_start_idx])
                    if mapping not in prev_context:
                        note = NOTE_TEMPLATE.format(token=token, mapping=mapping)
                        out_lines.insert(fence_start_idx, note)
                        changed = True
                out_lines.append(line)
        else:
            out_lines.append(line)

    if changed:
        path.write_text(''.join(out_lines), encoding='utf-8')
        print(f"NOTED: {path}")
        return True
    else:
        print(f"SKIPPED: {path} (no block-only tokens found)")
        return False


def main():
    changed_files = []
    for p in FILES:
        path = ROOT / p
        if not path.exists():
            print(f"MISSING: {path}")
            continue
        if process(path):
            changed_files.append(p)
    print('\nSummary:')
    print(f"Files scanned: {len(FILES)}")
    print(f"Files changed: {len(changed_files)}")
    for f in changed_files:
        print(f" - {f}")

if __name__ == '__main__':
    main()
