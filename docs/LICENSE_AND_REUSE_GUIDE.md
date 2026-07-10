# Public License and Reuse Guide

This document explains how OpenAMP Foundry artifacts and code are licensed, and how external teams may reuse, adapt, redistribute, or cite them.

## Repository license

The OpenAMP Foundry source code, documentation, schemas, and evidence artifacts are released under the **Apache License, Version 2.0** (the "License"). The full license text is in `LICENSE` at the repository root.

You may obtain a copy of the License at:

```
https://www.apache.org/licenses/LICENSE-2.0
```

Unless required by applicable law or agreed to in writing, software and materials distributed under this License are distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

## What you may do

Under Apache 2.0 you may:

- **Use** the code, schemas, and evidence artifacts for any purpose (commercial or non-commercial).
- **Reproduce and distribute** copies of the materials in source or compiled form.
- **Modify and create derivative works** — adapting schemas for your own pipeline, forking the repository, building on the tooling.
- **Sublicense** your derivative work under different terms, provided you comply with the attribution and notice requirements below.

## What you must do

If you use or distribute OpenAMP materials:

1. **Include the license.** Any distribution of the code or schemas must include the Apache 2.0 `LICENSE` file or a verbatim copy of the license text.
2. **Preserve copyright notices.** Do not remove or alter copyright statements in source files.
3. **State your changes.** If you modified the files, you must clearly state that changes were made. You may do so in a changelog, README, commit message, or other visible location.
4. **Cite the source.** We ask (though it is not legally required by Apache 2.0) that published research using OpenAMP outputs cites the repository and the specific artifact ID. See `docs/CITATION_TEMPLATE.md` for copy-paste formats.
5. **Do not imply endorsement.** You may not use OpenAMP contributor names, logos, or affiliation to imply that the OpenAMP project endorses your derivative work.

## What you must NOT do

- **Do not represent dry-lab candidates as biologically validated compounds.** Evidence certificates, FASTA exports, and benchmark outputs are computational nominees only. Redistributing them without this caveat would misrepresent the evidence.
- **Do not remove dry-lab disclaimers.** Any redistribution of evidence artifacts must preserve the `dry_lab_only: true` field and any associated human-readable caveats.
- **Do not add patent encumbrances** to derivative works in ways that prevent others from using the original Apache 2.0 code.

## Artifact-specific considerations

### Evidence certificates (CERT-)

Certificates are computational outputs documenting the dry-lab evidence trail. They may be reused, archived, and redistributed under Apache 2.0. Any redistribution must:

- Preserve the `dry_lab_only: true` assertion.
- Not modify the `proof_ladder_level` or evidence chain fields without re-issuing a new certificate with a new ID.
- Not strip `unsupported_claims` fields or `baseline_caveat` text.

### FASTA exports (FAE-)

Candidate sequences in FASTA format may be passed to partner lab analysis pipelines. Reuse must:

- Preserve the `;` comment lines indicating `dry_lab_only=true` and the candidate ID.
- Not assert biological activity based solely on the FASTA export.

### Schemas (`.schema.json`, Python modules)

JSON schemas and Python schema modules may be forked, adapted, and redistributed. If you modify a schema and publish the modified version, state clearly which fields or rules were changed and that the modified schema is not the canonical OpenAMP version.

### Benchmark cards (BMC-)

Benchmark card definitions document the measurement methodology. You may use them as templates but must not claim a benchmark was run under the OpenAMP protocol if you changed the evaluation procedure.

## Trademarks

"OpenAMP Foundry" is the project name used in this repository. It is not a registered trademark. Use of the name to describe the original project or to attribute work to the project is permitted. Use of the name to imply that a derivative project is the official OpenAMP Foundry is not permitted.

## Patents

As required by Apache 2.0, contributors grant a patent license for any patents embodied in their contribution. If you institute patent litigation against any contributor alleging that their contribution infringes a patent, your patent license for that contribution terminates automatically.

## Contributing

Contributions to this repository are subject to the Contributor Covenant Code of Conduct (see `docs/CONTRIBUTOR_COVENANT.md`) and are licensed to the project under Apache 2.0. By submitting a pull request, you agree that your contribution is offered under the same license.

## Questions

If you have a reuse question not covered here, open a GitHub issue with the label `reuse-question`. We will answer and, where useful, expand this guide.
