/**
 * src/components/AuditForm.tsx
 *
 * Audit input form — the primary action interface.
 *
 * Responsibilities:
 *   - Accept raw network device configuration text via a monospace textarea
 *   - Accept an optional source name (device label / filename)
 *   - Validate client-side (empty / too short) before calling onSubmit
 *   - Expose onSubmit callback to the parent — no direct API calls here
 *   - Disable inputs and button while isPending
 *   - Provide a Reset/Clear action when onReset is supplied
 *
 * Rules (from docs/FRONTEND_CONTRIBUTING.md):
 *   - No raw fetch() in this component
 *   - No compliance logic
 *   - No invented vendor detection
 *   - No security scores
 *   - Textarea submits config_text exactly as entered — no pre-processing
 */

import { useState, useId, type FormEvent } from 'react'
import type { AuditRequest } from '../types/api'

// ---------------------------------------------------------------------------
// Public interface
// ---------------------------------------------------------------------------

export interface AuditFormProps {
  /**
   * Called when the form is submitted with valid input.
   * The parent (Home) calls useAudit().mutate() with this data.
   */
  onSubmit: (request: AuditRequest) => void
  /** True while the API request is in-flight. Disables all inputs. */
  isPending: boolean
  /**
   * If provided, renders a secondary "Clear" / "New Audit" action.
   * Called when the user wants to discard current results and start over.
   */
  onReset?: () => void
  /** When true, the "New Audit" reset button is shown */
  hasResults?: boolean
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateConfigText(text: string): string | null {
  if (text.trim().length === 0) {
    return 'Configuration text is required.'
  }
  if (text.trim().length < 10) {
    return 'Configuration text is too short to be valid.'
  }
  return null
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AuditForm({ onSubmit, isPending, onReset, hasResults }: AuditFormProps) {
  const [configText, setConfigText] = useState('')
  const [sourceName, setSourceName] = useState('')
  const [validationError, setValidationError] = useState<string | null>(null)

  const configId = useId()
  const sourceId = useId()

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()

    const error = validateConfigText(configText)
    if (error) {
      setValidationError(error)
      return
    }

    setValidationError(null)
    onSubmit({
      config_text: configText,
      source_name: sourceName.trim() || undefined,
    })
  }

  function handleConfigChange(value: string) {
    setConfigText(value)
    // Clear client-side validation error as soon as user types
    if (validationError) setValidationError(null)
  }

  function handleReset() {
    setConfigText('')
    setSourceName('')
    setValidationError(null)
    onReset?.()
  }

  const isSubmitDisabled = isPending || configText.trim().length === 0

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

        {/* Config textarea ------------------------------------------------- */}
        <div>
          <label
            htmlFor={configId}
            style={{
              display: 'block',
              fontFamily: 'var(--cs-font-sans)',
              fontWeight: 500,
              fontSize: '0.8125rem',
              color: 'var(--cs-text-secondary)',
              marginBottom: '0.375rem',
              letterSpacing: '0.01em',
            }}
          >
            Device configuration
            <span
              aria-hidden="true"
              style={{
                marginLeft: '0.375rem',
                fontSize: '0.6875rem',
                fontWeight: 400,
                color: 'var(--cs-text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              required
            </span>
          </label>

          <textarea
            id={configId}
            className="cs-config-textarea"
            value={configText}
            onChange={e => handleConfigChange(e.target.value)}
            disabled={isPending}
            rows={12}
            spellCheck={false}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            aria-describedby={validationError ? `${configId}-error` : `${configId}-hint`}
            aria-invalid={validationError ? true : undefined}
            placeholder={
              'Paste Cisco IOS / IOS-XE or Juniper JunOS configuration here.\n\n' +
              'Example (Cisco):\n  version 17.9\n  hostname LAB-ROUTER\n  ip ssh version 2\n  ...\n\n' +
              'Example (Juniper):\n  system {\n      host-name CORE-SW;\n      services { ssh { protocol-version v2; } }\n  }'
            }
          />

          {/* Validation error */}
          {validationError && (
            <p
              id={`${configId}-error`}
              role="alert"
              style={{
                marginTop: '0.375rem',
                fontFamily: 'var(--cs-font-sans)',
                fontSize: '0.8125rem',
                color: 'var(--cs-fail)',
              }}
            >
              {validationError}
            </p>
          )}

          {/* Hint text */}
          {!validationError && (
            <p
              id={`${configId}-hint`}
              style={{
                marginTop: '0.375rem',
                fontFamily: 'var(--cs-font-sans)',
                fontSize: '0.75rem',
                color: 'var(--cs-text-muted)',
              }}
            >
              Paste raw device configuration text. Vendor is detected automatically —
              no pre-processing required.
            </p>
          )}
        </div>

        {/* Source name ---------------------------------------------------- */}
        <div>
          <label
            htmlFor={sourceId}
            style={{
              display: 'block',
              fontFamily: 'var(--cs-font-sans)',
              fontWeight: 500,
              fontSize: '0.8125rem',
              color: 'var(--cs-text-secondary)',
              marginBottom: '0.375rem',
              letterSpacing: '0.01em',
            }}
          >
            Label
            <span
              aria-hidden="true"
              style={{
                marginLeft: '0.375rem',
                fontSize: '0.6875rem',
                fontWeight: 400,
                color: 'var(--cs-text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
              }}
            >
              optional
            </span>
          </label>

          <input
            id={sourceId}
            type="text"
            className="cs-text-input"
            value={sourceName}
            onChange={e => setSourceName(e.target.value)}
            disabled={isPending}
            maxLength={120}
            placeholder="e.g. router-01.conf, CORE-SW, lab-device"
            autoComplete="off"
          />

          <p
            style={{
              marginTop: '0.375rem',
              fontFamily: 'var(--cs-font-sans)',
              fontSize: '0.75rem',
              color: 'var(--cs-text-muted)',
            }}
          >
            Optional identifier for this configuration. Used for display only.
          </p>
        </div>

        {/* Actions -------------------------------------------------------- */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            flexWrap: 'wrap',
          }}
        >
          <button
            type="submit"
            className="cs-btn-primary"
            disabled={isSubmitDisabled}
            aria-label={isPending ? 'Audit in progress' : 'Run compliance audit'}
          >
            {isPending ? (
              <>
                <span className="cs-spinner" aria-hidden="true" />
                Auditing…
              </>
            ) : (
              <>
                {/* Play / audit icon */}
                <svg
                  aria-hidden="true"
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M7 1C3.686 1 1 3.686 1 7C1 10.314 3.686 13 7 13C10.314 13 13 10.314 13 7C13 3.686 10.314 1 7 1Z"
                    stroke="currentColor"
                    strokeWidth="1.2"
                  />
                  <path
                    d="M5.5 5L9.5 7L5.5 9V5Z"
                    fill="currentColor"
                  />
                </svg>
                Run Audit
              </>
            )}
          </button>

          {/* Reset / clear — only shown when there are results to discard */}
          {hasResults && !isPending && (
            <button
              type="button"
              className="cs-btn-ghost"
              onClick={handleReset}
              aria-label="Clear results and start new audit"
            >
              New Audit
            </button>
          )}

          {/* Clear form without resetting results state */}
          {!hasResults && !isPending && (configText || sourceName) && (
            <button
              type="button"
              className="cs-btn-ghost"
              onClick={handleReset}
              aria-label="Clear configuration input"
            >
              Clear
            </button>
          )}
        </div>

      </div>
    </form>
  )
}
