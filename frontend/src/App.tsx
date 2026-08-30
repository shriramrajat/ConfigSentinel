/**
 * src/App.tsx
 *
 * Application root component.
 *
 * Responsibilities:
 *  - Render the route tree (AppRoutes).
 *
 * This component intentionally does very little. BrowserRouter and
 * QueryClientProvider are set up in main.tsx to keep this clean.
 *
 * Do not add global state, context providers, or business logic here
 * unless they are genuinely app-wide concerns.
 */

import { AppRoutes } from './routes'

function App() {
  return <AppRoutes />
}

export default App
