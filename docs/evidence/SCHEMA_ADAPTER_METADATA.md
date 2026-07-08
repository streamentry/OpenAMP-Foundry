# Adapter Metadata Schema

Standard metadata fields for external adapters.

## Required Fields
| Field | Type | Description |
|-------|------|-------------|
| name | string | Adapter name |
| version | string | Adapter version |
| type | string | simulation, external_api, local_process |
| requires_network | boolean | Whether network access is needed |

## Optional Fields
| Field | Type | Description |
|-------|------|-------------|
| timeout | integer | Default timeout in seconds |
| retry_count | integer | Number of retries on failure |
| rate_limit | integer | Maximum requests per minute |
| dependencies | list | Required Python packages |

## Example
```json
{
  "name": "example_adapter",
  "version": "0.1.0",
  "type": "external_api",
  "requires_network": true,
  "timeout": 30,
  "retry_count": 2
}
```
