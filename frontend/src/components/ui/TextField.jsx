import { useId } from 'react'

import { aplicarMascara } from '../../utils/masks'
import Tooltip from './Tooltip'

export default function TextField({
  label,
  id,
  className = '',
  tooltip,
  hint,
  error,
  mask,
  onChange,
  ...props
}) {
  const generatedId = useId()
  const inputId = id || generatedId
  const hintId = hint ? `${inputId}-hint` : undefined
  const errorId = error ? `${inputId}-error` : undefined
  const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined

  const handleChange = (event) => {
    if (mask) {
      event.target.value = aplicarMascara(mask, event.target.value)
    }
    onChange?.(event)
  }

  return (
    <div className={`ui-field ${className}`.trim()}>
      <div className="ui-field-label-row">
        <label className="ui-field-label" htmlFor={inputId}>{label}</label>
        {tooltip ? <Tooltip content={tooltip} label={`Ajuda sobre ${label}`} /> : null}
      </div>

      <input
        id={inputId}
        className={`ui-input${error ? ' ui-input-error' : ''}`}
        aria-invalid={Boolean(error)}
        aria-describedby={describedBy}
        onChange={handleChange}
        {...props}
      />

      {hint ? <small id={hintId} className="ui-field-hint">{hint}</small> : null}
      {error ? <small id={errorId} className="ui-field-error" role="alert">{error}</small> : null}
    </div>
  )
}
