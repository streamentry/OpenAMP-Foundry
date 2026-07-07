# Metric Guide: Navigation Health

**Question:** Can a reader find the document they need without searching?

**What to track:** Whether all docs are linked from PROJECT_INDEX.md.

**Target:** 100% of documents in docs/ are indexed in PROJECT_INDEX.md.

**How to measure:** Compare `find docs/ -name "*.md"` against links in PROJECT_INDEX.md.

**What good looks like:** A new reader can navigate from PROJECT_INDEX.md to any document in one or two clicks.
