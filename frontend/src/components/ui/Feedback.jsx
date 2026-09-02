export default function Feedback({ children, type = 'info', className = '' }) {
  return (
    <div className={`ui-feedback ui-feedback-${type} ${className}`.trim()} role="status">
      {children}
    </div>
  )
}
