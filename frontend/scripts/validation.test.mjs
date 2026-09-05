import test from 'node:test'
import assert from 'node:assert/strict'

import { mascaraCpf, mascaraDataBr, mascaraTelefoneBr } from '../src/utils/masks.js'
import { cpfValido, dataBrValida, emailValido, obrigatorio } from '../src/utils/validation.js'

test('máscaras formatam CPF, telefone e data', () => {
  assert.equal(mascaraCpf('52998224725'), '529.982.247-25')
  assert.equal(mascaraTelefoneBr('41999998888'), '(41) 99999-8888')
  assert.equal(mascaraTelefoneBr('4133334444'), '(41) 3333-4444')
  assert.equal(mascaraDataBr('01092026'), '01/09/2026')
})

test('campo obrigatório rejeita valor vazio', () => {
  assert.equal(obrigatorio('Biblioteca'), true)
  assert.equal(obrigatorio('   '), false)
})

test('validação de e-mail aceita e rejeita formatos esperados', () => {
  assert.equal(emailValido('usuario@exemplo.com'), true)
  assert.equal(emailValido('usuario-invalido'), false)
})

test('validação de CPF verifica dígitos verificadores', () => {
  assert.equal(cpfValido('529.982.247-25'), true)
  assert.equal(cpfValido('111.111.111-11'), false)
  assert.equal(cpfValido('529.982.247-24'), false)
})

test('validação de data rejeita datas inexistentes', () => {
  assert.equal(dataBrValida('01/09/2026'), true)
  assert.equal(dataBrValida('31/02/2026'), false)
})
