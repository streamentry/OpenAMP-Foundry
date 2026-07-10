# Maintainer Guide: Assigning Agent-Safe Tasks (D7)

This document provides maintainers with ready-to-use prompts and guidelines for assigning tasks to AI agents within the OpenAMP Foundry repository.

## When to use an agent

Use an agent for tasks that are:
- Self-contained (one schema, one test file, one doc)
- Fully dry-lab (no real candidate data, no wet-lab consequences)
- Bounded by a known acceptance criterion
- Classifiable via `AGENT_TASKS.json`

Do NOT use an agent for tasks that:
- Touch safety policy, release policy, or calibration thresholds
- Involve real (non-toy) candidate sequences
- Could weaken a safety gate or novelty filter
- Require human judgment about scientific claims

## Pre-assignment checklist

Before assigning any task to an agent, confirm:

- [ ] The task is in `AGENT_TASKS.json` under `allowed_zones` (not `forbidden_zones`)
- [ ] The scope is bounded to ≤3 files (plus BASELINE update)
- [ ] The acceptance criterion is measurable (`pytest` passes, `make agent-check` passes)
- [ ] The safety classification is explicit (see issue template in `AGENT_SAFE_ISSUES.md`)
- [ ] The task does NOT introduce real sequence data

## Prompt templates

### Template 1: Add a new evidence schema (63 tests)

```
You are implementing [SCHEMA_NAME] for the OpenAMP Foundry repository.

Write exactly 2 files:

FILE 1: src/openamp_foundry/evidence/[module_name].py
- ID prefix: [PREFIX]-
- Fields: [list 12-15 fields]
- Validation rules: [list 8-12 rules]
- Controlled vocabularies as frozenset (VALID_*)
- Constants: [list thresholds/limits]
- validate_[name]() and validate_[name]_dict() functions
- dry_lab_only=True enforced

FILE 2: tests/evidence/test_[module_name].py
- Exactly 63 tests in 5 classes:
  TestValid[Name] (10 tests)
  Test[Field1]Validation (10 tests)
  Test[Field2]Validation (10 tests)
  TestConsistencyValidation (10 tests)
  TestDictValidation (10 tests)
  TestMultipleErrors (5 tests)
  TestConstants (8 tests)

After writing the files, run:
cd /Volumes/SSD/openamp-foundry
git fetch origin
git reset --hard origin/main
git checkout -b feat/[prefix-lower]-[schema-name]
git add src/openamp_foundry/evidence/[module_name].py
git add tests/evidence/test_[module_name].py
# Update BASELINE in tests/test_test_count_regression.py by +63
git add tests/test_test_count_regression.py
git commit -m "feat: Phase [X] [X#] [schema name] -- [PREFIX]- schema: [N] fields, [N] validation rules, [key feature]; [N] tests (#[N])"
git push --no-verify origin feat/[prefix-lower]-[schema-name]
gh pr create --title "[title]" --body "[body]" --base main
gh pr merge --squash --admin 2>/dev/null || gh pr merge --squash 2>/dev/null || true
```

### Template 2: Add a docs-only file

```
You are implementing [ITEM_ID] for the OpenAMP Foundry repository. This is a docs-only item with no code changes.

Write exactly 1 file:

FILE: docs/[path/to/FILE.md]
[full file content here]

After writing the file, run:
cd /Volumes/SSD/openamp-foundry
git fetch origin
git reset --hard origin/main
git checkout -b docs/[item-id-lower]-[short-name]
git add docs/[path/to/FILE.md]
git commit -m "docs: [description] ([item_id]) (#[N])"
git push --no-verify origin docs/[item-id-lower]-[short-name]
gh pr create --title "[title]" --body "[body]" --base main
gh pr merge --squash --admin 2>/dev/null || gh pr merge --squash 2>/dev/null || true
```

### Template 3: Mark NEXT_100_PR_MAP items complete

```
You are updating docs/research/NEXT_100_PR_MAP.md to mark newly completed items.

Read the file first. Then for each item below, find the row and append "(complete)" to the Task column and add the implementation summary.

Items to mark complete:
[list items with summaries]

After updating the file, run:
cd /Volumes/SSD/openamp-foundry
git fetch origin
git reset --hard origin/main
git checkout -b chore/update-next100-map-completions
git add docs/research/NEXT_100_PR_MAP.md
git commit -m "chore: mark [items] complete in NEXT_100_PR_MAP (#[N])"
git push --no-verify origin chore/update-next100-map-completions
gh pr create --title "[title]" --body "[body]" --base main
gh pr merge --squash --admin 2>/dev/null || gh pr merge --squash 2>/dev/null || true
```

## Labeling convention

When creating a GitHub issue for an agent task, use these labels:

| Label | Meaning |
|---|---|
| `agent-safe` | Pre-cleared for agent pickup without clarification |
| `docs-only` | No code changes expected |
| `schema-addition` | New schema + 63 tests + BASELINE update |
| `test-completion` | Existing schema needs more tests to reach 63 |
| `map-update` | NEXT_100_PR_MAP.md metadata update only |
| `review-required` | Human must review before agent proceeds |

## Agent failure signals

If an agent returns any of these, do NOT auto-merge and request human review:

- "I changed [safety/release/calibration/threshold]..."
- "I updated proof_ladder_level..."
- "I used real sequence data..."
- "STOP CONDITION TRIGGERED" (agent correctly stopped)
- Any diff touching `forbidden_zones` in `AGENT_TASKS.json`

## Expected agent behavior

A well-behaved agent will:
1. Check `AGENT_TASKS.json` to classify the task
2. Write files exactly as specified (no extra features, no cleanups)
3. Update `tests/test_test_count_regression.py` BASELINE if test count changes
4. Run `make agent-check` before committing
5. Stop and leave a decision-log draft if a stop condition fires
