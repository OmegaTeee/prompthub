# Project TODOs

- [x] **Project paths** — Updated `~/.local/share/prompthub/` → `~/prompthub/` across guides, scripts, and start script. Symlink keeps old paths working.
- [x] **Dashboard URL** — Confirmed default is `http://localhost:9090/dashboard`. No stale `localhost:3000` references for the PromptHub dashboard.
- [x] **Start/kill scripts** — Fixed `$HOME/PromptHub` → `$HOME/prompthub` in `prompthub-start.zsh`. Fixed script name references in `QUICKSTART.md`.
- [x] **Open WebUI port bugs** — `_get_open_webui_info()` now reads port from `~/.prompthub/open-webui.json`. Fixed `start.sh` variable ordering so config file port takes effect.
- [x] **Documentation refresh** — All user guides (`docs/guides/01–09`) rewritten to grade 9–10 readability standard (short sentences, active voice, analogies, key-point summaries).
- [x] **Symlink for guides** — Removed; `docs/guides/` is now directly at project root.
- [x] **QUICKSTART.md** — Finalised at project root. Paths, script names, and readability standard applied.
