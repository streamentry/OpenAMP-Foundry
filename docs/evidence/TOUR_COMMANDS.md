# Command Tour for New Users

A guided tour of the most important CLI commands.

## 1. Rank Candidates
```bash
openamp-foundry rank --candidates examples/sequences/demo_candidates.csv \
  --references examples/known_reference/demo_known_amps.csv \
  --out outputs/demo_ranked.jsonl --report outputs/demo_report.md
```
This scores candidates, ranks them, and generates evidence certificates.

## 2. Validate Certificates
```bash
openamp-foundry validate --certificate outputs/evidence/AMPF-000001.json \
  --schema schemas/candidate.schema.json
```
This validates a candidate's evidence certificate against the schema.

## 3. Build a Lab Pack
```bash
make lab-batch-pack
```
This creates a zip file with everything a lab partner needs.

## 4. Check Pipeline Health
```bash
make full-reproducibility-report
```
This generates a report summarizing pipeline state and readiness.
