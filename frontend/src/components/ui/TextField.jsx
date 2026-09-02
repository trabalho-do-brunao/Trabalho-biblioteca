export default function TextField({ label, id, className = '', ...props }) {
  return (
    <label className={`ui-field ${className}`.trim()} htmlFor={id}>
      <span className="ui-field-label">{label}</span>
      <input id={id} className="ui-input" {...props} />
    </label>
  )
}
