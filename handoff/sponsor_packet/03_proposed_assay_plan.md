# Proposed Assay Plan

A minimal, standard validation panel for the candidate peptides.

## 1. Antibacterial activity — MIC (broth microdilution, CLSI M07)
Test strains (suggested, drug-resistant priority pathogens):
- *Escherichia coli* ATCC 25922 (Gram-negative reference)
- *Pseudomonas aeruginosa* ATCC 27853
- *Klebsiella pneumoniae* (carbapenem-resistant clinical isolate if available)
- *Staphylococcus aureus* ATCC 29213 + an MRSA isolate
- *Acinetobacter baumannii* (MDR isolate if available)

Controls: a known AMP (e.g. LL-37 or melittin) and a standard antibiotic.
Readout: MIC (µg/mL) in Mueller-Hinton broth. Run a parallel RPMI-1640 + 10% LB plate
for any proline-rich candidates (intracellular mechanism — flagged in the order table).

## 2. Hemolysis — HC50 vs human red blood cells
Serial dilution vs fresh hRBCs; readout = % hemolysis (A405) → HC50.
Compute the therapeutic index (HC50 / MIC). Melittin = hemolytic positive control.

## 3. Mammalian cytotoxicity — MTS/MTT
HEK293 or HepG2 viability across the MIC–10×MIC range.

## Synthesis notes
All peptides: N-terminal acetylation and/or C-terminal amidation as specified in
`01_synthesis_order_table.csv` (blocks exopeptidase / boosts stability — zero extra cost).
>=95% HPLC purity, TFA-free (acetate) counter-ion, ~5 mg each. Confirm identity by MS.
