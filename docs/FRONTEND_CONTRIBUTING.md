# ConfigSentinel â€” Frontend Contributing Guide

> **Audience:** Rohan, Matin, and all frontend contributors.
> This document governs how to contribute to the ConfigSentinel frontend.

---

## 1. Architecture Rules

### 1.1 Separation of concerns

| Location | What goes here |
|---|---|
| `src/api/` | API communication ONLY. No UI, no React, no routing. |
| `src/types/` | TypeScript type definitions. Must match the actual backend contract. |
| `src/hooks/` | React Query hooks and custom frontend hooks. Server state management. |
| `src/components/` | Reusable, composable UI components. No direct API calls. |
| `src/layouts/` | Page shells (nav, footer, sidebars). No business logic. |
| `src/pages/` | Route-level components. Compose hooks + components into a page. |
| `src/routes/` | Route configuration only. One file. |
| `src/lib/` | Generic utilities that don't belong to any other category. |

### 1.2 API call discipline

- **UI components must NOT contain raw API calls.**
  If you are writing `fetch(...)` inside a component, stop. Move it to `src/api/`.

- **API calls belong in `src/api/configsentinel.ts`.**
  One function per endpoint. Typed request and response.

- **Server state (loading/data/error) belongs in hooks.**
  Use `useAudit()`, `useVersion()`, or create a new hook in `src/hooks/`.

- **Do NOT use raw `fetch()` anywhere except `src/api/client.ts`.**

### 1.3 Type safety

- **Do NOT use `any` for API response types.**
  If the backend returns a field you don't know the type of, file an issue instead of using `any`.

- **TypeScript must remain strict.**
  Do not disable strict mode flags or add `// @ts-ignore` to work around type errors.

---

## 2. Backend Contract Rules

These rules protect the integrity of the compliance product. Violating them
produces incorrect UI that misleads operators.

### Frontend developers MUST NOT:

- **Silently modify backend API contracts.**
  If you need a different API shape, open a backend issue. Do not work around it in the frontend.

- **Invent response fields.**
  If `AuditSummary` does not have a `security_rating` field, do not add one to the TypeScript type.

- **Invent security scores.**
  The backend does not return a security score. A number like "72% secure" is meaningless and misleading. Do not calculate one from pass/fail counts.

- **Fabricate line numbers.**
  `evidence.raw_lines` contains text snippets, NOT line positions. Do not scan `config_text` to derive line numbers and present them as authoritative.

- **Alter backend error semantics.**
  `not_applicable` is NOT a failure. Display it as neutral. Do not include it in failure counts or red indicators.

- **Duplicate compliance logic.**
  Do not re-implement SSH version checking, telnet detection, or any other rule in JavaScript/TypeScript. The backend is the authority.

- **Auto-apply `config_hint`.**
  `remediation.config_hint` is advisory only. It must be displayed as a read-only code example with a clear "advisory only â€” do not apply automatically" label.

---

## 3. Git Workflow

### Branch naming

```
feature/frontend-<feature>    e.g. feature/frontend-dashboard
feature/frontend-upload
feature/frontend-results
bugfix/frontend-<description>
```

### Rules

- **No direct commits to `main`.**
- Keep branches focused â€” one feature or fix per branch.
- Rebase or merge `main` into your branch before opening a PR.
- Delete the branch after merge.

---

## 4. Pull Request Requirements

Every frontend PR must include:

| Requirement | Why |
|---|---|
| Clear description of changes | Context for reviewers |
| Screenshots for any visual changes | Verify intent matches implementation |
| `npm run build` output (must pass) | Build must not be broken |
| `npx tsc --noEmit` output (must pass) | Type errors are not acceptable |
| Scope of changes | Confirms the PR is focused |
| Error/loading/empty state consideration | Every API-driven UI must handle all states |

### PR checklist

```
[ ] Branch created from latest main
[ ] Feature scope is focused (one feature or fix)
[ ] No raw fetch() in components
[ ] No invented API fields or scores
[ ] TypeScript types match backend contract
[ ] Every API-driven UI handles: loading, success, error, empty state
[ ] npm run build passes
[ ] npx tsc --noEmit passes
[ ] Screenshots attached for visual changes
[ ] PR description is clear
```

---

## 5. Loading / Error / Empty State Rules

**Every UI component that drives from API data must implement all four states:**

```
1. Loading  â€” the request is in-flight (isPending)
2. Success  â€” data arrived and is rendered (isSuccess, data is defined)
3. Error    â€” request failed (isError, error.message is safe to display)
4. Empty    â€” request succeeded but there is nothing to show
```

Do not ship a component that crashes or shows broken UI in any of these states.

Use the `ApiError` class from `src/api/client.ts` to check error codes and show
appropriate messages (e.g. `INVALID_INPUT` â†’ prompt re-entry, `INTERNAL_ERROR` â†’ generic retry message).

---

## 6. Environment Variables

The only frontend environment variable is:

```
VITE_API_BASE_URL=http://localhost:8000
```

- Do NOT hardcode backend URLs in any source file.
- Do NOT commit `.env` to the repository.
- If a new environment variable is needed, add it to `.env.example` with a clear comment.

---

## 7. Compliance Display Rules

These rules are mandatory for any UI that displays audit results:

| Rule | Implementation |
|---|---|
| `not_applicable` is not a failure | Use neutral styling (grey), not red |
| `needs_review` is uncertain | Use amber/warning styling, not red |
| `fail` is a failure | Use red |
| `pass` is compliant | Use green |
| `config_hint` is advisory | Show in a code block with "Advisory only" label |
| `raw_lines` are text snippets, not line numbers | Do not display as "Line X" |
| Severity is a control property, not a finding property | A PASS can still be high severity |
| `severity_distribution` is for informational display only | Do not derive pass/fail from it |

---

## 8. Component Guidelines

- Keep components small and focused. A component should do one thing well.
- Props should be typed. No `any` prop types.
- Extract logic into hooks, not into component bodies.
- Prefer composition over inheritance.
- Component files should export one primary component, named the same as the file.

---

## 9. Questions & Issues

If you find a discrepancy between the TypeScript types (`src/types/api.ts`) and
the actual backend response, raise an issue immediately â€” do not paper over it
with a type assertion.

For backend behaviour questions, refer to:
- `docs/FRONTEND.md` â€” frontend integration contract
- `docs/ARCHITECTURE.md` â€” backend pipeline architecture
- `src/api/schemas.py` â€” authoritative Pydantic models
