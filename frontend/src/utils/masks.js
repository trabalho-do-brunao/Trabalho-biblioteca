export function somenteDigitos(valor = '') {
  return String(valor).replace(/\D/g, '')
}

export function mascaraCpf(valor = '') {
  const digitos = somenteDigitos(valor).slice(0, 11)

  return digitos
    .replace(/^(\d{3})(\d)/, '$1.$2')
    .replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1-$2')
}

export function mascaraTelefoneBr(valor = '') {
  const digitos = somenteDigitos(valor).replace(/^55(?=\d{10,11}$)/, '').slice(0, 11)

  if (digitos.length <= 10) {
    return digitos
      .replace(/^(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{4})(\d)/, '$1-$2')
  }

  return digitos
    .replace(/^(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d)/, '$1-$2')
}

export function mascaraTelefoneFlexivel(valor = '') {
  const texto = String(valor).trimStart()
  if (texto.startsWith('+')) {
    return `+${somenteDigitos(texto).slice(0, 15)}`
  }
  if (texto.startsWith('00')) {
    return `00${somenteDigitos(texto).slice(2, 17)}`
  }
  return mascaraTelefoneBr(texto)
}

export function formatarTelefoneArmazenado(valor = '') {
  const digitos = somenteDigitos(valor)
  if (digitos.startsWith('55') && [12, 13].includes(digitos.length)) {
    const nacional = digitos.slice(2)
    return `+55 ${mascaraTelefoneBr(nacional)}`
  }
  return digitos ? `+${digitos}` : '—'
}

export function mascaraDataBr(valor = '') {
  return somenteDigitos(valor)
    .slice(0, 8)
    .replace(/^(\d{2})(\d)/, '$1/$2')
    .replace(/^(\d{2})\/(\d{2})(\d)/, '$1/$2/$3')
}

export const mascaras = {
  cpf: mascaraCpf,
  telefoneBr: mascaraTelefoneBr,
  telefoneFlexivel: mascaraTelefoneFlexivel,
  dataBr: mascaraDataBr,
}

export function aplicarMascara(tipo, valor) {
  if (!tipo) return valor
  if (typeof tipo === 'function') return tipo(valor)
  return mascaras[tipo] ? mascaras[tipo](valor) : valor
}
