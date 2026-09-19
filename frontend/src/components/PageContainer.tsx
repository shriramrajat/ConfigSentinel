import React from 'react'

interface PageContainerProps {
  title?: string
  description?: string
  action?: React.ReactNode
  children: React.ReactNode
  className?: string
}

export function PageContainer({
  title,
  description,
  action,
  children,
  className = '',
}: PageContainerProps) {
  return (
    <div className={`cs-page-container ${className}`.trim()}>
      {(title || description || action) && (
        <header className="cs-page-header">
          <div className="cs-page-header-content">
            {title && <h1 className="cs-page-title">{title}</h1>}
            {description && <p className="cs-page-description">{description}</p>}
          </div>
          {action && <div className="cs-page-header-action">{action}</div>}
        </header>
      )}
      {children}
    </div>
  )
}
