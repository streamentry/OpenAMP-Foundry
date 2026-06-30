# Virtual Assay Scope

## Purpose

The OpenAMP virtual assay layer exists to perform one job: **reduce the number of wet-lab experiments required to find a validated AMP.**

It does this by serving as a multi-resolution triage filter between cheap dry-lab screening (Phase 1) and actual wet-lab testing. It is *not* intended to be a perfect biological simulation, and it does not replace the wet lab. 

The core operating principle is **"Wet lab is the expensive oracle."** The virtual assay layer asks the oracle fewer, smarter questions.

## What OpenAMP WILL Model

1.  **Multi-Resolution Proxies**: Moving beyond basic sequence heuristics (like charge and hydrophobicity) to include:
    *   **Structure Ensembles**: Predicted secondary/tertiary structures.
    *   **Coarse-Grained Membrane Interactions**: Simplified interaction simulations with bacterial (e.g., E. coli, S. aureus) and mammalian (RBC-like) membrane proxies (e.g., binding energy, insertion depth).
    *   **Serum Stability / Protease Resistance**: Proxies for half-life in physiological conditions.
2.  **Learned Surrogate Emulators**: Machine learning models trained to predict MIC, HC50, and cytotoxicity from the structural and membrane interaction features.
3.  **Uncertainty**: Every virtual assay must output an explicit uncertainty score. If the model is extrapolating outside its calibration data, it must abstain or flag low confidence.
4.  **Calibration via Active Learning**: The models will be updated using true wet-lab assay outcomes (both hits and failures) from small, targeted batches (8-12 peptides).

## What OpenAMP WILL NOT Model (No Simulation Theater)

1.  **Whole-Organism Simulation**: We are not simulating entire E. coli bacteria from atoms upward.
2.  **Uncalibrated "Truth"**: We will not treat molecular dynamics (MD) or surrogate model outputs as biological proof.
3.  **Simulation for Simulation's Sake**: A virtual assay module will only be integrated into the selection pipeline if it empirically improves candidate triage relative to a cheap heuristic baseline. If a complex 24-hour MD simulation doesn't select better candidates than a 2-second Boman index calculation, it will be discarded.
4.  **Cherry-Picked Validation**: We will not adjust success criteria after running simulations to make the pipeline look better.

## Integration Rules

Any new virtual assay module added to the `openamp_foundry.simulation` package must satisfy the following contract:

1.  **Implements `VirtualAssayProxy`**: Must conform to the standard interface returning a `SimulationResult`.
2.  **Explicit Baseline Comparison**: Must demonstrate performance against the `EmulatorBaseline` contract on a benchmark set before affecting actual candidate selection.
3.  **Strict Scope Definition**: Must explicitly list the scopes it targets (e.g., `["bacterial_membrane_binding", "rbc_membrane_disruption"]`).
4.  **Uncertainty Reporting**: Must provide an explicit uncertainty metric (0.0 to 1.0) and identify its calibration dataset.
