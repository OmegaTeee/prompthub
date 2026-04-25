#!/usr/bin/env python3
"""
Apply conservative parenthetical model mappings to flagged markdown files.
- Replacements are applied only outside fenced code blocks (```), and only
  outside inline code spans delimited by backticks (`).
- Tokens mapped:
    gemma3 -> gemma3 (now qwen3-4b-instruct-2507)
    llama3.2 -> llama3.2 (now qwen3-4b-instruct-2507)
    qwen2.5-coder -> qwen2.5-coder (now qwen3-4b-instruct-2507)
    qwen3:14b -> qwen3:14b (now qwen3-4b-thinking-2507)

This script is intentionally conservative: it will only edit prose segments
and will not touch fenced code blocks or inline code spans.

Run from repo root:
    python3 scripts/apply_model_mappings.py

"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "docs/rewrite-verification-report.md",
    "docs/archive/2026-02-17-secrets-docs-fixes.md",
    "docs/archive/TODOS.reordered.md",
    "docs/archive/2026-01-30-integration-fixes.md",
    "docs/architecture/ADR-009-orchestrator-agent.md",
    "docs/architecture/ADR-006-enhancement-timeout.md",
    "docs/architecture/ADR-003-per-client-enhancement.md",
    "docs/architecture/ADR-007-cloud-fallback.md",
    "docs/architecture/ADR-008-task-specific-models.md",
    "docs/superpowers/plans/2026-03-24-lm-studio-backend.md",
    "docs/notes/research/lmstudio-enhancement-sketch.md",
    "docs/notes/models/model-profiles-settings.md",
]

MAPPINGS = {
    "gemma3": "gemma3 (now qwen3-4b-instruct-2507)",
    "llama3.2": "llama3.2 (now qwen3-4b-instruct-2507)",
    "qwen2.5-coder": "qwen2.5-coder (now qwen3-4b-instruct-2507)",
    "qwen3:14b": "qwen3:14b (now qwen3-4b-thinking-2507)",
}

# build regex to match tokens as whole words (case-sensitive to preserve formatting)
TOKEN_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in MAPPINGS.keys()) + r")\b")


def replace_in_segment(seg: str) -> str:
    # seg is outside inline backticks; perform replacements safely
    def _repl(m: re.Match) -> str:
        token = m.group(1)
        return MAPPINGS.get(token, token)

    return TOKEN_RE.sub(_repl, seg)


def process_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"SKIP (read error): {path}: {e}")
        return False

    lines = text.splitlines(keepends=True)
    in_fence = False
    out = []
    changed = False

    for line in lines:
        if line.strip().startswith("```"):
            # toggle fence, keep line as-is
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        # outside fenced block: handle inline backticks by splitting
        parts = line.split('`')
        for i, part in enumerate(parts):
            if i % 2 == 0:
                # outside inline code
                new_part = replace_in_segment(part)
                if new_part != part:
                    changed = True
                parts[i] = new_part
            else:
                # inside inline code: leave alone
                parts[i] = part
        out.append('`'.join(parts))

    if changed:
        path.write_text(''.join(out), encoding='utf-8')
        print(f"UPDATED: {path}")
        return True
    else:
        print(f"NOCHANGE: {path}")
        return False


def main():
    changed_files = []
    for p in FILES:
        path = ROOT / p
        if not path.exists():
            print(f"MISSING: {path} — skipping")
            continue
        if process_file(path):
            changed_files.append(p)

    print('\nSummary:')
    print(f"Files scanned: {len(FILES)}")
    print(f"Files changed: {len(changed_files)}")
    if changed_files:
        for f in changed_files:
            print(f" - {f}")


if __name__ == '__main__':
    main()
