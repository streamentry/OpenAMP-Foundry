# External Result Cache Manifest

Records cached results from external adapter calls.

## Format
```json
{
  "cache_version": "1.0",
  "created_at": "ISO 8601",
  "entries": [
    {
      "adapter": "adapter_name",
      "sequence": "peptide_sequence",
      "result_hash": "sha256_of_result",
      "cached_at": "ISO 8601",
      "ttl_seconds": 86400
    }
  ]
}
```

## Rules
- Cache entries should have a TTL (time-to-live).
- Cached results should be validated against the adapter schema.
- Cache should be invalidated when the adapter version changes.
- Cached results must be clearly labeled as cached.
- Cache location: `outputs/adapter_cache/`.
