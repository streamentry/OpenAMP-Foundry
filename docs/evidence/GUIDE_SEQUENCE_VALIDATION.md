# Sequence Field Validation Report

Validates sequence fields in pipeline inputs.

## Checks Performed
- All characters are valid amino acids (A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y).
- Sequence length is within configured range (8-35 AA).
- Sequence is not empty.
- Sequence is uppercase.

## Example
```bash
python -c "
from openamp_foundry.data.loaders import is_valid_sequence
print(is_valid_sequence('ACDEFGHIKL'))  # True
print(is_valid_sequence('ACB'))          # False (B is invalid)
"
```

## Rules
- Invalid sequences should be rejected at the loading stage.
- Invalid sequences should be logged with the candidate ID.
- The pipeline should continue processing valid sequences after rejecting invalid ones.
