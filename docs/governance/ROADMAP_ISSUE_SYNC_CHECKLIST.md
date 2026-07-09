# Roadmap-to-Issue Sync Checklist

This checklist ensures that items in `docs/research/ROADMAP.md` and
`docs/research/NEXT_100_PR_MAP.md` remain actionable by keeping them linked
to tracked GitHub issues or pull requests.

## Purpose

The roadmap drives research direction. Without linking roadmap items to GitHub
issues, work can stall, duplicate, or drift from the stated plan. This
checklist is run by maintainers before each release and can be validated
by the CLI tool `openamp-foundry roadmap-sync-check`.

## Sync Checklist (run before each release)

### 1. Roadmap items → Issues

For each open item in ROADMAP.md and NEXT_100_PR_MAP.md:

- [ ] Item has a corresponding open GitHub issue or PR number
- [ ] Issue title matches the roadmap item description closely
- [ ] Issue is assigned to a milestone matching the roadmap version
- [ ] Issue labels include `roadmap` and the relevant phase (e.g. `phase-j`)
- [ ] Issue body references the roadmap item by ID (e.g. `J8`)

### 2. Issues → Roadmap

For each open issue labeled `roadmap`:

- [ ] Issue maps to a specific item in ROADMAP.md or NEXT_100_PR_MAP.md
- [ ] No orphaned issues labeled `roadmap` without a matching roadmap item
- [ ] Closed issues are reflected in the roadmap as `✓` completed items

### 3. Completed items

For each completed (✓) item in ROADMAP.md:

- [ ] Corresponding GitHub issue or PR is closed
- [ ] PR number is referenced in the roadmap entry
- [ ] METRICS_CURRENT.md is updated with the version bump
- [ ] ROADMAP.md entry includes the completion date

### 4. Priority alignment

- [ ] NEXT_100_PR_MAP.md priority column (A/B/C/D) reflects current bottlenecks
- [ ] Top-priority items (A) have open issues already filed
- [ ] No item has been at priority A for more than 2 release cycles without progress

### 5. Version consistency

- [ ] ROADMAP.md versions match METRICS_CURRENT.md pipeline version
- [ ] Each version bump in ROADMAP.md has a corresponding git tag or PR
- [ ] No version appears in ROADMAP.md without a corresponding METRICS_CURRENT.md entry

## Machine Validation

Roadmap sync entries can be validated with:

```bash
openamp-foundry roadmap-sync-check --entry-json '{\"item_id\": \"J8\", ...}'
```

See `src/openamp_foundry/governance/roadmap_sync.py` for the RoadmapSyncEntry schema.

## When to Run

- Before every minor version release
- When adding new items to NEXT_100_PR_MAP.md
- When closing issues labeled `roadmap`
- Monthly, as part of the governance review cycle

## Linked Policies

- [docs/research/ROADMAP.md](../research/ROADMAP.md) — live roadmap
- [docs/research/NEXT_100_PR_MAP.md](../research/NEXT_100_PR_MAP.md) — backlog
- [docs/evidence/METRICS_CURRENT.md](../evidence/METRICS_CURRENT.md) — version history
- [GOVERNANCE.md](../../GOVERNANCE.md) — governance structure
- [docs/governance/MAINTAINER_ROTATION_PLAN.md](MAINTAINER_ROTATION_PLAN.md) — maintainer responsibilities
