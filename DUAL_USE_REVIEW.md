# Dual-Use Review Checklist

Before publishing a new module, dataset, model, or candidate batch, review:

| Question | Yes/No | Action if yes |
|---|---|---|
| Does it optimize harmful biological traits? |  | Do not publish |
| Does it include pathogen-handling instructions? |  | Do not publish |
| Does it produce unscreened high-risk candidates? |  | Gate or delay |
| Could it be misread as medical advice? |  | Rewrite |
| Does it bypass expert review? |  | Add review gate |
| Does it lack clear limitations? |  | Add limitations |
| Does it include third-party data with unclear license? |  | Remove or replace |
| Does it provide enough reproducibility for benign science? |  | Improve docs |

Approval should require at least one technical maintainer and one domain/safety reviewer for high-impact releases.
