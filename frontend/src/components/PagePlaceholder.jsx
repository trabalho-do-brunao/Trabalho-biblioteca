export default function PagePlaceholder({ title, description }) {
  return (
    <section className="page">
      <header className="page-header">
        <div>
          <p className="page-eyebrow">BiblioAvisa</p>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </header>

      <div className="page-card placeholder-card">
        <strong>Estrutura da página pronta.</strong>
        <span>O conteúdo funcional desta tela será implementado na backlog correspondente.</span>
      </div>
    </section>
  )
}
