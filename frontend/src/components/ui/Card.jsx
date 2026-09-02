export default function Card({ children, className = '', as: Component = 'section' }) {
  return <Component className={`ui-card ${className}`.trim()}>{children}</Component>
}
