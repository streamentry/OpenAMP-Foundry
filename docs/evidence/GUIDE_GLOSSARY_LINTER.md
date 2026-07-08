# Glossary Term Linter

Checks that glossary terms are used consistently across documentation.

## How It Works
The linter scans markdown files for project-specific terms and checks
that they match the canonical form defined in the glossary.

## Terms to Check
| Canonical | Also Seen | Correction |
|-----------|-----------|------------|
| evidence certificate | cert, evidence file | Use "evidence certificate" |
| ensemble score | combined score, total score | Use "ensemble score" |
| simulation mode | sim mode, virtual mode | Use "simulation mode" |
| calibration gate | recalibration gate | Use "calibration gate" |
| pass/fail criteria | acceptance criteria | Use "pass/fail criteria" |

## Usage
Manual review is currently required. Future automation could use grep
or a custom linter script.
