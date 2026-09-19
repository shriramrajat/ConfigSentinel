/**
 * src/routes/index.tsx
 *
 * Centralised route configuration for ConfigSentinel.
 *
 * All routes are defined here. Page components are imported and assigned
 * to paths. The RootLayout wraps all routes for consistent header/footer.
 *
 * Adding a new route:
 * 1. Create the page in src/pages/YourPage.tsx.
 * 2. Import it here.
 * 3. Add a <Route> under the root layout Route.
 * 4. That is all — do not scatter routing logic into components.
 *
 * Route structure (current):
 *   /           → Home
 *
 * Planned (add in feature branches, not this phase):
 *   /audit      → Audit scanner page
 *   /results/:id → Results detail page (if audit state becomes persistent)
 */

import { Route, Routes } from 'react-router-dom'
import { RootLayout } from '../layouts/RootLayout'
import { Home } from '../pages/Home'
import { DiscoveryQueue } from '../pages/DiscoveryQueue'
import { History } from '../pages/History'
import { DeviceDashboard } from '../pages/DeviceDashboard'
import { Findings } from '../pages/Findings'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        <Route index element={<Home />} />
        <Route path="discovery" element={<DiscoveryQueue />} />
        <Route path="history" element={<History />} />
        <Route path="devices" element={<DeviceDashboard />} />
        <Route path="findings" element={<Findings />} />
      </Route>
    </Routes>
  )
}


