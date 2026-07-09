.PHONY: help demo test lint ci clean bench-leakage bench-multi-negatives bench-baseline bench-hidden-active bench-cluster-split bench-expert-ablation bench-expert-ablation-500 bench-selectivity bench-feature-decomp bench-gate bench-easy-baseline bench-charge-matched bench-order-dependent bench-precision-at-k bench-per-family bench-simulation-ablation bench-simulation-ablation-within-amp simulation-gate regenerate-all generate phase3 pilot validate-scoring validate-scoring-phase3 validate-scoring-strict external-pilot pilot-confident presynth-qc gold-standard diversity synthesis-order novelty-broad external-consensus questionnaire gate-check ip-report benchmark-card wave0-5-gate-check wave0-5-novelty-audit wave0-5-novelty-audit-v2 wave0-5-panel wave0-5-evidence wave0-5-fill-external wave0-5b-generate wave0-5b-filter recalibration-engine recalibration-engine-dry-run validate-policy-version generate-synthetic-lab-results bump-policy-version generate-review-packet failed-candidate-report safe-publication-filter classify-negative-informativeness validate-rejection-events negative-result-dashboard calibration-audit calibration-audit-example

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

benchmark-card: validate-scoring
	@echo "Benchmark card is a static document at docs/BENCHMARK_CARD.md"
	@echo "Run 'make validate-scoring' to update outputs/validate_scoring_report.json"

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
