# Archive

Completed implementation plans, superseded docs, and historical reviews.
Date-prefixed for chronological ordering.

Documents are archived instead of deleted to maintain institutional knowledge and provide context for future troubleshooting.

> Historical only: documents in this folder preserve the terminology, model
> names, routes, and architecture assumptions that were current when they were
> written. Do not treat archived docs as the source of truth for current
> PromptHub behavior.

## Contents

| Date | Document | Origin |
|------|----------|--------|
| 2026-01-30 | [integration-fixes](2026-01-30-integration-fixes.md) | Phase 3 integration fixes |
| 2026-02-03 | [agents-md-treatment](2026-02-03-agents-md-treatment.md) | Agents.md configuration |
| 2026-02-03 | [awesome-copilot-installation](2026-02-03-awesome-copilot-installation.md) | Copilot setup |
| 2026-02-03 | [enhancement-middleware-review](2026-02-03-enhancement-middleware-review.md) | Middleware review |
| 2026-02-10 | [test-completion-and-reorganization](2026-02-10-test-completion-and-reorganization.md) | Test suite restructuring |
| 2026-02-13 | [copilot-processing-archived](2026-02-13-copilot-processing-archived.md) | Task tracking (completed) |
| 2026-02-14 | [doc-tour-skill](2026-02-14-doc-tour-skill.md) | Documentation skill spec |
| 2026-02-17 | [keyring-integration-complete](2026-02-17-keyring-integration-complete.md) | Keyring migration (completed) |
| 2026-02-17 | [keyring-vs-security-cli](2026-02-17-keyring-vs-security-cli.md) | Keyring vs CLI decision record |
| 2026-02-17 | [secrets-docs-fixes](2026-02-17-secrets-docs-fixes.md) | Secrets documentation fixes |
| 2026-02-17 | [woolly-migration](2026-02-17-woolly-migration.md) | Woolly migration notes |
| 2026-02-28 | [async-audit](2026-02-28-async-audit.md) | Async/HTTP audit findings |
| 2026-02-28 | [audit-code-review](2026-02-28-audit-code-review.md) | Audit system code review |
| 2026-02-28 | [security-fixes](2026-02-28-security-fixes.md) | Security fix implementation |

## Retention Guidance

Keep archived documents when they answer one of these questions:
- Why does current code or naming look strange?
- What failed before, and what symptom should we recognize quickly?
- What tradeoff or migration decision still affects current behavior?

Lower-value archive material:
- completed task trackers with no enduring rationale
- implementation logs that duplicate `CHANGELOG.md`
- setup notes for workflows that no longer exist and are not referenced

Current keepers:
- decision and migration history such as keyring, async audit, security fixes,
  enhancement reviews, and integration fixes
- narrowly scoped historical analyses that explain present constraints

Best drop or condense first if you want a thinner archive:
- [`2026-02-13-copilot-processing-archived.md`](/Users/visualval/.local/share/prompthub/docs/archive/2026-02-13-copilot-processing-archived.md)
- [`2026-02-17-woolly-migration.md`](/Users/visualval/.local/share/prompthub/docs/archive/2026-02-17-woolly-migration.md)
- [`2026-02-03-awesome-copilot-installation.md`](/Users/visualval/.local/share/prompthub/docs/archive/2026-02-03-awesome-copilot-installation.md)

Those are not wrong, but they are mostly project-history logs rather than
decision records.
