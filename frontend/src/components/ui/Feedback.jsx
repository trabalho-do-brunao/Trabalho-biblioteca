export default function Feedback({ children, type = 'info', className = '' }) {
  const role = type === 'error' ? 'alert' : 'status'

  return (
    <div
      className={`ui-feedback ui-feedback-${type} ${className}`.trim()}
      role={role}
      aria-live={type === 'error' ? 'assertive' : 'polite'}
    >
      {children}
    </div>
  )
}
