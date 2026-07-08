# Docs Navigation Audit Guide

How to audit documentation navigation.

## Checklist
- [ ] PROJECT_INDEX.md lists all active documents.
- [ ] Each document category has a hub page.
- [ ] Every document has at least one incoming link from an index.
- [ ] No document is orphaned (no incoming links).
- [ ] Navigation paths are logical (start -> next -> next).
- [ ] Related documents are cross-linked.

## Process
1. Run `python scripts/check_doc_links.py` to find broken links.
2. Check PROJECT_INDEX.md against `find docs/ -name "*.md"`.
3. For each document not in PROJECT_INDEX.md, add it or archive it.
4. For each document with no incoming links, add cross-references.
5. Update navigation paths if the document structure has changed.
