# ConfigSentinel â€” Frontend

React + TypeScript + Vite frontend for the ConfigSentinel network configuration
security and compliance auditing tool.

> **Phase:** Frontend Foundation. The scanner UI and dashboard are built in subsequent phases.

---

## Prerequisites

| Tool | Version |
|---|---|
| Node.js | â‰¥ 20 |
| npm | â‰¥ 10 |
| ConfigSentinel Backend | Running on `http://localhost:8000` (or configured URL) |

---

## Installation

```bash
cd frontend
npm install
```

---

## Development

```bash
npm run dev
```

The development server starts at `http://localhost:5173` by default.

**The ConfigSentinel backend must be running separately.**
Start the backend from the repository root:

```bash
uvicorn src.api.main:app --reload
```

---

## Build

```bash
npm run build
```

Builds production assets into `frontend/dist/`.

---

## Type checking

```bash
npx tsc --noEmit
```

---

## API Environment Variable

| Variable | Purpose | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |

Copy `.env.example` to `.env` and set `VITE_API_BASE_URL` for your environment:

```bash
cp .env.example .env
```

**Never commit `.env`.** It is gitignored.

---

## Directory Structure

```
frontend/
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ client.ts          â† Low-level HTTP client (ApiError, apiFetch)
â”‚   â”‚   â””â”€â”€ configsentinel.ts  â† Typed API functions (auditConfig, healthCheck, getVersion)
â”‚   â”œâ”€â”€ components/            â† Reusable UI components (buttons, cards, badges, etc.)
â”‚   â”œâ”€â”€ hooks/
â”‚   â”‚   â”œâ”€â”€ useAudit.ts        â† React Query mutation for POST /api/v1/audit
â”‚   â”‚   â””â”€â”€ useVersion.ts      â† React Query query for GET /version
â”‚   â”œâ”€â”€ layouts/
â”‚   â”‚   â””â”€â”€ RootLayout.tsx     â† App shell (nav, main, footer)
â”‚   â”œâ”€â”€ lib/
â”‚   â”‚   â””â”€â”€ queryClient.ts     â† Shared QueryClient instance
â”‚   â”œâ”€â”€ pages/
â”‚   â”‚   â””â”€â”€ Home.tsx           â† Landing page (extend / replace with dashboard)
â”‚   â”œâ”€â”€ routes/
â”‚   â”‚   â””â”€â”€ index.tsx          â† All route definitions in one place
â”‚   â””â”€â”€ types/
â”‚       â””â”€â”€ api.ts             â† TypeScript types mirroring the backend contract
â”œâ”€â”€ .env.example               â† Environment variable template
â”œâ”€â”€ index.html                 â† HTML entry point
â”œâ”€â”€ package.json
â”œâ”€â”€ tsconfig.app.json
â”œâ”€â”€ vite.config.ts             â† Vite + React + Tailwind v4 config
â””â”€â”€ README.md
```

---

## Architecture Rules

These rules must be followed by all contributors. See also `docs/FRONTEND_CONTRIBUTING.md`.

1. **No raw `fetch()` in components.** All API calls go through `src/api/configsentinel.ts`.
2. **No business logic in components.** Components render; hooks and API functions handle data.
3. **TypeScript types must match the backend.** Do not invent fields not returned by the API.
4. **No hardcoded production URLs.** Always use `VITE_API_BASE_URL`.
5. **No security scores.** The backend does not produce a score; the frontend must not fabricate one.
6. **Every API-driven UI must handle:** loading, success, error, and empty state.

---

## Adding a New Feature

1. Create a branch: `feature/frontend-<feature-name>`
2. Add any new backend types to `src/types/api.ts` (only if the backend actually returns them).
3. Add API functions to `src/api/configsentinel.ts` if calling new endpoints.
4. Add React Query hooks in `src/hooks/`.
5. Add reusable UI in `src/components/`.
6. Add the page in `src/pages/`.
7. Register the route in `src/routes/index.tsx`.
8. Open a PR with description + screenshots + `npm run build` result.

---

## Stack

| Technology | Purpose |
|---|---|
| React 19 | UI rendering |
| TypeScript 6 | Type safety |
| Vite 8 | Build tool |
| React Router v7 | Client-side routing |
| TanStack React Query v5 | Server state management |
| Tailwind CSS v4 | Utility-first styling |
