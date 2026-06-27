# Model Release Policy

## Open by default

The following are intended to be open:

- data loaders;
- benchmark code;
- schemas;
- transparent baseline scorers;
- evidence certificate tooling;
- safety filters;
- documentation.

## Restricted, delayed, or withheld by default

The following are not released by default:

- high-throughput generator weights;
- objective functions that could optimize harmful biological properties;
- unscreened top candidate lists;
- model checkpoints trained on sensitive or restricted data;
- tooling that materially increases misuse capability.

## Release review questions

Before releasing any model or candidate batch, answer:

1. Could this artifact be used to increase biological harm?
2. Does it include safety filters by default?
3. Can it be used responsibly without wet-lab expertise?
4. Are the limitations clear?
5. Is staged release safer?
6. Should an external domain expert review it first?

## Labeling

Do not call restricted model artifacts “open source.” Use “responsible source,” “controlled access,” or “responsible open science.”
