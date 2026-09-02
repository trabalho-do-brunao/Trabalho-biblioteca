import { CircleHelp } from 'lucide-react'
import { useId } from 'react'

export default function Tooltip({ content, label = 'Mais informações', children, className = '' }) {
  const tooltipId = useId()

  return (
    <span className={`ui-tooltip ${className}`.trim()}>
      {children || (
        <button
          type="button"
          className="ui-tooltip-trigger"
          aria-label={label}
          aria-describedby={tooltipId}
        >
          <CircleHelp aria-hidden="true" />
        </button>
      )}
      <span id={tooltipId} className="ui-tooltip-content" role="tooltip">
        {content}
      </span>
    </span>
  )
}
