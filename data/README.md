# Data Directory

Do not commit third-party AMP databases here unless their licenses clearly allow redistribution.

Recommended layout for future local data:

```text
data/
  raw/                 # ignored or untracked external data
  processed/           # generated normalized data
  cards/               # dataset cards
```

For every external dataset, create a dataset card with:

- source;
- access date;
- license;
- redistribution status;
- citation requirement;
- preprocessing steps;
- known biases.
