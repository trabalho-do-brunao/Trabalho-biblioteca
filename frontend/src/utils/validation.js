import { somenteDigitos } from './masks.js'

export function obrigatorio(valor) {
  return String(valor ?? '').trim().length > 0
}

export function emailValido(valor) {
  const email = String(valor ?? '').trim()
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export function cpfValido(valor) {
  const cpf = somenteDigitos(valor)

  if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) {
    return false
  }

  const calcularDigito = (base, pesoInicial) => {
    let soma = 0
    for (let indice = 0; indice < base.length; indice += 1) {
      soma += Number(base[indice]) * (pesoInicial - indice)
    }
    const resto = (soma * 10) % 11
    return resto === 10 ? 0 : resto
  }

  const primeiro = calcularDigito(cpf.slice(0, 9), 10)
  const segundo = calcularDigito(cpf.slice(0, 10), 11)
  return primeiro === Number(cpf[9]) && segundo === Number(cpf[10])
}

export function dataBrValida(valor) {
  const partes = String(valor ?? '').split('/')
  if (partes.length !== 3) return false

  const [diaTexto, mesTexto, anoTexto] = partes
  if (diaTexto.length !== 2 || mesTexto.length !== 2 || anoTexto.length !== 4) return false

  const dia = Number(diaTexto)
  const mes = Number(mesTexto)
  const ano = Number(anoTexto)
  const data = new Date(ano, mes - 1, dia)

  return (
    data.getFullYear() === ano
    && data.getMonth() === mes - 1
    && data.getDate() === dia
  )
}

export function validarCampo(valor, regras = []) {
  for (const regra of regras) {
    const valida = typeof regra === 'function' ? regra : regra.validar
    if (!valida(valor)) {
      return typeof regra === 'function' ? 'Valor inválido.' : regra.mensagem
    }
  }
  return ''
}
