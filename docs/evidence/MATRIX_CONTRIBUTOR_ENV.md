# Contributor Environment Matrix

Supported environments for contributors.

| OS | Python | Shell | Status |
|---|:-------:|:-----:|:------:|
| macOS 14+ | 3.11-3.14 | zsh | ✅ |
| macOS 13 | 3.11-3.14 | zsh | ✅ |
| Ubuntu 22.04+ | 3.11-3.14 | bash | ✅ |
| Ubuntu 20.04 | 3.11-3.13 | bash | ✅ |
| Windows (WSL2/Ubuntu) | 3.11-3.13 | bash | ⚠️ |

## Requirements
- Python 3.11+ (3.14 recommended)
- pip 21+
- git 2.25+
- make (optional, for Makefile targets)

## Notes
- Windows native is not supported — use WSL2.
- Other Linux distributions likely work but are not tested in CI.
