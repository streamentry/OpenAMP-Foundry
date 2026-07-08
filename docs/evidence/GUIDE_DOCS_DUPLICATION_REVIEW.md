# Docs Duplication Review Guide

How to find and resolve documentation duplication.

## Signs of Duplication
- Same concept described in multiple documents.
- Same policy stated in different words in different places.
- Same procedure documented in multiple runbooks.
- Cross-references that point to each other (circular).

## Resolution
1. Identify which document is the authoritative source.
2. Keep the content in the authoritative source.
3. Replace duplicate content with a cross-reference.
4. If the duplicate contains unique information, merge it into the authoritative source.
5. Update all cross-references to point to the single source.

## Prevention
- Before creating a new document, check if the content already exists.
- Use cross-references instead of copying content.
- Maintain a source-of-truth map (see DOC_MAP_SOURCE_OF_TRUTH.md).
