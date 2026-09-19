# Natural Language Query Security & Boundaries

## Query Pipeline
```
Natural Language Input
        ↓
Sanitization & SQL Primitive Filter
        ↓
Strict StructuredQuerySchema (Pydantic v2 extra="forbid")
        ↓
Validation & Allowed Field Constraints
        ↓
Parameterized SQLite Query Builder
        ↓
Database Query Results
```

## Security Controls
1. **No Raw SQL Generation:** Natural language inputs are parsed strictly into predefined schema fields (`intent_id`, `severity`, `status`, `vendor`, `environment`).
2. **Injection Rejection:** Raw SQL keywords (`DROP`, `UNION`, `UPDATE`, `--`, `;`) are stripped/rejected.
3. **Deterministic Execution:** Database interactions use parameterized queries only.
