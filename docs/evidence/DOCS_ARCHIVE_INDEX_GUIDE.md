# Docs Archive Index Guide

When archiving documents, maintain this index.

## Archive Location
Archived docs go in `docs/archive/` with a date prefix.

## Index Format
```csv
original_path,archive_path,archived_date,reason,superseded_by
```

## Required Information
- Original document path
- Archive path with date
- Date of archiving
- Reason for archiving (deprecated, superseded, obsolete)
- If superseded, the path to the replacement document

## Search
The archive index should be searchable. Consider adding it to PROJECT_INDEX.md
with an `(archived)` marker.
