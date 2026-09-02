import assert from 'node:assert/strict'

import { mascaraCpf, mascaraDataBr, mascaraTelefoneBr } from '../src/utils/masks.js'
import { cpfValido, dataBrValida, emailValido, obrigatorio } from '../src/utils/validation.js'

console.log('=== Teste de qualidade da interface ===')

assert.equal(mascaraCpf('52998224725'), '529.982.247-25')
console.log('[OK] Máscara de CPF')

assert.equal(mascaraTelefoneBr('41999998888'), '(41) 99999-8888')
assert.equal(mascaraTelefoneBr('4133334444'), '(41) 3333-4444')
console.log('[OK] Máscara de telefone brasileiro')

assert.equal(mascaraDataBr('01092026'), '01/09/2026')
console.log('[OK] Máscara de data')

assert.equal(obrigatorio('  dado  '), true)
assert.equal(obrigatorio('   '), false)
assert.equal(emailValido('teste@exemplo.com'), true)
assert.equal(emailValido('teste-invalido'), false)
assert.equal(cpfValido('529.982.247-25'), true)
assert.equal(cpfValido('111.111.111-11'), false)
assert.equal(dataBrValida('01/09/2026'), true)
assert.equal(dataBrValida('31/02/2026'), false)
console.log('[OK] Validações de obrigatório, e-mail, CPF e data')

console.log('\n=== Teste de qualidade passou ===')
