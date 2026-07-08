# Maintainer Runbook: Broken Docs Links

When doc links are broken:

1. Run `python scripts/check_doc_links.py` to find all broken links.
2. For each broken link, determine the correct target path.
3. Update the link in the source document.
4. If the target document was moved, add a redirect or update all references.
5. Re-run the check to confirm 0 broken links.
