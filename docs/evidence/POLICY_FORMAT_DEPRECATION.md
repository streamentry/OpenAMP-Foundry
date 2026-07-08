# Artifact Format Deprecation Policy

How artifact formats are deprecated and retired.

## Deprecation Process
1. Announce the deprecation in the decision log and release notes.
2. Keep the old format working for one release cycle.
3. Provide a migration path or converter.
4. After one release cycle, remove the old format support.
5. Update all documentation referencing the old format.

## Rules
- Breaking format changes must be announced at least one release in advance.
- Deprecated formats must still be readable for one release cycle.
- Format changes must be documented in the schema changelog.
- Data in old formats should be migrated automatically when possible.
