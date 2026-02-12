# Guides Folder Reorganization Plan

**Date:** 2026-02-03
**Purpose:** Separate user-facing guides from engineering documentation
**Status:** 📋 Proposed - Ready for Implementation

---

## Current State Analysis

### Existing Structure (Flat - 17 files)

```
guides/
├── app-configs.md                    [492 lines] - Configuration reference
├── claude-desktop-integration.md     [656 lines] - Integration guide
├── comfyui-integration.md            [ 92 lines] - Integration guide
├── comparison-table.md               [227 lines] - Comparison reference
├── copilot-agents.md                 [ 42 lines] - ⚠️ Duplicate of .github content
├── design-prompts.md                 [291 lines] - ⚠️ Engineering content
├── docker-guide.md                   [197 lines] - Deployment guide
├── figma-integration.md              [132 lines] - Integration guide
├── getting-started.md                [775 lines] - Onboarding guide
├── index.md                          [377 lines] - Navigation hub
├── keychain-setup.md                 [253 lines] - Setup guide
├── keyring-migration-guide.md        [348 lines] - Migration guide
├── keyring-vs-security-cli.md        [295 lines] - Technical comparison
├── launchagent-setup.md              [338 lines] - Setup guide
├── raycast-integration.md            [809 lines] - Integration guide
├── testing-integrations.md           [1059 lines] - Testing procedures
└── vscode-integration.md             [781 lines] - Integration guide
```

### Issues Identified

1. **❌ Mixed Audiences**
   - User guides mixed with technical/engineering content
   - Setup guides alongside comparison documents
   - Integration guides alongside development guides

2. **❌ Misplaced Content**
   - `copilot-agents.md` - Duplicates `.github/agents/` content
   - `design-prompts.md` - Engineering/development content, not user guide
   - `keyring-vs-security-cli.md` - Technical comparison, better in docs

3. **❌ Flat Structure**
   - No hierarchy or categorization
   - Hard to find related content
   - Unclear progression path

4. **❌ Unclear Purpose**
   - What's a "guide" vs "reference" vs "tutorial"?
   - No distinction between beginner and advanced content

---

## Proposed Structure

### New Organization (Hierarchical)

```
guides/                                  # USER-FACING ONLY
│
├── README.md                            # Guide index (renamed from index.md)
│
├── 01-getting-started/                  # ONBOARDING
│   ├── README.md                        # Quick start overview
│   ├── installation.md                  # Installation steps (extracted from getting-started.md)
│   ├── first-setup.md                   # Initial configuration (extracted from getting-started.md)
│   ├── verification.md                  # Health checks (extracted from getting-started.md)
│   └── next-steps.md                    # What to do after installation
│
├── 02-core-setup/                       # ESSENTIAL CONFIGURATION
│   ├── README.md                        # Setup overview
│   ├── launchagent.md                   # Auto-start on login (from launchagent-setup.md)
│   ├── keychain.md                      # Secure credentials (from keychain-setup.md)
│   └── docker.md                        # Docker deployment (from docker-guide.md)
│
├── 03-integrations/                     # CLIENT CONNECTIONS
│   ├── README.md                        # Integration overview
│   ├── claude-desktop.md                # Claude Desktop (from claude-desktop-integration.md)
│   ├── vscode.md                        # VS Code/Cline/Claude Code (from vscode-integration.md)
│   ├── raycast.md                       # Raycast launcher (from raycast-integration.md)
│   ├── figma.md                         # Figma design (from figma-integration.md)
│   ├── comfyui.md                       # ComfyUI images (from comfyui-integration.md)
│   └── quick-config.md                  # Quick reference for all (from app-configs.md)
│
├── 04-workflows/                        # PRACTICAL USAGE PATTERNS (NEW)
│   ├── README.md                        # Workflow overview
│   ├── code-development.md              # VS Code + enhancement workflow
│   ├── content-creation.md              # Claude Desktop + research workflow
│   ├── quick-commands.md                # Raycast + CLI workflow
│   └── design-to-code.md                # Figma → Claude workflow
│
├── 05-testing/                          # VALIDATION & TROUBLESHOOTING
│   ├── README.md                        # Testing overview
│   ├── integration-tests.md             # Comprehensive tests (from testing-integrations.md)
│   ├── troubleshooting.md               # Common issues (NEW)
│   └── health-monitoring.md             # Dashboard usage (NEW)
│
└── 06-migration/                        # UPGRADE GUIDES
    ├── README.md                        # Migration overview
    └── keyring-migration.md             # Security CLI → keyring (from keyring-migration-guide.md)
```

### Content Moving to `docs/` (Engineering/Technical)

```
docs/
│
├── comparisons/                         # TECHNICAL COMPARISONS (NEW CATEGORY)
│   ├── README.md
│   ├── prompthub-vs-alternatives.md      # From guides/comparison-table.md
│   └── keyring-vs-security-cli.md       # From guides/keyring-vs-security-cli.md
│
└── development/                         # DEVELOPMENT GUIDES (NEW CATEGORY)
    ├── README.md
    ├── prompt-design.md                 # From guides/design-prompts.md
    └── copilot-workflows.md             # From guides/copilot-agents.md (or delete if duplicate)
```

---

## File-by-File Treatment Plan

### Phase 1: Restructure User Guides (guides/)

#### 01-getting-started/

| New File | Source | Action |
|----------|--------|--------|
| `README.md` | New | Overview of getting started path |
| `installation.md` | `getting-started.md` (lines 1-250) | Extract installation steps |
| `first-setup.md` | `getting-started.md` (lines 251-500) | Extract configuration |
| `verification.md` | `getting-started.md` (lines 501-775) | Extract health checks |
| `next-steps.md` | New | Guide to next actions |

#### 02-core-setup/

| New File | Source | Action |
|----------|--------|--------|
| `README.md` | New | Setup path overview |
| `launchagent.md` | `launchagent-setup.md` | Rename + move |
| `keychain.md` | `keychain-setup.md` | Rename + move |
| `docker.md` | `docker-guide.md` | Rename + move |

#### 03-integrations/

| New File | Source | Action |
|----------|--------|--------|
| `README.md` | New | Integration overview + decision tree |
| `claude-desktop.md` | `claude-desktop-integration.md` | Rename + move |
| `vscode.md` | `vscode-integration.md` | Rename + move |
| `raycast.md` | `raycast-integration.md` | Rename + move |
| `figma.md` | `figma-integration.md` | Rename + move |
| `comfyui.md` | `comfyui-integration.md` | Rename + move |
| `quick-config.md` | `app-configs.md` | Rename + move |

#### 04-workflows/ (NEW)

| New File | Source | Action |
|----------|--------|--------|
| `README.md` | New | Explain workflow concept |
| `code-development.md` | New | VS Code best practices |
| `content-creation.md` | New | Claude Desktop best practices |
| `quick-commands.md` | New | Raycast best practices |
| `design-to-code.md` | New | Figma workflow |

#### 05-testing/

| New File | Source | Action |
|----------|--------|--------|
| `README.md` | New | Testing overview |
| `integration-tests.md` | `testing-integrations.md` | Rename + move |
| `troubleshooting.md` | New + extract | Common issues from all guides |
| `health-monitoring.md` | New | Dashboard usage guide |

#### 06-migration/

| New File | Source | Action |
|----------|--------|--------|
| `README.md` | New | Migration guide overview |
| `keyring-migration.md` | `keyring-migration-guide.md` | Rename + move |

### Phase 2: Move Engineering Content (docs/)

#### docs/comparisons/ (NEW)

| New File | Source | Action |
|----------|--------|--------|
| `README.md` | New | Comparison overview |
| `prompthub-vs-alternatives.md` | `guides/comparison-table.md` | Move + enhance |
| `keyring-vs-security-cli.md` | `guides/keyring-vs-security-cli.md` | Move |

#### docs/development/ (NEW)

| New File | Source | Action |
|----------|--------|--------|
| `README.md` | New | Development guide overview |
| `prompt-design.md` | `guides/design-prompts.md` | Move + enhance |

### Phase 3: Cleanup

| File | Action | Reason |
|------|--------|--------|
| `guides/copilot-agents.md` | DELETE | Duplicates `.github/agents/` content |
| `guides/index.md` | RENAME → `README.md` | Standard convention |

---

## Content Enhancement Strategy

### Rewrite Philosophy

When rewriting guides as co-authors, focus on:

1. **Educational Voice**
   - Explain the "why" behind each step
   - Provide context for configuration choices
   - Link concepts to practical outcomes

2. **Progressive Disclosure**
   - Start with simplest case
   - Add complexity gradually
   - Mark advanced sections clearly

3. **Learning Outcomes**
   - Each guide section has clear objective
   - Include "What you'll learn" boxes
   - Add "Key Takeaways" summaries

4. **Practical Examples**
   - Real-world scenarios
   - Before/after comparisons
   - Common pitfalls and solutions

### Template Structure (for each guide)

```markdown
# Guide Title

> **What you'll learn:** Brief description of outcomes

## Overview
- What this guide covers
- Prerequisites
- Estimated time

## Concepts
Brief explanation of key concepts (educational)

## Step-by-Step Instructions
Clear, numbered steps with explanations

## Understanding the Configuration
Deep dive into what each setting does (educational)

## Common Use Cases
Real-world scenarios and examples

## Troubleshooting
Common issues and solutions

## Key Takeaways
- Bullet point summary
- Next steps
- Related guides

---
**Questions?** Link to discussions/issues
```

---

## Migration Strategy

### Option 1: Big Bang Migration (RECOMMENDED)

**Timeline:** 1-2 sessions
**Approach:** Complete restructure in one go

**Advantages:**
- ✅ Clean break, no confusion
- ✅ All links updated at once
- ✅ Immediate benefit of new structure

**Process:**
1. Create new directory structure
2. Move/rename files in bulk
3. Update all cross-references
4. Update documentation index
5. Add redirects in old location

### Option 2: Gradual Migration

**Timeline:** 2-3 weeks
**Approach:** Migrate one category at a time

**Advantages:**
- ✅ Lower risk
- ✅ Can test each section
- ✅ Easier to roll back

**Disadvantages:**
- ❌ Temporary inconsistency
- ❌ More complex link management
- ❌ Users see incomplete structure

---

## Link Update Requirements

### Files Requiring Link Updates

**Internal (within guides/):**
- All `*.md` files cross-reference each other
- `README.md` (formerly `index.md`) has comprehensive index

**External (in other directories):**
- `README.md` (root) - References guides
- `CLAUDE.md` - References guides
- `Copilot-Processing.md` - References guides
- `docs/DOCUMENTATION-INDEX.md` - Main doc index
- `.github/copilot-instructions.md` - References guides
- `.github/awesome-copilot-index.md` - References guides

### Automated Link Checking

```bash
# Find all references to guides/
grep -r "guides/" . --include="*.md" | grep -v ".git"

# Check for broken links after migration
find . -name "*.md" -exec markdown-link-check {} \;
```

---

## Benefits of New Structure

### For Users

| Before | After |
|--------|-------|
| ❌ Unclear where to start | ✅ Clear 01-getting-started path |
| ❌ All guides same level | ✅ Progressive structure (01 → 06) |
| ❌ Mixed technical content | ✅ Pure user focus |
| ❌ Hard to find related guides | ✅ Categorized by purpose |

### For Maintainers

| Before | After |
|--------|-------|
| ❌ Flat structure hard to navigate | ✅ Hierarchical organization |
| ❌ Unclear content ownership | ✅ Clear categories |
| ❌ Duplication across files | ✅ DRY principle |
| ❌ Hard to add new guides | ✅ Clear placement rules |

### For Documentation Quality

| Before | After |
|--------|-------|
| ❌ Inconsistent format | ✅ Template-driven consistency |
| ❌ Varying detail levels | ✅ Standard structure |
| ❌ No learning objectives | ✅ Educational framework |
| ❌ Missing troubleshooting | ✅ Dedicated troubleshooting section |

---

## Implementation Checklist

### Pre-Migration

- [ ] Backup current guides/ directory
- [ ] Document all existing cross-references
- [ ] Create new directory structure
- [ ] Write README.md for each new category

### Migration

- [ ] **Phase 1:** Restructure user guides
  - [ ] Create 01-getting-started/
  - [ ] Create 02-core-setup/
  - [ ] Create 03-integrations/
  - [ ] Create 04-workflows/ (new content)
  - [ ] Create 05-testing/
  - [ ] Create 06-migration/

- [ ] **Phase 2:** Move engineering content
  - [ ] Create docs/comparisons/
  - [ ] Create docs/development/
  - [ ] Move comparison files
  - [ ] Move development files

- [ ] **Phase 3:** Update links
  - [ ] Update guides/README.md
  - [ ] Update root README.md
  - [ ] Update CLAUDE.md
  - [ ] Update Copilot-Processing.md
  - [ ] Update docs/DOCUMENTATION-INDEX.md
  - [ ] Update .github/ references

### Post-Migration

- [ ] Run link checker
- [ ] Test navigation flow
- [ ] Update search indices
- [ ] Create redirect notices in old locations
- [ ] Update git history documentation

---

## Rewrite Priority Order

### Immediate (Pre-Middleware Development)

1. **01-getting-started/** - Users need this first
2. **03-integrations/** - Core value proposition
3. **guides/README.md** - Navigation hub

### During Middleware Development

1. **04-workflows/** - Can write as we learn
2. **05-testing/** - Test new middleware features
3. **02-core-setup/** - Refine based on experience

### Post-Middleware

1. **06-migration/** - Final polish
2. **docs/comparisons/** - Technical deep dives
3. **docs/development/** - For contributors

---

## Metrics for Success

### Quantitative

- [ ] All links working (0 broken links)
- [ ] Clear path from 01 → 06 (sequential flow)
- [ ] Average guide reading time < 15 minutes
- [ ] 90%+ guides follow template structure

### Qualitative

- [ ] User can find appropriate guide in < 30 seconds
- [ ] Each guide has clear learning objective
- [ ] Troubleshooting covers 80%+ common issues
- [ ] Workflow guides show real-world value

---

## Next Steps

### Decision Required

**Approve migration strategy:**
- [ ] Option 1: Big Bang (recommended)
- [ ] Option 2: Gradual
- [ ] Option 3: Custom hybrid

**Timeline:**
- Pre-Middleware: Restructure (2-3 hours)
- During Middleware: Rewrite collaboratively
- Post-Middleware: Polish and enhance

**Co-authoring Approach:**
- Work through each guide section-by-section
- You provide domain expertise, I provide structure/clarity
- Iterative refinement based on your feedback
- Focus on educational value and comprehension

---

## References

- **Current Index:** [guides/index.md](../../guides/index.md)
- **Documentation Index:** [docs/DOCUMENTATION-INDEX.md](../DOCUMENTATION-INDEX.md)
- **Similar Projects:** Explore how projects like [Next.js](https://nextjs.org/docs), [FastAPI](https://fastapi.tiangolo.com/tutorial/), and [Stripe](https://stripe.com/docs) structure their guides

---

**Plan Status:** 📋 Ready for Approval
**Estimated Effort:** 2-3 hours (restructure) + ongoing (rewrites)
**Risk Level:** Low (can rollback via git)
**User Impact:** High (significantly improved discoverability)
