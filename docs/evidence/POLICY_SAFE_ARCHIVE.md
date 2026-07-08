# Safe Archive Extraction Policy

How to safely extract archives in the pipeline.

## Rules
- Only extract archives from trusted sources.
- Validate archive contents before extraction.
- Prevent path traversal attacks (no `../` in extracted paths).
- Set a maximum file size and count.
- Extract to a dedicated directory, not to an existing directory tree.
- Verify extracted file hashes against expected values when available.

## Implementation
- The `build_lab_batch_pack.py` script creates ZIP archives.
- Extraction should use `zipfile.ZipFile.extractall()` with path validation.
- Path traversal is prevented by checking that all extracted paths are within the target directory.
