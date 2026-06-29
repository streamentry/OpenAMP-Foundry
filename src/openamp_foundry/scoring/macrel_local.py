"""Calibrated local Macrel scorer — real ONNX models, margin-based decisions.

Macrel (Santos-Junior et al. 2020, PeerJ) ships two trained models: an AMP classifier
and a hemolysis classifier. In this environment the model's *calibrated probability*
output is broken by an onnxruntime/sklearn-onnx ZipMap incompatibility — the returned
values are centred decision **margins** (AMP = −NAMP, summing to 0) rather than
probabilities in [0,1]. Consequently Macrel's own `is_AMP` label mis-classifies even
magainin-2 as non-AMP.

The *relative* signal, however, is perfectly intact. Measured AMP margins:

    gold-standard AMPs   magainin −0.050, LL-37 −0.069, cecropin-A −0.079,
                         pexiganan −0.040, melittin −0.188, buforin-II −0.257
    non-AMPs             polyK −0.545, polyA −0.515, insulin-B −0.812, albumin −1.000

There is a clean separating gap (~−0.26 worst AMP vs ~−0.51 best non-AMP). We therefore
use the margins as a calibrated relative scorer: a candidate must be *at least as
AMP-like as the gold-standard panel* and *no more hemolytic than magainin* by Macrel's
own model. This recovers a genuine, independent, in-the-loop activity+hemolysis signal
despite the absolute-probability bug.

Calibration thresholds are derived from the panel above and fixed before ranking:
    AMP_MARGIN_GATE  = -0.30   (clearly inside the known-AMP zone)
    HEMO_MARGIN_GATE = -0.05   (excludes the melittin/pexiganan hemolytic cluster)

If the models are absent or onnxruntime is unavailable, scoring returns None and the
caller should treat Macrel as unavailable (never silently pass/fail).
"""
from __future__ import annotations

import functools
import gzip
import os
from dataclasses import dataclass

# Calibration constants (see module docstring; derived from a fixed known-AMP panel).
AMP_MARGIN_GATE = -0.30
HEMO_MARGIN_GATE = -0.05

# Normalisation anchors for mapping margins → [0,1] component scores.
_AMP_LO, _AMP_HI = -0.55, -0.04   # non-AMP floor → best-AMP ceiling
_HEMO_HI, _HEMO_LO = -0.01, -0.80  # most-hemolytic → least-hemolytic


@dataclass(frozen=True)
class MacrelResult:
    amp_margin: float
    hemo_margin: float
    amp_like_score: float      # [0,1], higher = more AMP-like (normalised margin)
    nonhemo_score: float       # [0,1], higher = less hemolytic (normalised margin)
    passes_amp_gate: bool
    passes_hemo_gate: bool

    @property
    def passes(self) -> bool:
        return self.passes_amp_gate and self.passes_hemo_gate


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


@functools.lru_cache(maxsize=1)
def _sessions():
    """Lazily load the two Macrel ONNX models. Returns (amp_sess, hemo_sess) or None."""
    try:
        import macrel
        import onnxruntime as rt
    except Exception:
        return None
    models_dir = os.path.join(os.path.dirname(macrel.__file__), "data", "models")
    amp_path = os.path.join(models_dir, "AMP.onnx.gz")
    hemo_path = os.path.join(models_dir, "Hemo.onnx.gz")
    if not (os.path.exists(amp_path) and os.path.exists(hemo_path)):
        return None
    try:
        with gzip.open(amp_path, "rb") as f:
            amp = rt.InferenceSession(f.read(), providers=["CPUExecutionProvider"])
        with gzip.open(hemo_path, "rb") as f:
            hemo = rt.InferenceSession(f.read(), providers=["CPUExecutionProvider"])
    except Exception:
        return None
    return amp, hemo


def available() -> bool:
    """True if the Macrel ONNX models can be loaded in this environment."""
    return _sessions() is not None


def _featurize(seqs: list[str]):
    """Compute Macrel's 22-feature matrix for a batch of sequences."""
    from macrel.macrel_features import compute_all, normalize_seq
    import numpy as np
    return np.array([compute_all(normalize_seq(s)) for s in seqs], dtype="float32")


def score_batch(seqs: list[str]) -> list[MacrelResult] | None:
    """Score a batch of peptides with the calibrated local Macrel models.

    Returns one MacrelResult per input, or None if Macrel is unavailable.
    Batched because ONNX inference amortises best over many rows at once.
    """
    sess = _sessions()
    if sess is None or not seqs:
        return None if sess is None else []
    amp_sess, hemo_sess = sess
    feats = _featurize(seqs)
    amp_out = amp_sess.run(["output_probability"], {"input_features": feats})[0]
    hemo_out = hemo_sess.run(["output_probability"], {"input_features": feats})[0]

    results: list[MacrelResult] = []
    for amp_map, hemo_map in zip(amp_out, hemo_out):
        amp_m = float(amp_map["AMP"])
        hemo_m = float(hemo_map["Hemo"])
        amp_like = _clip01((amp_m - _AMP_LO) / (_AMP_HI - _AMP_LO))
        nonhemo = _clip01((_HEMO_HI - hemo_m) / (_HEMO_HI - _HEMO_LO))
        results.append(MacrelResult(
            amp_margin=round(amp_m, 4),
            hemo_margin=round(hemo_m, 4),
            amp_like_score=round(amp_like, 4),
            nonhemo_score=round(nonhemo, 4),
            passes_amp_gate=amp_m >= AMP_MARGIN_GATE,
            passes_hemo_gate=hemo_m <= HEMO_MARGIN_GATE,
        ))
    return results


def score_one(seq: str) -> MacrelResult | None:
    """Score a single peptide. Returns None if Macrel is unavailable."""
    out = score_batch([seq])
    if out is None:
        return None
    return out[0] if out else None
