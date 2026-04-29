#!/usr/bin/env python3
"""
Safely replace occurrences of "Ollama"/"ollama" with "LLM"/"llm" in markdown files
under docs/. Skips fenced code blocks (```).
Also scans for model tokens that require manual review and reports them.
Outputs a JSON summary to stdout.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TARGET_FILES = list(DOCS.rglob("*.md"))

# patterns
ollama_pattern = re.compile(r"\b(Ollama)\b")
ollama_lower_pattern = re.compile(r"\b(ollama)\b")

# model tokens to flag for manual review (case-insensitive)
model_tokens = [
    "gemma3",
    "llama3.2",
    "qwen2.5-coder",
    "qwen3:14b",
]
model_re = re.compile(r"(" + "|".join(re.escape(t) for t in model_tokens) + r")",
                      flags=re.IGNORECASE)

def main() -> None:
    """Run the docs-safe replacement pass.

    Scans markdown files under `docs/`, replaces prose occurrences of
    "Ollama"/"ollama" with "LLM"/"llm" outside fenced code blocks,
    and collects model tokens that require manual review.
    Prints a JSON summary to stdout.
    """
    changed_files: list[str] = []
    manual_review: dict[str, list[dict[str, int | str]]] = {}

    for path in TARGET_FILES:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Skip files we can't read (permission, encoding issues)
            continue

        lines = text.splitlines(keepends=True)
        in_fence = False
        new_lines: list[str] = []
        file_changed = False
        for line in lines:
            # detect fenced blocks (```), ignore ``` with language
            if line.strip().startswith("```"):
                in_fence = not in_fence
                new_lines.append(line)
                continue
            if in_fence:
                new_lines.append(line)
                continue
            # outside fenced blocks: replace Ollama/Ollama
            new_line = ollama_pattern.sub("LLM", line)
            new_line = ollama_lower_pattern.sub("llm", new_line)
            if new_line != line:
                file_changed = True
            new_lines.append(new_line)

        # scan for model tokens in original text for manual review
        model_matches: list[dict[str, int | str]] = []
        for m in model_re.finditer(text):
            # capture the line number
            start = m.start()
            lineno = text.count("\n", 0, start) + 1
            model_matches.append({"token": m.group(0), "line": lineno})

        if model_matches:
            manual_review[str(path.relative_to(ROOT))] = model_matches

        if file_changed:
            path.write_text("".join(new_lines), encoding="utf-8")
            changed_files.append(str(path.relative_to(ROOT)))

    summary = {
        "changed_files": changed_files,
        "manual_review": manual_review,
        "counts": {
            "files_scanned": len(TARGET_FILES),
            "files_changed": len(changed_files),
            "files_flagged_manual": len(manual_review),
        },
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
