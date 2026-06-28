from __future__ import annotations

from typing import Any

from openamp_foundry.scoring.activity import clamp01


def serum_stability_score(features: dict[str, Any]) -> float:
    """Predict relative stability against serum/tissue proteases from site density.

    Short cationic AMPs face three major proteolytic threats in biological fluids:
    1. Serum trypsin (K/R sites): dominant degradation route in blood/plasma.
    2. Serum chymotrypsin (F/W/Y sites): secondary serum route.
    3. Neutrophil elastase (A/V/S sites): abundant at infection sites; degrades
       helix-forming AMPs with high Ala content significantly faster than serum
       trypsin alone predicts.

    Weights reflect relative proteolytic efficiency for short cationic peptides:
    trypsin 2.0 > chymotrypsin 1.0 > elastase 0.5

    Literature basis:
    - Hilpert et al. (2006) J Antimicrob Chemother: short cationic peptides with
      ≥3 interior K/R sites typically have serum t½ < 30 min.
    - Wade et al. (1990) PNAS: D-amino acid substitution extends t½ by >10×.
    - Bieth (1986) Bull Eur Physiopathol Respir; Doherty et al. (1991) Biochemistry:
      HNE cleaves Ala > Val > Ser; abundant at infection sites (>1 μM).

    Returns a value in [0, 1]:
      1.0 = no interior cleavage sites
      0.5 = moderate combined site density (~0.25 per residue)
      0.0 = very high combined site density (≥0.5 per residue)

    This score is informational — it does not gate the ensemble.
    Use it to stratify candidates by predicted proteolytic longevity.
    """
    length = features.get("length", 0)
    if not length:
        return 1.0

    trypsin_density = features.get("trypsin_site_density", 0.0)
    chymo_density = features.get("chymotrypsin_site_density", 0.0)
    # Elastase density: pre-normalised by compute_features(); defaults 0 for backward compat.
    elastase_density = features.get("elastase_site_density", 0.0)

    # Weighted sum: trypsin 2 : chymotrypsin 1 : elastase 0.5 (denominator = sum of weights)
    combined_density = (2.0 * trypsin_density + 1.0 * chymo_density + 0.5 * elastase_density) / 3.5

    # At combined_density ≈ 0.5 (every other residue is a cleavage site), score → 0
    score = 1.0 - clamp01(combined_density / 0.5)
    return round(score, 4)
