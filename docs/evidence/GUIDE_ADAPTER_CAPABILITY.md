# Adapter Capability Reading Guide

How to understand what an external adapter can and cannot do.

## Required Documentation
Each adapter should document:
- What it models (scope)
- What it does NOT model (out of scope)
- Calibration data available
- Error handling behavior
- Resource requirements

## Reading the SimulationResult
- `scope` — what was modeled (e.g., `bacterial_membrane_binding`)
- `scores` — the actual output values
- `uncertainty` — 0 = certain, 1 = completely uncertain
- `calibration_set` — what data was used for calibration (None = no calibration)
- `notes` — warnings, limitations, and context

## Red Flags
- `uncertainty` > 0.5 — do not use for decision-making
- `calibration_set` is None — no evidence the adapter works
- `notes` mention `SIMULATION_THEATER_RISK` — adapter is speculative
