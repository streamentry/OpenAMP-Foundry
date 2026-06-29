"""Generate scrambled decoys for expanded AMP set. Run after expand_benchmark.py."""

import csv
import random
from pathlib import Path

KNOWN_AMPS_PATH = Path("examples/validation/known_amps.csv")
SCRAMBLED_PATH = Path("examples/validation/scrambled_decoys.csv")

RNG_SEED = 42  # Must match original seed


def scramble(seq: str, rng: random.Random) -> str:
    """Shuffle amino acid order, ensuring result differs from original."""
    chars = list(seq)
    for _ in range(100):
        rng.shuffle(chars)
        shuffled = "".join(chars)
        if shuffled != seq:
            return shuffled
    return "".join(rng.sample(chars, len(chars)))


def main():
    rng = random.Random(RNG_SEED)

    # Read existing scrambles
    existing_amplic_ids = set()
    with open(SCRAMBLED_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_amplic_ids.add(row["source_id"])

    # Read all AMPs
    new_amplic_ids = set()
    amps = []
    with open(KNOWN_AMPS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            amps.append(row)
            new_amplic_ids.add(row["id"])

    # Find AMPs without scrambles
    missing_ids = new_amplic_ids - existing_amplic_ids
    print(f"Existing scrambles: {len(existing_amplic_ids)}")
    print(f"Total AMPs: {len(new_amplic_ids)}")
    print(f"Missing scrambles: {len(missing_ids)}")

    if not missing_ids:
        print("No scrambles to add.")
        return

    # Append missing scrambles
    with open(SCRAMBLED_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        added = 0
        for amp in amps:
            if amp["id"] not in missing_ids:
                continue
            seq = amp["sequence"]
            shuffled = scramble(seq, rng)
            family_prefix = amp["family"].replace(" ", "_").replace("-", "_")
            writer.writerow([
                f"DECOY-{amp['id']}",
                shuffled,
                f"shuffled_{family_prefix}",
                amp["id"],
                "0",
            ])
            added += 1

    # Verify total
    total_scrambles = 0
    with open(SCRAMBLED_PATH, newline="", encoding="utf-8") as f:
        total_scrambles = sum(1 for _ in csv.DictReader(f))
    print(f"Added {added} scrambles; total now {total_scrambles} (AMP count: {len(amps)})")


if __name__ == "__main__":
    main()
