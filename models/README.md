# Models Directory

No trained model weights are shipped in this starter repository.

Future model artifacts must follow `MODEL_RELEASE_POLICY.md`.

Recommended layout:

```text
models/
  manifests/           # model cards and version metadata
  local/               # ignored local-only weights
```

Do not commit high-capability generator weights or sensitive model artifacts without review.
