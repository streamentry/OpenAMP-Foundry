"""Build unified AMP reference library from all known sequence sources.

Combines:
  - examples/known_reference/amp_curated_references.csv (72 curated AMPs)
  - examples/validation/known_amps.csv (95 expanded benchmark AMPs)
  
Deduplicates by sequence (first occurrence wins). Adds library_source column
to track provenance.

Output: examples/known_reference/amp_library.csv
"""

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CURATED_CSV = REPO_ROOT / "examples" / "known_reference" / "amp_curated_references.csv"
EXPANDED_CSV = REPO_ROOT / "examples" / "validation" / "known_amps.csv"
DEMO_CSV = REPO_ROOT / "examples" / "known_reference" / "demo_known_amps.csv"
OUT_CSV = REPO_ROOT / "examples" / "known_reference" / "amp_library.csv"


def load_csv(path: Path, source_label: str, dedup: set) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seq = row.get("sequence", "").upper().strip()
            if not seq or seq in dedup:
                continue
            dedup.add(seq)
            rows.append({
                "id": row.get("id", ""),
                "sequence": seq,
                "family": row.get("family", row.get("source", "")),
                "source": row.get("reference", row.get("source", "")),
                "taxonomy_class": _infer_taxonomy(row.get("family", ""), row.get("id", "")),
                "library": source_label,
            })
    return rows


def _infer_taxonomy(family: str, id_str: str) -> str:
    """Infer taxonomic origin from family string and ID using substring matching.

    Order matters: more specific keywords must come before generic ones
    (e.g. 'tenecin' in insect BEFORE 'bactenecin' in mammalian; but 'bactenecin'
    is explicitly added to mammalian to override the substring collision).
    """
    f = family.lower()
    i = id_str.lower()

    # Human
    if any(x in f for x in ["human_defensin", "hbd-1", "hbd-2", "hbd-3",
                             "beta_defensin_human", "histatin",
                             "hepcidin", "dermcidin", "cathelicidin"]):
        return "human"

    # Frog (buforin (toad), maximin)
    if any(x in f for x in ["magainin", "pexiganan", "temporin", "brevinin",
                             "esculentin", "gaegurin", "ranalexin", "japonicin",
                             "phylloseptin", "dermaseptin", "nigrocin", "rugosin",
                             "aurein", "caerin", "maculatin", "bombinin", "uperin",
                             "buforin", "maximin"]):
        return "frog"

    # Insect — note: 'tenecin' catches 'tenecin_1' (Tenebrio) but also
    # matches 'bactenecin'. 'bactenecin' is added to mammalian to override.
    if any(x in f for x in ["apidaecin", "drosocin", "formaecin", "thanatin",
                             "defensin_a", "hymenoptaecin",
                             "melittin", "scorpion", "pyrrhocoricin",
                             "oncocin", "cecropin", "silkworm"]):
        return "insect"
    # tenecin (insect) must be after bactenecin exclusion
    if "tenecin" in f and "bactenecin" not in f:
        return "insect"

    # Mammalian — 'bactenecin' must be here (overrides 'tenecin' causing false insect match)
    if any(x in f for x in ["bactenecin", "bac7", "bac5",
                             "bmaps", "bmap_27", "bmap_28", "smap_29",
                             "pmap_23", "pmap_36", "oabac_5", "oabac_11",
                             "protegrin", "pr_39", "indolicidin",
                             "cathelicidin", "bovine", "sheep", "porcine",
                             "murine", "cramp", "hlp", "smap", "bmap"]):
        return "mammalian"

    # Defensin (generic — after insect defensin_a and human defensins)
    if "defensin" in f:
        return "mammalian"

    # Human LL-37 / cathelicidin (already handled above)
    if any(x in f for x in ["ll37", "ll-37", "human"]):
        return "human"

    # Plant
    if any(x in f for x in ["rsafp", "ace-amp", "ace_amp1", "snakin", "thionin", "plant"]):
        return "plant"

    # Fungal
    if any(x in f for x in ["plectasin", "eurocin", "fungal"]):
        return "fungal"

    # Fish
    if any(x in f for x in ["pleurocidin", "piscidin", "moronecidin", "fish"]):
        return "fish"

    # Marine invertebrate
    if any(x in f for x in ["tachyplesin", "polyphemusin", "arenicin",
                             "horseshoe", "marine", "clavanin"]):
        return "marine_invertebrate"

    # Bacterial
    if any(x in f for x in ["nisin", "lantibiotic", "bacteriocin", "gramicidin", "bacterial"]):
        return "bacterial"

    # Synthetic / designed
    if any(x in f for x in ["tryptophan_rich", "template_seed", "klaklak",
                             "short_cationic", "ala_lys_repeat", "cecropin_core",
                             "omiganan", "bp100", "chimera", "designed",
                             "engineered", "cm15", "cationic_tryptophan"]):
        return "synthetic"

    # Linear (generic catch-all)
    if "linear" in f:
        return "mammalian"
        return "frog"
    if any(x in f for x in ["msi", "msi_594"]):
        return "frog"
    if any(x in f for x in ["murine", "cramp"]):
        return "mammalian"
    if any(x in f for x in ["oncocin", "pyrrhocoricin", "proline_rich_oncocin"]):
        return "insect"
    if any(x in f for x in ["cationic_tryptophan"]):
        return "synthetic"
    if any(x in f for x in ["ace_amp1", "ace-amp"]):
        return "plant"
    # Default based on ID pattern
    if i.startswith("ref-drs") or i.startswith("ref-brv") or i.startswith("ref-gae"):
        return "frog"
    if i.startswith("ref-tmp"):
        return "frog"
    if i.startswith("ref-buf"):
        return "frog"
    if i.startswith("ref-mel") or i.startswith("ref-api") or i.startswith("ref-bom"):
        return "insect"
    if i.startswith("ref-kin") or i.startswith("ref-kla") or i.startswith("ref-rlk"):
        return "synthetic"
    return "unknown"


def main():
    dedup: set = set()
    all_rows = []

    # Load in priority order (first occurrence wins on dedup)
    all_rows.extend(load_csv(CURATED_CSV, "curated_72", dedup))
    all_rows.extend(load_csv(EXPANDED_CSV, "expanded_95", dedup))
    all_rows.extend(load_csv(DEMO_CSV, "demo_3", dedup))

    # Sort by library, then by id
    all_rows.sort(key=lambda r: (r["library"], r["id"]))

    # Write
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "sequence", "family", "source", "taxonomy_class", "library",
        ])
        writer.writeheader()
        writer.writerows(all_rows)

    # Stats
    from collections import Counter
    lib_counts = Counter(r["library"] for r in all_rows)
    tax_counts = Counter(r["taxonomy_class"] for r in all_rows)

    print(f"AMP library built: {len(all_rows)} unique sequences")
    print(f"  Sources: {', '.join(f'{k}={v}' for k, v in lib_counts.most_common())}")
    print(f"  Taxonomy: {', '.join(f'{k}={v}' for k, v in tax_counts.most_common())}")
    print(f"  Output: {OUT_CSV}")


if __name__ == "__main__":
    main()
