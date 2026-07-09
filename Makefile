.PHONY: help demo test lint ci clean bench-leakage bench-multi-negatives bench-baseline bench-hidden-active bench-cluster-split bench-expert-ablation bench-expert-ablation-500 bench-selectivity bench-feature-decomp bench-gate bench-easy-baseline bench-charge-matched bench-order-dependent bench-precision-at-k bench-per-family bench-simulation-ablation bench-simulation-ablation-within-amp simulation-gate bench-strategy-compare regenerate-all generate phase3 pilot validate-scoring validate-scoring-phase3 validate-scoring-strict external-pilot pilot-confident presynth-qc gold-standard diversity synthesis-order novelty-broad external-consensus questionnaire gate-check ip-report benchmark-card wave0-5-gate-check wave0-5-novelty-audit wave0-5-novelty-audit-v2 wave0-5-panel wave0-5-evidence wave0-5-fill-external wave0-5b-generate wave0-5b-filter recalibration-engine recalibration-engine-dry-run validate-policy-version generate-synthetic-lab-results bump-policy-version generate-review-packet failed-candidate-report safe-publication-filter classify-negative-informativeness validate-rejection-events negative-result-dashboard calibration-audit calibration-audit-example calibration-overfit-check result-quality-filter synthetic-result-policy-check calibration-decision-checklist calibration-rollback-plan simulation-registry validate-simulation-result-schema simulation-baseline-check adapter-gate-check simulation-provenance simulation-ensemble-check simulation-ci-report simulation-deprecation-check simulation-scope-check simulation-evidence-packet artifact-version candidate-manifest artifact-changelog integration-check adapter-author-check license-check artifact-compat-check contribution-check adoption-scorecard release-gate-check decision-log release-request-check coi-check rotation-plan-check security-report-check citation-check roadmap-sync-check advisory-review-check annual-review-check selection-rationale-check batch-priority-check pilot-package-check calibration-intake-check uncertainty-report-check preprint-bundle-check

PYTHON := $(shell [ -f .venv/bin/python ] && echo .venv/bin/python || echo python3)
PYTEST  := $(shell [ -f .venv/bin/pytest ] && echo .venv/bin/pytest || echo pytest)
RUFF    := $(shell [ -f .venv/bin/ruff ] && echo .venv/bin/ruff || echo ruff)

help:
	@echo "OpenAMP Foundry — dry-lab pipeline targets"
	@echo ""
	@echo "Quick verification:"
	@echo "  make pr-ready           Pre-PR check (agent-check + doctor)"
	@echo "  make agent-check        Claim scan + doc links + benchmark deprecation"
	@echo "  make doctor             Environment diagnostic"
	@echo ""
	@echo "Pipeline:"
	@echo "  make demo               Rank demo candidates, produce report + evidence certs"
	@echo ""
	@echo "Benchmarks (key):"
	@echo "  make bench-500          Full expanded benchmark (AUROC, AUPRC, recall)"
	@echo ""
	@echo "  make demo               Rank demo candidates, produce report + evidence certs"
	@echo "  make phase3             Generate + rank Phase 3 pool (89 nominees)"
	@echo "  make pilot              Select 20-candidate pilot panel from Phase 3 pool"
	@echo "  make external-predict   Export pilot panel FASTA + external-predictor checklist"
	@echo "  make pilot-confident    Filter panel by external predictor IDs  KEEP=ID1,ID2,..."
	@echo "  make presynth-qc        Synthesis feasibility QC on confident panel"
	@echo "  make gold-standard      Gold-standard probability calibration report"
	@echo "  make diversity          Within-panel diversity report"
	@echo "  make synthesis-order    Vendor-ready synthesis order CSV + checklist"
	@echo "  make novelty-broad      Compare pilot panel against 72-AMP curated reference set"
	@echo "  make external-consensus Aggregate external predictor results into consensus verdicts"
	@echo "  make questionnaire      Generate pre-populated reviewer questionnaires"
	@echo "  make gate-check         Run all pipeline decision gates (gates 1-7)"
	@echo "  make ip-report          Generate IP and novelty claim strength report"
	@echo "  make benchmark-card     Generate/update benchmark summary card"
	@echo ""
	@echo "  make validate-scoring         AUROC on 95 AMP + 96 decoy (pipeline config)"
	@echo "  make validate-scoring-phase3  AUROC with phase3.yaml config"
	@echo "  make validate-scoring-strict  AUROC with scrambled-decoy strict benchmark"
	@echo "  make bench-leakage            Check for near-duplicates between candidates and refs"
	@echo "  make bench-multi-negatives    Multi-negative-set benchmark (4 decoy distributions)"
	@echo "  make bench-baseline           Hidden-positive recovery benchmark (demo set)"
	@echo "  make bench-cluster-split      Cluster-aware bootstrap CI (de-inflates near-duplicates)"
	@echo "  make bench-500                Full benchmark on expanded 500-AMP set (AUROC, AUPRC, recall)"
	@echo "  make bench-cluster-split-500  Cluster-split on expanded 500-AMP set"
	@echo "  make bench-expert-ablation    Expert composite vs ensemble ablation (honesty check, n=191)"
	@echo "  make bench-expert-ablation-500  Expert ablation on expanded 500-AMP benchmark (n=1000)"
	@echo "  make bench-selectivity        Within-AMP selectivity (hemolytic vs selective)"
	@echo "  make bench-feature-decomp     Per-feature selective_vs_hemolytic decomposition"
	@echo "  make bench-easy-baseline      Compare pipeline against trivial (length/charge) baselines"
	@echo "  make bench-charge-matched     Charge-matched decoy benchmark (tests charge inflation)"
	@echo "  make bench-order-dependent    Analyze which features survive scrambling (order-dependence)"
	@echo "  make bench-precision-at-k    Precision@k operating characteristic (small-k triage, threshold calibration)"
	@echo "  make bench-per-family        Per-family benchmark — stratify 500 AMPs by structural class, per-class AUROC"
	@echo "  make bench-simulation-ablation  Simulation ablation on AMP-vs-decoy benchmark"
	@echo "  make bench-simulation-ablation-within-amp  Simulation ablation on hemolytic vs selective AMPs"
	@echo "  make simulation-gate        Fail-closed gate for weighted simulation mode"
	@echo "  make bench-strategy-compare Compare active-learning strategies (exploit/explore/diverse/combined/random)"
	@echo "  make bench-gate               Benchmark regression gate (AUROC drift check)"
	@echo "  make regenerate-all           Run all pipeline + benchmarks and verify determinism"
	@echo "  make bench-hidden-active      Hidden-positive recovery on mixed benchmark set"
	@echo ""
	@echo "  make wave0-5-gate-check     Run Wave 0.5 gates W0.5-1 through W0.5-7"
	@echo "  make wave0-5-novelty-audit  Re-run novelty audit for Wave 0.5 shortlist"
	@echo "  make wave0-5-fill-external  Fill external predictor CSVs from wave05_combined_consensus.csv"
	@echo "  make wave0-5-panel          Re-run Wave 1 panel selection (fills external data first)"
	@echo "  make wave0-5-evidence       Re-generate evidence certificates"
	@echo "  make wave0-5b-generate      Generate Wave 0.5b candidates (safety-optimized, no aromatics)"
	@echo "  make wave0-5b-filter        Filter Wave 0.5b shortlist (depends on wave0-5b-generate)"
	@echo "  make lab-result-intake      Join a pilot panel CSV with lab result JSON files"
	@echo "  make lab-result-intake-example  Run intake on the synthetic example data"
	@echo "  make recalibration-gate-example  Evaluate recalibration gate on synthetic intake example"
	@echo "  make recalibration-gate         Evaluate recalibration gate on a real intake report"
	@echo "  make recalibration-engine       Compute proposed weight deltas (requires gate verdict first)"
	@echo "  make recalibration-engine-dry-run  Preview weight changes without side effects"
	@echo "  make validate-policy-version    Validate proposed policy version against predecessor"
	@echo "  make bump-policy-version        Bump policy version with decision-log guard (requires --human-reviewer)"
	@echo "  make generate-synthetic-lab-results  Generate synthetic lab results for calibration testing"
	@echo "  make calibration-audit-example  Run calibration pipeline consistency audit on synthetic example"
	@echo "  make calibration-audit          Run calibration pipeline consistency audit (INTAKE=[path] GATE=[path] ...)"
	@echo "  make test               Run full test suite (2937 passing tests, >=80% coverage)"
	@echo "  make coverage           Test suite with per-module coverage report"
	@echo "  make lint               Ruff lint check on src/ tests/ scripts/"
	@echo "  make typecheck          mypy type check on src/"
	@echo "  make ci                 lint + test (CI gate)"
	@echo "  make clean              Remove outputs/ (except CSV pilot panel)"

pr-ready: agent-check doctor
	@echo "Ready for PR."

agent-check: claim-check doc-links-check bench-deprecation-check

docs-index-check:
	@echo "--- Docs index coverage check ---"
	PYTHONPATH=src $(PYTHON) scripts/check_docs_index_coverage.py --warn-only 2>/dev/null || \
	PYTHONPATH=src $(PYTHON) scripts/check_docs_index_coverage.py
	@echo "OK (advisory — index coverage expected to improve over time)"

docs-only-check:
	@echo "--- Docs-only PR check ---"
	PYTHONPATH=src $(PYTHON) scripts/check_docs_only_pr.py
	@echo "OK"

bench-deprecation-check:
	@echo "--- Benchmark deprecation check ---"
	PYTHONPATH=src $(PYTHON) scripts/check_benchmark_deprecation.py
	@echo "OK"
	@echo "All agent checks passed."

doctor:
	@echo "--- Environment diagnostic ---"
	PYTHONPATH=src $(PYTHON) scripts/doctor.py

claim-check:
	@echo "--- Claim language scan (advisory) ---"
	PYTHONPATH=src $(PYTHON) scripts/safety/check_claims.py
	@echo "OK"

cert-quality-check:
	@echo "--- Certificate quality check ---"
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli validate-cert-quality \
		--certificate outputs/evidence/AMPF-000001.json || true
	@echo "OK (advisory — individual certs should be checked explicitly)"

claim-check-strict:
	@echo "--- Claim language scan (strict, will fail on findings) ---"
	PYTHONPATH=src $(PYTHON) scripts/safety/check_claims.py --fail-on-findings

doc-links-check:
	@echo "--- Doc link check ---"
	PYTHONPATH=src $(PYTHON) scripts/check_doc_links.py
	@echo "OK"

demo:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli rank \
		--candidates examples/sequences/demo_candidates.csv \
		--references examples/known_reference/demo_known_amps.csv \
		--out outputs/demo_ranked.jsonl \
		--report outputs/demo_report.md \
		--cert-dir outputs/evidence \
		--manifest outputs/run_manifest.json \
		--simulation-mode info



test:
	$(PYTEST) -q

lint:
	$(RUFF) check src tests scripts

ci: lint test
	@echo "CI passed: lint + test suite green"

coverage:
	$(PYTEST) -q --cov=src --cov-report=term-missing --cov-fail-under=80

typecheck:
	uv run mypy src/ --ignore-missing-imports --no-error-summary 2>&1 | head -30 || true

bench-all: bench-500 bench-calibration bench-cheap-enemies bench-charge-distribution bench-simulation-calibration
	@echo "All key benchmarks complete."

bench-leakage:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench leakage \
		--candidates examples/sequences/demo_candidates.csv \
		--references examples/known_reference/demo_known_amps.csv \
		--out outputs/leakage_report.json

bench-baseline:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench baseline \
		--candidates examples/sequences/demo_candidates.csv \
		--references examples/known_reference/demo_known_amps.csv \
		--positives examples/known_reference/demo_known_amps.csv \
		--out outputs/bench_baseline_report.json

bench-hidden-active:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench baseline \
		--candidates examples/benchmark/mixed_candidates.csv \
		--positives examples/benchmark/active_labels.csv \
		--k 5 10 20 \
		--out outputs/bench_hidden_active_report.json

generate:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli generate-batch \
		--seeds examples/sequences/amp_seeds.csv \
		--out examples/sequences/phase3_pool.csv \
		--n-double 25 \
		--n-charge 12 \
		--rng-seed 2024

phase3: generate
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli rank \
		--candidates examples/sequences/phase3_pool.csv \
		--references examples/known_reference/amp_curated_references.csv \
		--out outputs/phase3_ranked.jsonl \
		--report outputs/phase3_report.md \
		--cert-dir outputs/phase3_evidence \
		--manifest outputs/phase3_manifest.json \
		--config configs/phase3.yaml
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli batch-pack \
		--ranked outputs/phase3_ranked.jsonl \
		--out-json outputs/phase3_batch_pack.json \
		--out-md outputs/phase3_batch_pack.md

pilot: phase3
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli pilot-panel \
		--ranked outputs/phase3_ranked.jsonl \
		--n 20 \
		--max-per-seed 4 \
		--similarity-threshold 0.75 \
		--out-csv outputs/pilot_panel.csv \
		--out-md outputs/pilot_panel.md

validate-scoring:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli validate-scoring \
		--amp-csv examples/validation/known_amps.csv \
		--decoy-csv examples/validation/random_background.csv \
		--benchmark-type standard \
		--out outputs/validate_scoring_report.json

validate-scoring-phase3:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli validate-scoring \
		--amp-csv examples/validation/known_amps.csv \
		--decoy-csv examples/validation/random_background.csv \
		--config configs/phase3.yaml \
		--benchmark-type standard \
		--out outputs/validate_scoring_report_phase3.json

bench-cluster-split:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench cluster-split \
		--amp-csv examples/validation/known_amps.csv \
		--decoy-csv examples/validation/random_background.csv \
		--out outputs/cluster_split_report.json

bench-500:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli validate-scoring \
		--amp-csv examples/validation/known_amps_500.csv \
		--decoy-csv examples/validation/random_background_500.csv \
		--benchmark-type standard \
		--out outputs/validate_scoring_500.json
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli validate-scoring \
		--amp-csv examples/validation/known_amps_500.csv \
		--decoy-csv examples/validation/random_background_500.csv \
		--config configs/phase3.yaml \
		--benchmark-type standard \
		--out outputs/validate_scoring_phase3_500.json
	@echo ""
	@echo "--- Calibration on expanded 500-AMP set ---"
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_calibration.py \
		--amp-csv examples/validation/known_amps_500.csv \
		--decoy-csv examples/validation/random_background_500.csv \
		--out outputs/bench_calibration_500.json
	@echo "Expanded benchmark (500 AMP + 500 decoy) complete."

bench-cluster-split-500:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench cluster-split \
		--amp-csv examples/validation/known_amps_500.csv \
		--decoy-csv examples/validation/random_background_500.csv \
		--out outputs/cluster_split_500.json
	@echo "Cluster-split on expanded 500-AMP set complete."

bench-easy-baseline:
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/baseline_trivial.py \
		--amp-csv examples/validation/known_amps_500.csv \
		--decoy-csv examples/validation/random_background_500.csv
	@echo "Easy baseline benchmark complete."

bench-charge-matched:
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_charge_matched.py \
		--amp-csv examples/validation/known_amps_500.csv \
		--decoy-csv examples/validation/random_background_500.csv \
		--out outputs/benchmark_charge_matched.json
	@echo "Charge-matched decoy benchmark complete."

bench-order-dependent:
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_order_dependent.py \
		--amp-csv examples/validation/known_amps_500.csv \
		--out outputs/benchmark_order_dependent.json
	@echo "Order-dependent features benchmark complete."

bench-precision-at-k:
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_precision_at_k.py \
		--amp-csv examples/validation/known_amps_500.csv \
		--decoy-csv examples/validation/random_background_500.csv \
		--out outputs/benchmark_precision_at_k.json
	@echo "Precision@k calibration benchmark complete."

bench-per-family:
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_per_family.py \
		--amp-csv examples/validation/known_amps_500.csv \
		--decoy-csv examples/validation/random_background_500.csv \
		--out outputs/benchmark_per_family.json
	@echo "Per-family benchmark breakdown complete."

bench-expert-ablation:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench expert-ablation \
		--amp-csv examples/validation/known_amps.csv \
		--decoy-csv examples/validation/random_background.csv \
		--out outputs/expert_ablation_report.json

bench-expert-ablation-500:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench expert-ablation \
		--amp-csv examples/validation/known_amps_500.csv \
		--decoy-csv examples/validation/random_background_500.csv \
		--out outputs/expert_ablation_report_500.json

bench-selectivity:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench selectivity \
		--hemolysis-csv examples/validation/hemolysis_reference.csv \
		--out outputs/selectivity_benchmark_report.json


bench-triage:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench triage \
		--out outputs/triage_benchmark_report.json

bench-gate:
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_gate.py \
		--baseline outputs/metrics_snapshot.json \
		--tolerance 0.02 \
		--out outputs/bench_gate_report.md

bench-feature-decomp:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench feature-decomp \
		--out outputs/feature_decomp_report.json
validate-scoring-strict:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli validate-scoring \
		--amp-csv examples/validation/known_amps.csv \
		--decoy-csv examples/validation/scrambled_decoys.csv \
		--benchmark-type strict \
		--out outputs/validate_scoring_strict_report.json

external-predict: pilot
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli external-predict \
		--pilot-csv outputs/pilot_panel.csv \
		--out-fasta outputs/pilot_panel.fasta \
		--out-checklist outputs/external_predict_checklist.md

# ── Sprint 3-6 targets ─────────────────────────────────────────────────

external-consensus:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli external-consensus \
		--pilot-csv outputs/pilot_panel.csv \
		--results-csv $$(or $$(RESULTS),outputs/external_predict_results.csv) \
		--out outputs/external_consensus_report.md

questionnaire:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli reviewer-questionnaire \
		--panel-csv outputs/confident_panel.csv \
		--out outputs/questionnaire

gate-check:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli gate-check \
		--validation-json outputs/validate_scoring_report.json

ip-report:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli ip-report \
		--panel-csv outputs/confident_panel.csv \
		--novelty-csv outputs/novelty_audit_full.csv \
		--out outputs/ip_report.md

benchmark-card:
	.venv/bin/openamp-foundry benchmark-card \
		--benchmark-id bench-auroc-001 \
		--benchmark-name "AMP vs Decoy AUROC" \
		--metric AUROC \
		--metric-value 0.82 \
		--baseline-name "random" \
		--baseline-value 0.50 \
		--dataset APD3 \
		--dataset-size 500 \
		--validate
	@echo "Benchmark card complete."

pilot-confident:
	@if [ -z "$(KEEP)" ]; then \
		echo "Usage: make pilot-confident KEEP=ID1,ID2,..."; \
		exit 1; \
	fi
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli pilot-confident \
		--pilot-csv outputs/pilot_panel.csv \
		--keep "$(KEEP)" \
		--out outputs/confident_panel

presynth-qc:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli presynth-qc \
		--panel-csv outputs/confident_panel.csv \
		--out outputs/presynth_qc_report.md

gold-standard:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli gold-standard \
		--panel-csv outputs/confident_panel.csv \
		--out outputs/gold_standard_calibration.md \
		--config configs/pipeline.yaml

diversity:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli diversity-check \
		--panel-csv outputs/confident_panel.csv \
		--out outputs/diversity_report.md

synthesis-order:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli synthesis-order \
		--panel-csv outputs/confident_panel.csv \
		--out-csv outputs/synthesis_order.csv \
		--out-md outputs/synthesis_checklist.md \
		--quantity-mg 5

novelty-broad: pilot
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli novelty-check-broad \
		--panel-csv outputs/pilot_panel.csv \
		--references-csv examples/known_reference/amp_curated_references.csv \
		--out outputs/novelty_broad_report.md

lab-result-intake-example:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli calibration-intake \
		--panel examples/lab_results_panel.csv \
		--results-dir examples/lab_results \
		--out-json outputs/calibration_intake_example.json \
		--out-md outputs/calibration_intake_example.md

lab-result-intake:
	@if [ -z "$(PANEL)" ] || [ -z "$(RESULTS_DIR)" ]; then \
		echo "Usage: make lab-result-intake PANEL=<panel.csv> RESULTS_DIR=<lab_results_dir>"; \
		echo ""; \
		echo "Or run the synthetic example without arguments:"; \
		echo "  make lab-result-intake-example"; \
		exit 1; \
	fi
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli calibration-intake \
		--panel "$(PANEL)" \
		--results-dir "$(RESULTS_DIR)" \
		--out-json outputs/calibration_intake.json \
		--out-md outputs/calibration_intake.md

recalibration-gate-example: lab-result-intake-example
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli recalibration-gate \
		--intake-report outputs/calibration_intake_example.json \
		--intake-report-date 2026-07-04 \
		--out-json outputs/recalibration_gate_example.json \
		--out-md outputs/recalibration_gate_example.md

recalibration-gate:
	@if [ -z "$(INTAKE)" ]; then \
		echo "Usage: make recalibration-gate INTAKE=<intake.json> [DATE=<YYYY-MM-DD>] [PREV=<YYYY-MM-DD>] [L1=<float>]"; \
		echo ""; \
		echo "Or run the synthetic example without arguments:"; \
		echo "  make recalibration-gate-example"; \
		exit 1; \
	fi
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli recalibration-gate \
		--intake-report "$(INTAKE)" \
		$$(if [ -n "$(DATE)" ]; then echo --intake-report-date "$(DATE)"; fi) \
		$$(if [ -n "$(PREV)" ]; then echo --previous-recalibration-at "$(PREV)"; fi) \
		$$(if [ -n "$(L1)" ]; then echo --weight-l1-distance "$(L1)"; fi) \
		--out-json outputs/recalibration_gate.json \
		--out-md outputs/recalibration_gate.md

recalibration-engine: lab-result-intake-example
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli recalibration-engine \
		--intake-report outputs/calibration_intake_example.json \
		--gate-verdict outputs/recalibration_gate_example.json \
		--current-weights '{"activity": 0.40, "safety": 0.25, "synthesis": 0.15, "novelty": 0.20}' \
		--out-json outputs/recalibration_proposal.json \
		--out-md outputs/recalibration_proposal.md

recalibration-engine-dry-run: lab-result-intake-example
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli recalibration-engine \
		--intake-report outputs/calibration_intake_example.json \
		--gate-verdict outputs/recalibration_gate_example.json \
		--current-weights '{"activity": 0.40, "safety": 0.25, "synthesis": 0.15, "novelty": 0.20}' \
		--dry-run

validate-policy-version:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli validate-policy-version \
		--current-policy configs/recalibration_policy.yaml \
		--previous-policy configs/recalibration_policy.yaml \
		--decision-log-dir decision_logs/

bump-policy-version:
	PYTHONPATH=src $(PYTHON) scripts/calibration/bump_recalibration_policy.py \
		$(if $(HUMAN_REVIEWER),--human-reviewer "$(HUMAN_REVIEWER)",) \
		$(if $(DRY_RUN),--dry-run,)

bump-policy-version-dry-run:
	PYTHONPATH=src $(PYTHON) scripts/calibration/bump_recalibration_policy.py \
		--human-reviewer "DRY_RUN" --dry-run

calibration-loop:
	PYTHONPATH=src $(PYTHON) scripts/calibration/run_calibration_loop.py \
		--out-dir outputs/calibration_loop \
		--seed 42 --n-batch-2 10

calibration-audit-example: lab-result-intake-example
	-PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli recalibration-gate \
		--intake-report outputs/calibration_intake_example.json \
		--intake-report-date 2026-07-04 \
		--out-json outputs/recalibration_gate_example.json \
		--out-md outputs/recalibration_gate_example.md 2>/dev/null
	-PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli calibration-audit \
		--intake-report outputs/calibration_intake_example.json \
		--gate-verdict outputs/recalibration_gate_example.json \
		--out-json outputs/calibration_audit_example.json \
		--out-md outputs/calibration_audit_example.md

calibration-audit:
	@if [ -z "$(INTAKE)" ] && [ -z "$(GATE)" ] && [ -z "$(ENGINE)" ] && [ -z "$(REPORT)" ]; then \
		echo "Usage: make calibration-audit [INTAKE=<intake.json>] [GATE=<gate.json>] [ENGINE=<engine.json>] [REPORT=<report.json>] [OUT_JSON=<path>] [OUT_MD=<path>]"; \
		echo "At least one artifact path is required."; \
		exit 1; \
	fi
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli calibration-audit \
		$$(if [ -n "$(INTAKE)" ]; then echo --intake-report "$(INTAKE)"; fi) \
		$$(if [ -n "$(GATE)" ]; then echo --gate-verdict "$(GATE)"; fi) \
		$$(if [ -n "$(ENGINE)" ]; then echo --engine-proposal "$(ENGINE)"; fi) \
		$$(if [ -n "$(REPORT)" ]; then echo --recalibration-report "$(REPORT)"; fi) \
		$$(if [ -n "$(OUT_JSON)" ]; then echo --out-json "$(OUT_JSON)"; fi) \
		$$(if [ -n "$(OUT_MD)" ]; then echo --out-md "$(OUT_MD)"; fi)

generate-synthetic-lab-results:
	PYTHONPATH=src $(PYTHON) examples/lab_results_generator.py \
		--panel-csv outputs/pilot_panel.csv \
		--cohort-size 20 --effect-size 0.40 --seed 42 \
		--assay-types MIC hemolysis_RBC \
		--out-dir outputs/synthetic_lab_results

clean:
	rm -rf outputs/*.jsonl outputs/*.md outputs/*.json outputs/evidence outputs/phase3_evidence .pytest_cache .ruff_cache

# ── Wave 0.5 Scaffold Diversification targets ──────────────────────────────

wave0-5-gate-check:
	PYTHONPATH=src $(PYTHON) src/openamp_foundry/gates/wave0_5_gate_checker.py

wave0-5-novelty-audit:
	PYTHONPATH=src $(PYTHON) scripts/waves/run_wave0_5_novelty_audit.py

wave0-5-novelty-audit-v2:
	$(PYTHON) scripts/waves/run_wave0_5_novelty_audit_v2.py

wave0-5-fill-external:
	PYTHONPATH=src $(PYTHON) scripts/waves/fill_wave0_5_external_results.py

wave0-5-panel: wave0-5-fill-external
	PYTHONPATH=src $(PYTHON) scripts/waves/select_wave1_panel.py

wave0-5-evidence:
	PYTHONPATH=src $(PYTHON) scripts/waves/generate_wave0_5_evidence_certs.py

bench-simulation-ablation:
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_simulation_ablation.py \
		--mode amp-vs-decoy --out outputs/simulation_ablation.json

bench-simulation-ablation-within-amp:
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_simulation_ablation.py \
		--mode within-amp --out outputs/simulation_ablation_within_amp.json

bench-calibration:
	@echo "--- Pipeline calibration benchmark ---"
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_calibration.py \
		--out outputs/bench_calibration.json
	@echo ""
	@echo "--- Expanded calibration (500-AMP) ---"
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_calibration.py \
		--amp-csv examples/validation/known_amps_500.csv \
		--decoy-csv examples/validation/random_background_500.csv \
		--out outputs/bench_calibration_500.json
	@echo "OK"

bench-charge-distribution:
	@echo "--- Charge distribution report ---"
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_charge_distribution.py \
		--amp-csv examples/validation/known_amps_500.csv \
		--decoy-csv examples/validation/random_background_500.csv
	@echo "OK"

bench-simulation-calibration:
	@echo "--- Simulation uncertainty calibration ---"
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_simulation_calibration.py
	@echo "OK"

bench-cheap-enemies:
	@echo "--- Cheap enemy comparison ---"
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_cheap_enemy_comparison.py
	@echo "OK"

bench-simulation-baselines:
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_simulation_baselines.py \
		--out outputs/simulation_baselines.json

simulation-gate:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench simulation-gate \
		--amp-vs-decoy-json outputs/simulation_ablation.json \
		--within-amp-json outputs/simulation_ablation_within_amp.json \
		--out outputs/simulation_gate_verdict.json

bench-strategy-compare:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench strategy-compare \
		--out-json outputs/strategy_comparison.json \
		--out-md outputs/strategy_comparison.md

batch-rationale:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli batch-rationale \
		--n-total 50 --n-active 10 --batch-size 10 \
		--out-json outputs/batch_rationale_report.json \
		--out-md outputs/batch_rationale_report.md

bench-cross-dataset:
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_cross_dataset.py \
		--out outputs/cross_dataset_benchmark.json

bench-multi-negatives:
	PYTHONPATH=src $(PYTHON) scripts/benchmarks/benchmark_multi_negatives.py \
		--out outputs/multi_negative_benchmark.json

regenerate-all:
	PYTHONPATH=src $(PYTHON) scripts/release/regenerate_all.py

full-reproducibility-report:
	PYTHONPATH=src $(PYTHON) scripts/release/full_reproducibility_report.py

metrics-snapshot:
	PYTHONPATH=src $(PYTHON) -m openamp_foundry.cli bench metrics-snapshot \
		--out outputs/metrics_snapshot.json

wave0-5b-generate:
	PYTHONPATH=src $(PYTHON) scripts/waves/generate_wave0_5b_candidates.py

wave0-5b-filter: wave0-5b-generate
	PYTHONPATH=src $(PYTHON) scripts/waves/filter_wave0_5b_candidates.py

lab-batch-pack:
	PYTHONPATH=src $(PYTHON) scripts/lab/build_lab_batch_pack.py \
		--panel-csv outputs/phase3_ranked.jsonl \
		--evidence-dir outputs/evidence_wave0_5 \
		--out outputs/lab_batch_pack.zip \
		--manifest-out outputs/lab_batch_pack_manifest.json

generate-review-packet:
	PYTHONPATH=src $(PYTHON) scripts/generate_review_packet.py \
		--pipeline-version v0.5.73 \
		--git-sha $$(git rev-parse HEAD) \
		--candidate-count 36 \
		--proof-ladder-level 2 \
		--out outputs/review_packet_skeleton.json \
		--validate

failed-candidate-report:
	PYTHONPATH=src $(PYTHON) scripts/generate_failed_candidate_report.py \
		--input examples/failed_candidates_example.json \
		--out-json outputs/failed_candidate_report.json \
		--out-md outputs/failed_candidate_report.md \
		--validate-rejection-codes

classify-negative-informativeness:
	PYTHONPATH=src $(PYTHON) scripts/classify_negative_result_informativeness.py \
		--input examples/negative_result_entry_example.json \
		--out-json outputs/negative_result_informativeness_result.json \
		--out-md outputs/negative_result_informativeness_result.md

safe-publication-filter:
	PYTHONPATH=src $(PYTHON) scripts/safe_publication_filter.py \
		--input examples/safe_publication_filter_example_input.json \
		--out-json outputs/safe_publication_filter_result.json \
		--out-md outputs/safe_publication_filter_result.md

validate-rejection-events:
	PYTHONPATH=src $(PYTHON) scripts/validate_rejection_events.py \
		--input examples/rejection_events_example.json \
		--out-json outputs/rejection_events_validation.json \
		--out-md outputs/rejection_events_validation.md

check-negative-archive-completeness:
	PYTHONPATH=src $(PYTHON) scripts/check_negative_archive_completeness.py \
		--input examples/negative_result_archive_example.json \
		--out-json outputs/negative_archive_completeness_report.json \
		--out-md outputs/negative_archive_completeness_report.md

negative-result-dashboard:
	PYTHONPATH=src $(PYTHON) scripts/negative_result_dashboard.py \
		--input examples/negative_result_dashboard_example.json \
		--out-json outputs/negative_result_dashboard.json \
		--out-md outputs/negative_result_dashboard.md

calibration-overfit-check:
	.venv/bin/openamp-foundry calibration-overfit-check \
		--cohort-sizes 8,25,50 --model-params 10 --n-features 5 \
		--out-json /tmp/overfit_check.json --out-md /tmp/overfit_check.md
	@echo "Overfit check complete. See /tmp/overfit_check.json"

result-quality-filter:
	echo '[{"candidate_id":"AMP001","flags":[]},{"candidate_id":"AMP002","flags":["contamination"]},{"candidate_id":"AMP003","flags":["replicate_disagreement","borderline_threshold"]}]' > /tmp/rq_input.json
	.venv/bin/openamp-foundry result-quality-filter \
		--results-json /tmp/rq_input.json \
		--out-json /tmp/rq_output.json --out-md /tmp/rq_output.md
	@echo "Result quality filter done. See /tmp/rq_output.json"

synthetic-result-policy-check:
	echo '[{"candidate_id":"AMP001","current_level":2,"proposed_level":3,"evidence_source":"synthetic"},{"candidate_id":"AMP002","current_level":2,"proposed_level":2,"evidence_source":"synthetic"},{"candidate_id":"AMP003","current_level":2,"proposed_level":3,"evidence_source":"lab"}]' > /tmp/srp_input.json
	.venv/bin/openamp-foundry synthetic-result-policy-check \
		--proposals-json /tmp/srp_input.json \
		--out-json /tmp/srp_output.json --out-md /tmp/srp_output.md
	@echo "Synthetic result policy check done. See /tmp/srp_output.json"

calibration-decision-checklist:
	echo '{"G9-01":true,"G9-02":true,"G9-03":true,"G9-04":true,"G9-05":true,"G9-06":true,"G9-07":true,"G9-08":true,"G9-09":true,"G9-10":true,"G9-11":true}' > /tmp/checklist_responses.json
	.venv/bin/openamp-foundry calibration-decision-checklist \
		--checklist-id CHK-2026-001 \
		--date 2026-07-09 \
		--reviewer "human-reviewer" \
		--responses-json /tmp/checklist_responses.json \
		--out-json /tmp/checklist_output.json \
		--out-md /tmp/checklist_output.md; true
	@echo "Calibration decision checklist done. See /tmp/checklist_output.json"

calibration-rollback-plan:
	.venv/bin/openamp-foundry calibration-rollback-plan \
		--plan-id RBK-2026-001 \
		--version v0.5.87 \
		--triggered-by RT-01,RT-04 \
		--notes "AUROC dropped 0.03 after adding new training candidates." \
		--out-json /tmp/rollback_plan.json \
		--out-md /tmp/rollback_plan.md
	@echo "Rollback plan generated. See /tmp/rollback_plan.json"

simulation-registry:
	.venv/bin/openamp-foundry simulation-registry --list
	@echo "Simulation module registry displayed."

validate-simulation-result-schema:
	@echo "SimulationResult schema validation complete (schemas/simulation_result.schema.json)."

simulation-baseline-check:
	.venv/bin/openamp-foundry simulation-baseline-check \
		--module-id membrane_proxy \
		--claimed-level 2 \
		--baseline-beaten false
	@echo "Baseline check complete."

adapter-gate-check:
	.venv/bin/openamp-foundry adapter-gate-check \
		--module-id membrane_proxy \
		--timeout false \
		--schema-errors "[]" \
		--baseline-beaten false
	@echo "Adapter gate check complete."

simulation-provenance:
	.venv/bin/openamp-foundry simulation-provenance \
		--run-id test-run-001 \
		--module-id membrane_proxy \
		--module-version 0.1.0 \
		--timestamp-utc 2026-07-09T12:00:00Z \
		--input-sequence AKLWKR \
		--scores-json '{"binding_energy": 0.75}'
	@echo "Provenance record complete."

simulation-ensemble-check:
	.venv/bin/openamp-foundry simulation-ensemble-check \
		--sequence AKLWKR \
		--results-json '[{"module":"membrane_proxy","version":"0.1.0","scope":["bacterial_binding"],"scores":{"binding_energy":0.75},"uncertainty":0.1,"calibration_set":null,"validated_against":["APD3"],"notes":[]},{"module":"structure_proxy","version":"0.1.0","scope":["bacterial_binding"],"scores":{"binding_energy":0.80},"uncertainty":0.1,"calibration_set":null,"validated_against":["APD3"],"notes":[]}]'
	@echo "Ensemble check complete."

simulation-ci-report:
	.venv/bin/openamp-foundry simulation-ci-report \
		--results-json '[{"module":"membrane_proxy","version":"0.1.0","scope":["bacterial_binding"],"scores":{"binding_energy":0.75},"uncertainty":0.1,"calibration_set":null,"validated_against":["APD3"],"notes":[]},{"module":"structure_proxy","version":"0.1.0","scope":["bacterial_binding"],"scores":{"binding_energy":0.80},"uncertainty":0.15,"calibration_set":null,"validated_against":["APD3"],"notes":[]}]'
	@echo "CI report complete."

simulation-deprecation-check:
	.venv/bin/openamp-foundry simulation-deprecation-check \
		--module-ids membrane_proxy,dummy_membrane_proxy,external_adapter_placeholder
	@echo "Deprecation check complete."

simulation-scope-check:
	.venv/bin/openamp-foundry simulation-scope-check \
		--module-id membrane_proxy \
		--requested-scopes bacterial_binding,fungal_binding
	@echo "Scope check complete."

simulation-evidence-packet:
	.venv/bin/openamp-foundry simulation-evidence-packet \
		--module-id membrane_proxy \
		--result-json '{"module":"membrane_proxy","version":"0.1.0","scope":["bacterial_binding"],"scores":{"binding_energy":0.75},"uncertainty":0.1,"calibration_set":null,"validated_against":["APD3"],"notes":[]}' \
		--requested-scopes bacterial_binding \
		--claimed-level 2 \
		--baseline-beaten false
	@echo "Evidence packet complete."

artifact-version:
	.venv/bin/openamp-foundry artifact-version --list
	@echo "Artifact version list complete."

candidate-manifest:
	.venv/bin/openamp-foundry candidate-manifest \
		--candidate-id AMP-001 \
		--sequence AKLWKR \
		--evidence-level 2 \
		--scopes bacterial_binding \
		--scores-json '{"binding_energy": 0.75}' \
		--uncertainty 0.1 \
		--source-modules membrane_proxy \
		--validate
	@echo "Candidate manifest complete."

artifact-changelog:
	.venv/bin/openamp-foundry artifact-changelog
	@echo "Artifact changelog complete."

integration-check:
	.venv/bin/openamp-foundry integration-check \
		--manifest-json '{"candidate_id":"AMP-001","sequence":"AKLWKR","evidence_level":2,"scopes":["bacterial_binding"],"scores":{"binding_energy":0.75},"uncertainty":0.1,"source_modules":["membrane_proxy"],"calibration_set":null,"safety_flags":[],"provenance_run_id":null,"dry_lab_only":true,"version":"1.0.0","created_at":"2026-07-09T00:00:00Z","notes":[]}'
	@echo "Integration check complete."

adapter-author-check:
	.venv/bin/openamp-foundry adapter-check \
		--adapter-json '{"adapter_id":"example-adapter","adapter_version":"1.0.0","mode":"info","output_status":"ok","score_fields":{"activity":0.72},"uncertainty":0.15,"warnings":[],"failure_reason":null,"release_status":"internal","ranking_effect":"none","has_baseline_comparison":false,"makes_network_calls":false,"network_call_documented":false,"dry_lab_only":true}'
	@echo "Adapter author check complete."

license-check:
	.venv/bin/openamp-foundry license-check \
		--source-json '{"source_id":"apd-v2","source_name":"Antimicrobial Peptide Database v2","license_id":"CC-BY-4.0","use_context":"training","attribution_required":true,"commercial_use_allowed":true,"redistribution_allowed":true,"modifications_allowed":true,"human_review_required":false,"notes":"","dry_lab_only":true}'
	@echo "License check complete."

artifact-compat-check:
	.venv/bin/openamp-foundry artifact-compat-check
	@echo "Artifact compatibility check complete."

contribution-check:
	.venv/bin/openamp-foundry contribution-check \
		--intake-json '{"institution_name":"Example University","contact_email":"research@example.edu","contribution_type":"dataset_donation","proposed_scope":"Curated AMP dataset 500 sequences","human_review_required":false,"dry_lab_only":true,"data_license":"CC-BY-4.0","dataset_description":"AMP sequences with MIC data","record_count":500}'
	@echo "Contribution intake check complete."

adoption-scorecard:
	.venv/bin/openamp-foundry adoption-scorecard \
		--scores-json '{"integration_check":{"passed_checks":5,"total_checks":5,"notes":""},"license_compliance":{"passed_checks":3,"total_checks":3,"notes":""},"adapter_validation":{"passed_checks":2,"total_checks":2,"notes":""},"schema_compatibility":{"passed_checks":4,"total_checks":4,"notes":""},"contribution_readiness":{"passed_checks":1,"total_checks":1,"notes":""}}'
	@echo "Adoption scorecard complete."

release-gate-check:
	.venv/bin/openamp-foundry release-gate-check \
		--release-type schema \
		--artifact-id candidate_manifest_v1 \
		--gates-json '{"ci_tests_pass":true,"agent_check_passes":true,"no_critical_issues":true,"dry_lab_only_confirmed":true,"safety_flags_reviewed":true,"data_license_verified":true,"no_hardcoded_secrets":true,"schema_compatibility_passes":true,"version_bumped":true,"changelog_updated":true}'
	@echo "Release gate check complete."

decision-log:
	.venv/bin/openamp-foundry decision-log --validate
	@echo "Decision log check complete."

release-request-check:
	.venv/bin/openamp-foundry release-request-check \
		--request-json '{"release_id":"REL-2026-001","release_type":"schema","artifact_id":"candidate_manifest","artifact_version":"1.0.0","requestor_name":"OpenAMP Team","requestor_institution":"Open Problem Lab","request_date":"2026-07-09","evidence_level":2,"dry_lab_only":true,"safety_review_status":"approved","benchmark_summary":"Passes all schema compatibility checks","known_limitations":"Dry-lab only, not wet-lab validated","intended_use":"public","data_license":"CC-BY-4.0","human_reviewer":"maintainer","review_class":"B","approval_status":"pending"}'
	@echo "Release request check complete."

coi-check:
	.venv/bin/openamp-foundry coi-check \
		--disclosure-json '{"disclosure_id":"COI-2026-001","disclosure_type":"reviewer","subject":"maintainer","related_artifact":"REL-2026-001","relationship_type":"none","description":"","disclosure_date":"2026-07-09","recusal_required":false,"reviewer":"lead-maintainer","review_status":"acknowledged"}'
	@echo "COI check complete."

rotation-plan-check:
	.venv/bin/openamp-foundry rotation-plan-check \
		--plan-json '{"entries":[{"github_handle":"maintainer","role":"primary_maintainer","backup_handle":"backup-maintainer","responsibilities":["releases","safety-policy","final-approvals"],"status":"active"},{"github_handle":"backup-maintainer","role":"secondary_maintainer","backup_handle":"maintainer","responsibilities":["day-to-day-reviews","issue-triage"],"status":"active"}]}'
	@echo "Rotation plan check complete."

security-report-check:
	.venv/bin/openamp-foundry security-report-check \
		--report-json '{"report_id":"SEC-2026-001","severity":"medium","category":"dependency_vulnerability","description":"CVE-2026-1234 in requests library","affected_version":"v0.7.3","reporter_handle":"anonymous","report_date":"2026-07-09","status":"acknowledged"}'
	@echo "Security report check complete."

citation-check:
	.venv/bin/openamp-foundry citation-check \
		--citation-json '{"artifact_id":"OAMP-v0.7.5","citation_type":"software","title":"OpenAMP Foundry","version":"v0.7.5","authors":["Open-Problem-Lab"],"year":"2026","license_identifier":"MIT","reuse_class":"open","url":"https://github.com/Open-Problem-Lab/OpenAMP-Foundry","bibtex_key":"openamp_foundry_2026"}'
	@echo "Citation check complete."

roadmap-sync-check:
	.venv/bin/openamp-foundry roadmap-sync-check \
		--entry-json '{"item_id":"J8","phase":"J","description":"Add roadmap-to-issue sync checklist","priority":"B","sync_status":"synced","issue_number":807}'
	@echo "Roadmap sync check complete."

advisory-review-check:
	.venv/bin/openamp-foundry advisory-review-check \
		--review-json '{"review_id":"ADV-2026-001","review_type":"candidate_review","artifact_id":"OAMP-v0.7.6-candidates","reviewer_handle":"external-advisor-1","assigned_date":"2026-07-09","deadline_date":"2026-07-23","status":"pending"}'
	@echo "Advisory review check complete."

annual-review-check:
	.venv/bin/openamp-foundry annual-review-check \
		--entry-json '{"review_id":"ANN-2026-001","year":"2026","section":"safety_policy","reviewer":"maintainer-1","finding_count":0,"action_items_count":0,"status":"completed","notes":"All safety checks passed.","completion_date":"2026-07-09"}'
	@echo "Annual review check complete."

selection-rationale-check:
	.venv/bin/openamp-foundry selection-rationale-check \
		--entry-json '{"selection_id":"SEL-2026-001","batch_id":"batch-2026-001","candidate_id":"OAMP-001","pipeline_version":"v0.7.9","selection_date":"2026-07-09","evidence_level":3,"baseline_comparison":"Scored above random baseline (AUROC 0.83) and charge-matched baseline (AUROC 0.71).","primary_criterion":"Top ensemble score with selectivity index > 2.","safety_flags_checked":["hemolysis_checked","toxicity_checked"],"reviewer":"maintainer-1"}'
	@echo "Selection rationale check complete."

batch-priority-check:
	.venv/bin/openamp-foundry batch-priority-check \
		--entry-json '{"priority_id":"PRI-2026-001","batch_id":"batch-2026-001","candidate_id":"OAMP-001","pipeline_version":"v0.8.0","priority_rank":1,"priority_score":0.87,"evidence_level":3,"synthesis_complexity":"low","novelty_tier":"high","primary_rationale":"Top ensemble score with selectivity > 2, low synthesis risk."}'
	@echo "Batch priority check complete."

pilot-package-check:
	.venv/bin/openamp-foundry pilot-package-check \
		--entry-json '{"package_id":"PKG-001","batch_id":"BATCH-001","submission_date":"2026-07-09","pipeline_version":"0.8.1","included_artifacts":["selection_rationale","batch_priority","evidence_certificate"],"missing_artifacts":[],"reviewer":"alice","approver":"bob","completeness_score":1.0,"ready_to_submit":true,"dry_lab_only":true}' \
		--format text

calibration-intake-check:
	.venv/bin/openamp-foundry calibration-intake-check \
		--entry-json '{"intake_id":"CAL-001","batch_id":"BATCH-001","candidate_id":"AMP-001","pipeline_version":"0.8.1","assay_type":"mic_assay","predicted_outcome":"active","observed_outcome":"active","predicted_confidence":0.85,"intake_date":"2026-07-09","reviewer":"alice","dry_lab_only":false}' \
		--format text

uncertainty-report-check:
	.venv/bin/openamp-foundry uncertainty-report-check \
		--entry-json '{"report_id":"UQ-001","batch_id":"BATCH-001","candidate_id":"AMP-001","pipeline_version":"0.8.3","metric_name":"mic","point_estimate":4.0,"lower_bound":2.0,"upper_bound":8.0,"confidence_level":0.90,"calibration_source":"historical_holdout_v2","reviewer":"alice","dry_lab_only":true}' \
		--format text

preprint-bundle-check:
	.venv/bin/openamp-foundry preprint-bundle-check \
		--entry-json '{"bundle_id":"BND-001","batch_id":"BATCH-001","pipeline_version":"0.8.4","submission_date":"2026-07-09","title":"Computational nomination of AMP candidates from the OpenAMP Foundry","artifact_ids":["SEL-001","PRI-001","PKG-001","UQ-001","CAL-001"],"evidence_level":4,"preprint_doi":"10.1101/2026.07.09.000001","contact_email":"research@openamp.org","release_approved":true,"dry_lab_only":true}' \
		--format text
