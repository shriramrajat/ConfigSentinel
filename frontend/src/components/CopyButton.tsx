/**
 * src/components/CopyButton.tsx
 *
 * A reusable, accessible copy-to-clipboard button.
 * Relies exclusively on the standard navigator.clipboard API.
 * Provides brief visual feedback when clicked.
 */

import { useState, useCallback } from 'react'

interface CopyButtonProps {
  textToCopy: string
  label?: string
}

export function CopyButton({ textToCopy, label = 'Copy' }: CopyButtonProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    if (!textToCopy) return

    try {
      await navigator.clipboard.writeText(textToCopy)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }, [textToCopy])

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="cs-btn-ghost"
      style={{
        padding: '0.25rem 0.5rem',
        fontSize: '0.6875rem',
        gap: '0.375rem',
        borderColor: copied ? 'var(--cs-pass-border)' : 'var(--cs-border)',
        color: copied ? 'var(--cs-pass)' : 'var(--cs-text-secondary)',
        backgroundColor: copied ? 'var(--cs-pass-bg)' : 'transparent',
      }}
      aria-label={copied ? 'Copied to clipboard' : `Copy ${label.toLowerCase()} to clipboard`}
    >
      {copied ? (
        <>
          <svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path
              d="M10 3L4.5 8.5L2 6"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Copied
        </>
      ) : (
        <>
          <svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12" fill="none">
            <rect x="2.5" y="4" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.2" />
            <path d="M4 2.5C4 1.94772 4.44772 1.5 5 1.5H8.5C9.05228 1.5 9.5 1.94772 9.5 2.5V6" stroke="currentColor" strokeWidth="1.2" />
          </svg>
          {label}
        </>
      )}
    </button>
  )
}
