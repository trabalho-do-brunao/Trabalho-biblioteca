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

export function mascaraDataBr(valor = '') {
  return somenteDigitos(valor)
    .slice(0, 8)
    .replace(/^(\d{2})(\d)/, '$1/$2')
    .replace(/^(\d{2})\/(\d{2})(\d)/, '$1/$2/$3')
}

export const mascaras = {
  cpf: mascaraCpf,
  telefoneBr: mascaraTelefoneBr,
  dataBr: mascaraDataBr,
}

export function aplicarMascara(tipo, valor) {
  if (!tipo) return valor
  if (typeof tipo === 'function') return tipo(valor)
  return mascaras[tipo] ? mascaras[tipo](valor) : valor
}
