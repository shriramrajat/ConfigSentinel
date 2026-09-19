# Security Operations Architecture

## Overview
ConfigSentinel Phase 3 provides continuous fleet configuration management, risk prioritization, remediation verification, and baseline governance.

### Core Workflows
1. **Fleet Device Management:** Register and tag devices across production, DMZ, core, staging, and lab environments.
2. **Prioritization Risk Queue:** Ranks findings into priority tiers (P1 Critical -> P4 Low) based on deterministic risk, recurrence, and attack chain amplifications.
3. **Remediation Verification:** Tests updated configuration text against compliance rules post-fix to confirm resolution (`FIX VERIFIED`).
4. **Configuration Baselines:** Maintains immutable baseline states for devices with structural drift detection.
5. **Bounded Natural-Language Querying:** Translates natural language questions into strict schema parameters evaluated by deterministic queries.
