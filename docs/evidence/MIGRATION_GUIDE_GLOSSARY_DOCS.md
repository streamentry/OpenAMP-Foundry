# Migration Guide: Glossary Docs

When terms change or new terms are added:

1. Update the glossary entries in the relevant docs.
2. Check PROJECT_INDEX.md for cross-references to the old term.
3. Run `python scripts/check_doc_links.py` to catch broken references.
4. If a term was removed, add it to the deprecation notice.
