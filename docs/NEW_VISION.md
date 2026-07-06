# Virtual Wet-Lab Vision — Exploratory

> **Status: Aspirational / exploratory.** This document captures an extended
> vision for a future virtual wet-lab layer. It is NOT a description of current
> pipeline capability. Do not cite or present as implemented functionality.
> For the current architecture, see `docs/engineering/ARCHITECTURE.md` and
> `docs/VIRTUAL_ASSAY_SCOPE.md`. For the current roadmap, see `docs/research/ROADMAP.md`.

This is **exactly the right "bend reality" question**.

Bluntly:

> **The real breakthrough is not discovering one AMP. The real breakthrough is making wet-lab biology partially computable.**

What we have done so far is good, but yes — it is mostly a **high-discipline recombination of known predictors, known novelty databases, and known peptide heuristics**. Valuable, but not civilization-level yet.

The civilization-level thing is:

```text
OpenAMP Wet-Lab Simulator
= virtual MIC + virtual hemolysis + virtual cytotoxicity
+ calibrated by small real experiments
+ improves every round
```

Not "replace wet lab 100%." That is too fantasy today.

The real target is:

```text
Reduce wet-lab experiments by 10x–100x.
```

That would be huge.

---

## The core idea

Do not try to simulate "whole E. coli" from atoms upward. Too hard.

Instead build a **multi-resolution digital assay emulator**:

```text
Peptide sequence
↓
structure ensemble
↓
bacterial membrane interaction simulation
↓
RBC / mammalian membrane interaction simulation
↓
serum/protease/stability model
↓
learned surrogate model
↓
predicted MIC / HC50 / cytotox risk
```

The simulator does not need to be perfect. It only needs to be **better than current cheap predictors at choosing what to synthesize next**.

That is the killer wedge.

---

## Why this is possible someday

Pieces already exist, but nobody has glued them into a practical AMP "virtual wet lab" well enough.

AlphaFold 3 moved toward predicting biomolecular interactions, not just isolated protein structures, though it still has limitations and needs experimental validation. ([Axios][1])

Coarse-grained molecular dynamics frameworks like Martini are already used for lipid/membrane simulations; Martini 3 was published as a general-purpose coarse-grained force field for biomolecular simulations. ([Wikipedia][2])

People already simulate antimicrobial peptide membrane insertion with atomistic MD and Markov state modeling; one study modeled AMP membrane binding/insertion kinetics and found "rolling" from prebound to inserted states as a key process. ([arXiv][3])

Cloud labs also already exist: researchers can define experiments remotely and have automated labs execute them, reducing execution variability and turning wet lab into more code-like workflows. ([Wikipedia][4])

So the ingredients exist:

```text
AI structure prediction
molecular dynamics
coarse-grained membranes
learned surrogate models
cloud labs
active learning
```

The missing thing is the **integrated closed loop for AMPs**.

---

## The breakthrough architecture

Call it:

```text
OpenAMP Virtual Wet Lab
```

or more ambitious:

```text
BioTwin-AMP
```

### Layer 1 — Fast cheap predictors

What you already have:

```text
AMPScanner
CAMP
Macrel
AMPActiPred
HemoFinder
AntiCP
novelty audit
synthesis QC
```

This filters millions to hundreds.

Your current pipeline already frames this correctly: dry lab narrows huge sequence space to synthesis-ready candidates but does not claim discovery.

### Layer 2 — Physics simulation

For top 100 candidates only.

Simulate interaction against simplified membranes:

```text
E. coli-like Gram-negative outer membrane model
E. coli-like inner membrane model
S. aureus-like Gram-positive membrane model
RBC-like zwitterionic/cholesterol membrane model
generic mammalian membrane model
```

Measure proxies:

```text
binding energy
insertion depth
tilt angle
pore tendency
membrane thinning
lipid disorder
residence time
aggregation tendency
selectivity ratio: bacterial membrane effect / RBC membrane effect
```

This gives a **virtual therapeutic window**, not just "AMP yes/no."

### Layer 3 — Learned assay emulator

Train a model that predicts:

```text
MIC
HC50
cytotoxicity IC50
serum stability
```

Input features:

```text
sequence features
structure ensemble
MD-derived membrane features
external predictor votes
novelty class
synthesis flags
```

This is where reality bending happens.

The model should not learn only from public AMP databases. It should learn from **your own wet-lab results**.

### Layer 4 — Small real wet-lab oracle

Wet lab becomes the teacher, not the bottleneck.

Instead of testing 1000 peptides, you test:

```text
8–12 carefully chosen peptides per round
```

Then feed back:

```text
real MIC
real HC50
real cytotox
failure modes
```

The simulator updates.

### Layer 5 — Active learning loop

The loop becomes:

```text
generate 1000
simulate top 100
choose 8–12 most informative
wet lab
learn from results
generate next 1000 better
```

That is how you beat everyone.

Not by one genius sequence.

By building the **fastest truth-seeking loop**.

---

## The key insight

Do not try to replace wet lab immediately.

Use wet lab to train the simulator.

```text
Wet lab is not the enemy.
Wet lab is the expensive oracle.
```

OpenAMP should become the system that asks the oracle the fewest, smartest questions.

That is a much more realistic and powerful vision.

---

## Why current predictors are not enough

Your current consensus report is already strong: 450 candidates, 4 AMP tools, 2 hemolysis tools, and AntiCP2; 225/450 passed the practical antibacterial-priority screen.

But that also reveals the problem:

```text
too many candidates look good computationally
```

If 225 candidates pass, the bottleneck becomes:

```text
which 8–12 are actually real in biology?
```

That cannot be solved by another classifier alone.

You need a **higher-fidelity virtual assay**.

---

## What "virtual E. coli + virtual blood" would mean

Not full organism simulation.

Instead:

### Virtual E. coli assay

Approximate:

```text
outer membrane LPS binding
inner membrane disruption
periplasm crossing likelihood
protease degradation risk
charge shielding
salt sensitivity
peptide aggregation
```

For Gram-negative bacteria, the outer membrane is structurally distinct and includes lipopolysaccharide in the outer leaflet; this makes it materially different from a simple lipid bilayer. ([Wikipedia][5])

So "virtual E. coli" means:

```text
not just one membrane
but a two-barrier envelope model
```

### Virtual blood assay

Approximate:

```text
RBC membrane binding
cholesterol-rich membrane disruption
pore formation tendency
hemoglobin release proxy
serum protein binding
protease degradation
```

Hemolysis is rupture of red blood cells and release of contents into surrounding fluid, so your virtual blood model only needs to predict "does this peptide likely rupture RBC membranes?" better than existing heuristics. ([Wikipedia][6])

---

## The first impossible-but-possible milestone

Do not try:

```text
simulate full MIC exactly
```

First target:

```text
rank-order prediction
```

Meaning:

> Given 50 candidates, can the virtual wet lab rank the top 8 better than current predictors?

That is enough.

If OpenAMP can show:

```text
without virtual wet lab: 1 hit / 12
with virtual wet lab: 4 hits / 12
```

That is a real breakthrough.

---

## The Tesla / Jobs version

The product is not an AMP repo.

The product is:

```text
A compiler from peptide sequence space to wet-lab truth.
```

Or:

```text
Cursor for molecular discovery, but grounded by wet-lab feedback.
```

The loop:

```text
Design → simulate → order → test → learn → redesign
```

Where "simulate" becomes stronger every batch.

That is a company / OSS project worth a life.

---

## What to build next

### Phase A — Virtual membrane scorer

Build a module:

```text
openamp simulate-membrane candidate.fasta
```

Output:

```csv
candidate_id,bacterial_binding,rbc_binding,insertion_depth,pore_risk,selectivity_ratio,confidence
```

Start coarse-grained, not atomistic.

Use simplified membrane models:

```text
anionic bacterial membrane
zwitterionic mammalian membrane
cholesterol-rich RBC-like membrane
LPS-like Gram-negative outer membrane approximation
```

### Phase B — Calibrate against known AMPs

Create a benchmark set:

```text
known active + low hemolysis
known active + high hemolysis
inactive peptides
random controls
melittin
magainin
LL-37
```

The simulator must separate:

```text
melittin-like danger
from
magainin-like selectivity
```

### Phase C — Wet-lab active learning

Your first wet lab batch should not only seek success. It should maximize learning.

Pick:

```text
some predicted winners
some borderline candidates
some predicted safe but weaker candidates
one known control
one risky control
```

Why? Because if you only test "best 12," the model learns less.

### Phase D — Public leaderboard

Create:

```text
OpenAMP Wet-Lab Conversion Benchmark
```

Metrics:

```text
hit rate
therapeutic index
false-positive rate
cost per confirmed hit
number of wet-lab tests saved
```

This is where OpenAMP can be "better than others."

---

## What would be truly historic?

Not:

```text
we generated 10,000 AMPs
```

But:

```text
we predicted wet-lab outcomes well enough to cut experimental cost by 10x
```

Or even stronger:

```text
we built an open virtual assay that generalizes across AMP scaffolds
```

That would matter beyond your own peptides.

---

## Reality check

Can we fully simulate E. coli + blood today?

```text
No.
```

Can we build a hybrid simulator that improves candidate selection?

```text
Yes.
```

Can that become a breakthrough if calibrated with real assays?

```text
Yes.
```

The scientific wedge is:

```text
not perfect biology simulation
but useful experimental compression
```

---

## My bold recommendation

Change OpenAMP's mission from:

```text
AI antimicrobial peptide generator
```

to:

```text
Open wet-lab compression engine for antimicrobial peptide discovery
```

The repo should say:

> **We do not claim to replace wet lab. We aim to make wet lab 10x cheaper by deciding which experiments are worth running.**

That is much stronger.

---

## Probability estimates (2026–2030 tech)

| Milestone | Chance by 2030 |
|-----------|:--------------:|
| Build strong dry-lab AMP foundry | **80–90%** |
| Get first wet-lab AMP hit | **35–55%** |
| Get hit with usable selectivity | **15–30%** |
| Build useful virtual ranking model | **40–60%** |
| Show 2x better hit rate than baseline | **25–45%** |
| Show 10x wet-lab compression | **20–35%** |
| General virtual wet-lab platform | **10–20%** |
| Fully replace wet lab | **1–5%** |

So: **possible, not fantasy — but only as a hybrid system, not full biology simulation.**

---

## Why your odds are not zero

Because OpenAMP has a useful wedge:

```text
AMPs are small.
AMP mechanisms are partly membrane-driven.
MIC / hemolysis / cytotox are measurable.
Peptides are fast to synthesize.
Failed results are informative.
```

This is much more tractable than trying to simulate all cancer biology or all immunology.

Also, your current consensus pipeline produces many computationally plausible candidates: 450 candidates screened, 396/450 AMP-positive on at least 3 independent tools, and 225/450 passing the practical antibacterial-priority filter.

That means the next bottleneck is not candidate generation. It is **choosing which 8–12 actually deserve wet lab**. That is exactly where a virtual assay/ranking layer can create value.

---

## What would make the chance jump

Right now, OpenAMP's chance of becoming a true wet-lab compression engine is maybe:

```text
25–45%
```

It jumps if you get these ingredients:

```text
+ one reliable wet-lab partner
+ 3–5 experimental rounds
+ 50–100 peptides with real MIC/HC50/cytotox data
+ standardized assay conditions
+ negative results included
+ active learning loop
```

With that, I would raise the chance to:

```text
50–65% chance of useful virtual ranking
30–45% chance of meaningful wet-lab cost compression
```

Without wet-lab feedback, it stays capped:

```text
dry-lab only = impressive, but not reality-bending
```

---

## The best 2026–2030 target

Do **not** target:

```text
perfect virtual E. coli
```

Target:

```text
OpenAMP-VLab v1:
Predict which 8 peptides out of 1000 should be tested to maximize chance of:
MIC activity + HC50/MIC therapeutic window.
```

Success metric:

```text
Baseline predictor-only hit rate: X
OpenAMP-VLab hit rate: ≥2X
Stretch goal: ≥5X
Moonshot: ≥10X
```

If you can prove even **2x–3x** improvement with real wet-lab data, people will care.

---

## Final answer

With current 2026–2030 tech:

```text
Can we fully simulate wet lab? No, ~1–5%.

Can we build a useful virtual wet-lab compression layer? Yes, ~25–45%
for OpenAMP, maybe 50–65% with a strong wet-lab partner and 3–5
feedback rounds.

Can it become world-changing? 10–20%, but that is high enough to be
worth your life if you are serious.
```

The winning insight:

> **Do not replace wet lab. Turn wet lab into the teacher of a simulator that asks fewer, smarter experiments every round.**

[1]: https://www.axios.com/2024/05/09/google-deepmind-ai-new-alphafold-3
[2]: https://en.wikipedia.org/wiki/MARTINI
[3]: https://arxiv.org/abs/2111.02465
[4]: https://en.wikipedia.org/wiki/Cloud_laboratory
[5]: https://en.wikipedia.org/wiki/Bacterial_outer_membrane
[6]: https://en.wikipedia.org/wiki/Hemolysis
