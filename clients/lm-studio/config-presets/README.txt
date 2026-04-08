# LM Studio Config Presets

This directory stores LM Studio preset JSON files for local model defaults and task-specific
chat behavior.

## Naming convention

Use filenames that match the preset `name` field and keep the model family/version visible:

- `Qwen3-0.6B.preset.json`
- `Qwen3-4B-Instruct-2507.preset.json`
- `Qwen3-4B-Thinking-2507.preset.json`
- `DeepSeek-R1-0528-Qwen3-8B.preset.json`
- `Text-Rewriter.preset.json`

Avoid duplicate suffixes such as `(2)` and avoid mixed spacing styles.

## Recommended split

Use model presets for reusable runtime defaults:

- `Qwen3-4B-Instruct-2507.preset.json` for fast deterministic rewrite and assistant tasks
- `Qwen3-4B-Thinking-2507.preset.json` for deliberate reasoning-heavy tasks
- `Qwen3-0.6B.preset.json` as a small compatible draft model for speculative decoding

Use task presets for behavior shaping:

- `Text-Rewriter.preset.json` references `../prompt_templates/proof-read.txt` by name and
  adds rewrite-oriented sampling defaults

## Current rewrite defaults

For quick prompt rewriting, the repository standard is:

- `temperature: 0.2`
- `top_p: 0.9`
- `top_k: 40`
- `repeat_penalty: 1.05`
- `maxTokens: 256`
- `contextLength: 4096`
- `draftModel: qwen3-0.6b`

## Common pitfalls

- Using a draft model that is too large, which can reduce speed instead of improving it
- Letting the task preset and the model preset drift apart
- Confusing the preset filename with the LM Studio model key
- Relying on duplicate preset exports instead of cleaning up names after import

If LM Studio uses a different local key for the 0.6B draft model on this machine, update the
`draftModel` field in both rewrite-oriented presets to match the exact loaded model key.
