# AI Governance & Security Boundaries

## Strict AI Boundary Principles

1. **Zero Compliance Authority:**
   - LLMs and AI providers NEVER determine `PASS` or `FAIL`.
   - AI NEVER sets or alters control severity (CRITICAL, HIGH, MEDIUM, LOW, INFO).
   - AI NEVER sets or alters risk scores.

2. **Pre-LLM Secret Redaction:**
   - All passwords, secrets, community strings, and private keys are redacted (`[REDACTED_SECRET]`) before passing configuration snippets to any external LLM service.

3. **Strict Schema Validation:**
   - All LLM outputs must strictly adhere to Pydantic v2 schemas configured with `extra="forbid"`.
   - Any response containing unapproved or extra fields is rejected immediately.

4. **Human Approval for Mappings:**
   - AI-proposed semantic mappings must be explicitly reviewed and approved by a human administrator before being persisted into production.

5. **Deterministic Fallback:**
   - If AI service is offline or fails validation, the system falls back seamlessly to pre-canned deterministic explanations without breaking core auditing functions.
