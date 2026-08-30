/**
 * src/main.tsx
 *
 * Application entry point.
 *
 * Sets up the mandatory providers:
 *  - BrowserRouter    — React Router v7 client-side routing.
 *  - QueryClientProvider — TanStack React Query server state.
 *
 * Do not add business logic, components, or API calls here.
 * This file should remain trivially small.
 */

import { QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { queryClient } from './lib/queryClient'
import './index.css'

const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Root element #root not found in index.html.')
}

createRoot(rootElement).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>,
)
