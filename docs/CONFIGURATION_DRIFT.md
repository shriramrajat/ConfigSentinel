# ConfigSentinel — Configuration Fingerprinting & Drift Engine

## Overview

ConfigSentinel tracks configuration drift and security posture changes across consecutive device audits.

---

## 1. Deterministic Configuration Fingerprinting

Configuration fingerprints are calculated using SHA-256 hashes over normalized, canonical key/value tuples:
- Ignores whitespace and comment changes.
- Vendor-aware normalization.
- Sensitive to security-relevant directive changes.

---

## 2. Configuration Drift Classification

Compares consecutive `NormalizedConfig` objects to detect:
- `ADDED` directives
- `REMOVED` directives
- `MODIFIED` directive values

---

## 3. Posture Delta & Security Impact Analysis

Directly compares deterministic `ComplianceResult` lists between consecutive audits:
- `SECURITY_DEGRADATION`: Number of new failing controls > resolved controls.
- `SECURITY_IMPROVEMENT`: Number of resolved controls > new failing controls.
- `NEUTRAL`: Equal number of new failures and resolutions.

 Zero reliance on LLMs for compliance or risk score calculation.

---

## 4. API Endpoints

- `GET /api/v1/devices/{device_id}/drift` — Configuration drift comparison between the last two audits.
- `GET /api/v1/devices/{device_id}/posture` — Posture delta, security impact, new failures, and resolved failures.
