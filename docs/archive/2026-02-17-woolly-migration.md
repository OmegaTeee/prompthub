# PromptHub Migration Complete — February 17, 2026

## Summary

The PromptHub project has been successfully migrated from `~/Code/woolly/` to `~/prompthub/` with full history and context preservation.

**Status**: ✅ Complete | **Date**: 2026-02-17 | **Impact**: Zero disruption

---

## What Changed

### Before Migration
```
~/Code/woolly/                    ← Old development location
├── app/                          # Python FastAPI router
├── clients/                      # Client setup scripts
├── mcps/                         # Node.js MCP servers
├── .git/                         # Git history
├── .venv/                        # Python venv (118MB)
└── node_modules/ (within mcps)   # Node packages
```

### After Migration
```
~/prompthub/         ← New canonical location
├── app/                          # Python FastAPI router
├── clients/                      # Client setup scripts
├── mcps/                         # Node.js MCP servers
└── ...                           # All original files

~/Code/woolly → ~/prompthub  ← Symlink (forwarding)
```

---

## Why This Migration

1. **Consolidation**: PromptHub lives alongside other user tools and configs in `~/`
2. **Elimination of Duplication**: Single source of truth, no conflicting references
3. **History Preservation**: All conversations and context maintained
4. **Clean Forwarding**: Old paths still work via symlinks

---

## Context & History Preservation

### Claude Project Contexts

**Primary Context**: `~/.claude/projects/-Users-visualval--cursor-worktrees-woolly--Workspace--eoz`
- Contains 122 conversation history files (JSONL)
- All project history and context from development
- Automatically updated as you work

**Alias**: `~/.claude/projects/-Users-visualval--local-share-prompthub`
- Symlink pointing to primary context
- Ensures both old and new references work
- No duplication of conversation history

### Git History

**Backup Location**: `/Users/visualval/Code/woolly.full-backup/`
- Full git repository with complete history
- All commits preserved: 327f63f (main branch)
- Readable if you need to access old history

**Bundle**: `/tmp/woolly-git-history.bundle`
- Git bundle format suitable for archival
- Can be imported if needed in future

### Reference Archive

**Location**: `/Users/visualval/Code/woolly-archive-2026-02-17/`
- Old CHANGELOG.md, CLAUDE.md, README.md (for reference only)
- Git history folder (.git/)
- MIGRATION-INFO.txt explaining the change

---

## Accessing the Project

### Most Common Operations

```bash
# All paths work now:
cd ~/.local/share/prompthub          # New canonical path
cd ~/Code/woolly                     # Old path (symlink)

# Setup
cd app && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ../mcps && npm install && cd ..

# Run
cd app && uvicorn router.main:app --reload --port 9090

# Test
cd app && pytest tests/ -v
```

### Symlink Transparency

Everything continues to work from **both** old and new paths:

```bash
# These are equivalent:
open ~/Code/woolly/CLAUDE.md
open ~/prompthub/CLAUDE.md

# Both access the SAME file
```

---

## Cleanup Actions Taken

✅ **Symlink Created**: `~/Code/woolly/` → `~/prompthub/`
✅ **Claude Contexts Consolidated**: VSCode & stargazing-waterfall archived
✅ **Git History Backed Up**: Bundle + full directory backup created
✅ **Documentation Created**: This file + MIGRATION-INFO.txt

### Optional: Remove Old Backups (After Verification)

Once you confirm everything works, you can remove the old backups:

```bash
# NOT recommended until you're confident
rm -rf ~/Code/woolly.full-backup/
rm -rf ~/Code/woolly-archive-2026-02-17/
rm /tmp/woolly-git-history.bundle
```

**Keep for now** in case you need to reference old git history.

---

## Testing the Migration

### Quick Verification

```bash
# 1. Check symlink works
ls ~/Code/woolly/app/router/main.py

# 2. Verify CLAUDE.md loads
cat ~/Code/woolly/CLAUDE.md | head -5

# 3. Confirm both paths access same file
diff <(ls ~/Code/woolly/app) <(ls ~/prompthub/app)

# 4. Test app startup
cd ~/prompthub/app
uvicorn router.main:app --port 9090 &
curl http://localhost:9090/health
```

### Claude Desktop

If you've set up PromptHub in Claude Desktop:
- Symlink is transparent to Claude Desktop
- Existing client configs still work
- Run `clients/setup-claude.sh` again if needed

---

## Files Changed/Preserved

| Item | Status | Location |
|------|--------|----------|
| Python code | ✅ Preserved | `~/prompthub/app/` |
| MCP servers | ✅ Preserved | `~/prompthub/mcps/` |
| Client setup | ✅ Preserved | `~/prompthub/clients/` |
| Git history | ✅ Backed Up | `/Users/visualval/Code/woolly.full-backup/.git/` |
| Conversation history | ✅ Preserved | `~/.claude/projects/-Users-visualval--cursor-worktrees-woolly--Workspace--eoz/` |
| Old references | ✅ Forwarded | `~/Code/woolly/ → ~/prompthub/` |

---

## Troubleshooting

### Issue: "Code/woolly not found"
**Solution**: Verify symlink exists
```bash
ls -lh ~/Code/woolly
# Should show: woolly -> /Users/visualval/.local/share/prompthub
```

### Issue: "Can't find configs after migration"
**Solution**: Configs are in the same place relative to project root
```bash
cd ~/prompthub/app
cat configs/mcp-servers.json  # Still works
```

### Issue: "Claude history is missing"
**Solution**: Check both context directories
```bash
# Both point to same place now:
ls ~/.claude/projects/-Users-visualval--cursor-worktrees-woolly--Workspace--eoz/ | wc -l
ls ~/.claude/projects/-Users-visualval--local-share-prompthub/ 2>/dev/null || echo "Is symlink"

# New path should resolve to old path:
readlink ~/.claude/projects/-Users-visualval--local-share-prompthub
```

---

## Next Steps (Optional)

1. **If keeping old backups**: Move them to archival storage if space is needed
2. **If updating documentation**: Update any internal READMEs mentioning `~/Code/woolly/` to note symlink behavior
3. **If publishing**: Update any external documentation to direct users to `~/prompthub/`

---

## Questions or Issues?

All conversation history is preserved in Claude project context. The migration is completely transparent and backward-compatible.

**Key Takeaway**: You can reference the code from either path, but internally everything is now in `~/prompthub/`.
