// Filtra apenas ruídos conhecidos do libsignal usados internamente pelo Baileys.
// Não interfere nos logs do BiblioAvisa nem altera o funcionamento da conexão.

const metodos = ['log', 'warn', 'error']

const prefixosIgnorados = [
  'Closing session:',
  'Closing stale open session for new outgoing prekey bundle',
  'Session error:Error: Bad MAC Error',
]

for (const metodo of metodos) {
  const original = console[metodo].bind(console)

  console[metodo] = (...args) => {
    const primeiraParte = String(args[0] ?? '')

    if (prefixosIgnorados.some((prefixo) => primeiraParte.startsWith(prefixo))) {
      return
    }

    original(...args)
  }
}
