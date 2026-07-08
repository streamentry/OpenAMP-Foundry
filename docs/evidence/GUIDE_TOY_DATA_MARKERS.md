# Toy Data Marker Guide

Toy and demo data must be clearly marked to avoid confusion with real data.

## Required Markers
- File header or disclaimer: `SYNTHETIC` or `DEMO`
- Source field: `toy`, `demo`, or `synthetic`
- No toy data should have a source that implies real biological data

## Where to Apply
- Demo candidate CSVs
- Demo reference CSVs
- Synthetic lab results
- Test fixtures

## Examples
```csv
candidate_id,sequence,source
DEMO-001,ACDEFGHIKLMNPQRSTVWY,demo
```
```json
{"disclaimer": "SYNTHETIC — replace with real data"}
```
