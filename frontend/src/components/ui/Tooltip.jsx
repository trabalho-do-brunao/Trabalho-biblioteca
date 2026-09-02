import { CircleHelp } from 'lucide-react'
import { cloneElement, isValidElement, useId } from 'react'

export default function Tooltip({
  content,
  label = 'Mais informações',
  children,
  className = '',
  position = 'top',
}) {
  const tooltipId = useId()

  const trigger = isValidElement(children)
    ? cloneElement(children, {
        'aria-describedby': [children.props['aria-describedby'], tooltipId].filter(Boolean).join(' '),
      })
    : (
      <button
        type="button"
        className="ui-tooltip-trigger"
        aria-label={label}
        aria-describedby={tooltipId}
      >
        <CircleHelp aria-hidden="true" />
      </button>
    )

  return (
    <span className={`ui-tooltip ui-tooltip-${position} ${className}`.trim()}>
      {trigger}
      <span id={tooltipId} className="ui-tooltip-content" role="tooltip">
        {content}
      </span>
    </span>
  )
}
