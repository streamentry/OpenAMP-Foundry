# Long-Term Archival Format Specification

This document specifies how OpenAMP evidence artifacts should be packaged for long-term archival — surviving software churn, dependency rot, and institutional knowledge loss.

An archive that requires OpenAMP to be installed to read is not an archive. The goal is a package that a researcher with no prior OpenAMP knowledge can open and understand in 2030 or 2040.

## Archival principles

1. **Format stability over convenience.** Prefer formats that will be readable without the original software: JSON, CSV, FASTA, plain text, and PDF.
2. **No implicit external dependencies.** An archive must be self-contained. It must not reference schemas or validation scripts by URL without also including the content locally.
3. **Human-readable summaries alongside machine-readable data.** Every machine-readable artifact (`.json`, `.jsonl`) must have a companion `.md` or `.txt` summary that explains what it contains.
4. **Version pinning.** Every archive records the exact tool version and commit SHA that produced it.
5. **Checksums.** Every file in the archive has a SHA-256 checksum in `checksums.sha256`.

## Recommended archive format

A complete OpenAMP evidence archive is a directory tree:

```
openamp-archive-<VERSION>-<DATE>/
├── README.md                          # Plain-English introduction
├── checksums.sha256                   # SHA-256 checksum of every file in this archive
├── VERSION.txt                        # OpenAMP version and commit SHA
├── LICENSE.txt                        # Copy of the project license (Apache-2.0)
│
├── candidates/
│   ├── candidates.fasta               # All nominated candidates in FASTA format
│   ├── candidates.csv                 # One row per candidate: ID, sequence, scores
│   └── candidates.md                  # Human-readable candidate summary table
│
├── evidence/
│   ├── certificates/
│   │   ├── <CERT_ID>.json             # One file per certificate
│   │   └── certificates_summary.md   # Table of all certificates and proof-ladder levels
│   ├── release_manifest.json          # RMF- release manifest
│   ├── release_manifest.md            # Human-readable version of the manifest
│   └── negative_results/
│       ├── <NRR_ID>.json              # One file per negative result record
│       └── negative_results_summary.md
│
├── benchmarks/
│   ├── benchmark_cards.json           # All BMC- benchmark card definitions
│   ├── benchmark_results.json         # Benchmark run outputs
│   └── benchmarks_summary.md          # Benchmark honesty summary with caveats
│
├── calibration/
│   ├── calibration_cycle.json         # CCS- calibration cycle summary
│   ├── calibration_cycle.md           # Human-readable calibration summary
│   └── recalibration_history.jsonl    # Append-only log of calibration events
│
├── schemas/
│   ├── <schema_name>.schema.json      # Local copies of all JSON schemas used
│   └── schemas_index.md               # Index of schemas with $id and version
│
└── provenance/
    ├── pipeline_run.json              # Pipeline run ID, parameters, environment
    ├── pipeline_run.md                # Human-readable run summary
    └── cross_repo_links.json          # CRT- cross-repo traceability records
```

## Required files

Every archive must include:

| File | Format | Required | Purpose |
|------|--------|----------|---------|
| `README.md` | Markdown | Yes | Plain-English introduction |
| `checksums.sha256` | Text | Yes | Integrity verification |
| `VERSION.txt` | Text | Yes | Version and commit pinning |
| `LICENSE.txt` | Text | Yes | Reuse rights |
| `candidates/candidates.fasta` | FASTA | Yes | Canonical candidate sequences |
| `candidates/candidates.csv` | CSV | Yes | Candidate scores and metadata |
| `evidence/release_manifest.json` | JSON | Yes | Machine-readable release manifest |
| `benchmarks/benchmarks_summary.md` | Markdown | Yes | Benchmark honesty summary |

## Required fields in `VERSION.txt`

```
openamp_foundry_version: v<MAJOR>.<MINOR>.<PATCH>
commit_sha: <40-char SHA>
archive_date: <ISO 8601 date>
python_version: <e.g. 3.12.0>
schema_version: <e.g. 1.0>
produced_by: openamp_foundry.evidence.release_manifest
```

## `checksums.sha256` format

One line per file, SHA-256 hash followed by two spaces followed by the relative path:

```
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  README.md
...
```

Compute with:

```bash
find . -type f | sort | xargs sha256sum > checksums.sha256
```

Verify with:

```bash
sha256sum --check checksums.sha256
```

## Format constraints

### JSON files

- UTF-8 encoded.
- No trailing commas (strict JSON).
- Indented with 2 spaces.
- All JSON files must include a `"_schema_version"` key at the top level.
- All JSON files that represent artifacts must include `"dry_lab_only": true`.

### CSV files

- UTF-8 encoded.
- First row is a header.
- Fields that may contain commas are double-quoted.
- No BOM.

### FASTA files

- Standard FASTA: `>id description` header, sequence in uppercase, 60-character line wrap.
- Each entry must have a `;` comment line before it: `; candidate_id=<ID> dry_lab_only=true`.

### Markdown files

- UTF-8, standard CommonMark.
- Must begin with a heading that includes the archive date and version.
- Human summaries must include a statement that artifacts are computational nominees only.

## Anti-rot guarantees

An archive is not archival if it silently fails to load. To prevent rot:

1. **No import from `openamp_foundry`** in any file included in the archive. The archive is read-only data.
2. **No symlinks** in the archive root.
3. **No binary files** except a compressed version of the entire archive (`.tar.gz`).
4. **All schema files included locally** in `schemas/`. Do not rely on external URLs.
5. **The `README.md` must explain how to validate the checksums** without any special software beyond `sha256sum`.

## Compression

The archive directory should be compressed to:

```
openamp-archive-<VERSION>-<DATE>.tar.gz
```

Using:

```bash
tar -czf openamp-archive-<VERSION>-<DATE>.tar.gz openamp-archive-<VERSION>-<DATE>/
```

Do not use `.zip` (platform line-ending inconsistencies affect checksum verification).

## What is NOT in the archive

The archive does not include:

- Python source code or pip packages.
- Raw lab result files that contain PII or unpublished wet-lab data.
- Intermediate pipeline outputs that are derivable from the included files.
- Any file that requires OpenAMP to parse.

## Agent rules

An agent MUST NOT:
- Place Python `import` statements in archive content files.
- Include files that require internet access to validate.
- Include files with embedded credentials, API keys, or internal hostnames.
- Change the `checksums.sha256` format without updating this document.

An agent MAY:
- Add optional subdirectories to the archive structure (e.g., `external_reviews/`).
- Compress the archive as `.tar.gz` after all required files are present.
- Validate checksums during CI as a smoke test.
