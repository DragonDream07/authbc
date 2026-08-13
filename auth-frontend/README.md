# auth-frontend

React + TypeScript frontend for the Auth Starter project. Provides a complete authentication UI including login, registration, forgot-password, reset-password, and a protected profile page.

---

## Tech Stack

- **React 18** with function components
- **TypeScript 5** (strict mode)
- **Vite 5** (dev server + bundler)
- **React Router v6** for client-side routing
- **Vitest** for unit tests
- **ESLint** (React + hooks + TypeScript)

---

## Project Structure

```
auth-frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
├── .env.example
└── src/
    ├── main.tsx                      # App entry point
    ├── api/
    │   └── auth.ts                   # API client (login, register, forgotPassword, resetPassword, me, logout, refresh)
    ├── context/
    │   └── AuthContext.tsx            # AuthContext + AuthProvider
    ├── hooks/
    │   └── useAuthForm.ts             # Controlled-input + client-side validation hook
    ├── components/
    │   ├── RequireAuth.tsx            # Route guard for protected pages
    │   └── RequireGuest.tsx           # Route guard for guest-only pages
    ├── features/
    │   └── auth/
    │       └── pages/
    │           ├── LoginPage.tsx
    │           ├── RegisterPage.tsx
    │           ├── ForgotPasswordPage.tsx
    │           └── ResetPasswordPage.tsx
    ├── pages/
    │   └── ProfilePage.tsx            # Protected profile page
    └── styles/
        └── tokens.css                # CSS custom properties from design tokens
```

---

## Environment Variables

Copy `.env.example` to `.env` before running the dev server:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000` | Base URL of the Auth backend API. The Vite dev server proxies `/api/v1` to this origin automatically. |

> **Note:** All Vite environment variables must be prefixed with `VITE_` to be exposed to the browser bundle. Never put secrets in `.env` files committed to source control.

---

## Setup

### Prerequisites

- Node.js ≥ 18
- npm ≥ 9 (or pnpm / yarn)
- The `auth-backend` service running (see the root `README.md` and `docker-compose.yml`)

### Install dependencies

```bash
cd auth-frontend
npm install
```

### Configure environment

```bash
cp .env.example .env
# Edit .env if your backend runs on a different host or port
```

### Start development server

```bash
npm run dev
```

The app is available at `http://localhost:5173` by default. API calls to `/api/v1/*` are proxied to `VITE_API_BASE_URL` (configured in `vite.config.ts`), so no CORS issues occur during development.

### Build for production

```bash
npm run build
# Output is in dist/
```

Serve `dist/` with any static file host (Nginx, Caddy, S3 + CloudFront, etc.). Ensure your web server redirects all paths to `index.html` to support client-side routing.

---

## Running Tests

```bash
npm test
```

Tests use **Vitest**. The test suite covers:

- Client-side validation rules (exact messages matching `validation-rules.json`)
- Route guard behaviour (`RequireAuth`, `RequireGuest`)

---

## Linting

```bash
npm run lint
```

ESLint is configured for React, React Hooks, and TypeScript. Zero warnings are permitted (`--max-warnings 0`).

---

## API Endpoints Consumed

All requests are sent to `VITE_API_BASE_URL`. The following endpoints are used (defined in `src/api/auth.ts`):

| Handler | Method | Path |
|---|---|---|
| `login` | POST | `/auth/login` |
| `register` | POST | `/auth/register` |
| `forgotPassword` | POST | `/auth/forgot-password` |
| `resetPassword` | POST | `/auth/reset-password` |
| `me` | GET | `/auth/me` |
| `logout` | POST | `/auth/logout` |
| `refresh` | POST | `/auth/refresh` |

---

## Authentication Flow

1. **Register** — `RegisterPage` collects `full_name`, `email`, `password`, `confirm_password`, and Terms acceptance. On success, redirects to `/login`.
2. **Login** — `LoginPage` issues a `login` request; on success the `AuthContext` stores the access token and user, then redirects to `/profile`.
3. **Protected routes** — `RequireAuth` redirects unauthenticated users to `/login`.
4. **Guest-only routes** — `RequireGuest` redirects authenticated users to `/profile`.
5. **Token refresh** — `AuthContext.refresh` calls `POST /auth/refresh` to silently obtain a new access token.
6. **Forgot / Reset password** — Two-step flow: `ForgotPasswordPage` requests a reset email; `ResetPasswordPage` (reached via the emailed link with a `token` query parameter) submits the new password.
7. **Logout** — Calls `POST /auth/logout`, clears local auth state, and redirects to `/login`.

---

## Styling

- All colors, spacing, border-radius, and font sizes come from `src/styles/tokens.css` (CSS custom properties mirroring `design-tokens.json`). No hard-coded values in components.
- Layout uses the `centered-card` pattern; branding renders above the card.
- BEM-like class names: `.auth-card`, `.auth-card__field`, `.field--error`, etc.
- WCAG AA color contrast; errors are never communicated by color alone.

---

## Accessibility

- Every input has an associated `<label>`.
- Validation errors are linked via `aria-describedby`.
- Password visibility toggles are `<button>` elements with descriptive `aria-label`.
- Submit buttons are `disabled` and carry `aria-busy="true"` while a request is in flight.
- Success/error banners live in an `aria-live="polite"` region.

---

## Running with Docker

See the root `docker-compose.yml`. The frontend service builds this directory and serves the static output. Start everything together:

```bash
# From the repository root
docker compose up --build
```

---

## License

MIT
