---
description: Run the Hybrid Code Auditor on a specific Python file to check for syntax errors and architectural compliance against soul.md.
---
To execute the Hybrid Code Auditor on a specific file:

1. Run `flake8` to check for critical syntax bugs and unused variables. AI must fix these autonomously.
// turbo
2. Perform an AI conceptual peer review to ensure the code obeys the strict rules in `soul.md` (no destructive operations, proper quarantines, etc.).

```bash
cd "c:\Users\Tuchi\MiEstudioIA"
# Replace <file_path.py> with the actual file path you want to audit
python -m flake8 "<file_path.py>"
```
