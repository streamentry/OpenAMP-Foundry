# Migration Guide: README to Docs

When moving content from README.md to docs/:

1. Create the new doc in the appropriate subdirectory.
2. Link to the new doc from README.md.
3. Update any cross-references that pointed to the old location.
4. Run `python scripts/check_doc_links.py` to verify links.
5. Do not delete README.md — keep it as a navigation hub.
