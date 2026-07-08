# Release Blocker Taxonomy

Types of issues that can block a release.

| Blocker Type | Description | Resolution |
|-------------|-------------|-----------|
| Safety | Overclaiming language, safety policy error | Fix before release |
| Quality | Failing tests, broken links, benchmark regression | Fix before release |
| Completeness | Missing artifact or documentation | Complete before release |
| Process | Review not completed, decision not logged | Complete before release |
| Dependency | External dependency is broken or unavailable | Wait or work around |

## Decision Rules
- Any Safety blocker → do not release
- Any Quality blocker → do not release
- Completeness blockers → evaluate impact; minor gaps can be deferred
- Process blockers → complete before release
- Dependency blockers → evaluate urgency; may block or delay
