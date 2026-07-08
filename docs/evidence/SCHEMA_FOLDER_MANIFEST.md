# Artifact Manifest Schema for Generated Folders

Schema for manifests that describe generated output folders.

## Format
```json
{
  "folder": "outputs/",
  "generated_at": "ISO 8601",
  "file_count": 5,
  "total_size_bytes": 1024000,
  "files": {
    "ranked.jsonl": {"size": 500000, "hash": "sha256:..."},
    "report.md": {"size": 20000, "hash": "sha256:..."},
    "manifest.json": {"size": 500, "hash": "sha256:..."}
  }
}
```

## Required Fields
- `folder` — path to the generated folder
- `generated_at` — when the manifest was created
- `file_count` — number of files in the folder
- `files` — dict of filename to metadata (size, hash)

## Rules
- Generate this manifest after running batch commands.
- Use the manifest to verify folder contents before sharing.
- If files are missing or hashes don't match, regenerate.
