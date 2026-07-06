"""Create external predictor results CSV template with Macrel data.
All 5 tools require manual web submission which cannot be automated.
Macrel local results are invalid due to known ONNX bug (see PR #77).
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PANEL_CSV = ROOT / "outputs" / "pilot_panel.csv"
RESULTS_CSV = ROOT / "outputs" / "external_predict_results.csv"

TOOLS = ["CAMPR4", "AMPScanner", "dbAMP", "AntiCP2", "Macrel", "HAPPENN"]

# Macrel local results (all NAMP due to ONNX bug — marked INVALID)
MACREL_RESULTS = {
    "SEED-009_VAR_033": "",
    "SEED-009_VAR_027": "",
    "SEED-007_VAR_009": "",
    "SEED-007_VAR_001": "",
    "SEED-007_VAR_018": "",
    "SEED-009_VAR_039": "",
    "SEED-009_VAR_017": "",
    "SEED-007_VAR_035": "",
    "SEED-006_VAR_059": "",
    "SEED-006_VAR_071": "",
    "SEED-006_VAR_062": "",
    "SEED-006_VAR_006": "",
    "SEED-008_VAR_032": "",
    "SEED-008_VAR_009": "",
    "SEED-008_VAR_019": "",
    "SEED-003_VAR_017": "",
    "SEED-003_VAR_012": "",
    "SEED-008_VAR_044": "",
    "SEED-005_VAR_019": "",
    "SEED-001_VAR_064": "",
}


def main():
    panel = []
    with open(PANEL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            panel.append(row)

    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(TOOLS)
        for p in panel:
            cid = p["candidate_id"]
            macrel = MACREL_RESULTS.get(cid, "")
            # All tools blank — Macrel results are INVALID (ONNX bug)
            # Fill in manually after web submission
            writer.writerow([cid, "", "", "", "", macrel, ""])

    print(f"Created {RESULTS_CSV}")
    print("Instructions:")
    print("  1. Submit outputs/pilot_panel.fasta to each tool:")
    print("     - CAMPR4: http://www.camp3.bicnirrh.res.in/predict.php")
    print("     - AMPScanner v2: https://www.dveltri.com/ascan/v2/ascan.html")
    print("     - dbAMP 2.0: https://awi.cuhk.edu.cn/dbAMP/predict.php")
    print("     - AntiCP 2.0: https://webs.iiitd.edu.in/raghava/anticp2/")
    print("     - Macrel: https://big-data-biology.org/software/macrel (web server, NOT local CLI)")
    print("  2. Fill Y/N in each tool column per candidate")
    print("  3. Run: make external-consensus RESULTS=outputs/external_predict_results.csv")
    print("  4. Gate 6 will then pass/fail for real")


if __name__ == "__main__":
    main()
