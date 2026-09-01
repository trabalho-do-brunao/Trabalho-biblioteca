# Análise de risco de atraso do BiblioAvisa

## Objetivo

A análise de risco é um diferencial complementar do BiblioAvisa. Ela utiliza o histórico objetivo de empréstimos do usuário para decidir se um lembrete adicional deve ser preparado antes dos avisos obrigatórios.

Ela **não substitui** os avisos exigidos pelo sistema:

- 2 dias antes do vencimento;
- no dia do vencimento;
- após o vencimento.

Esses três avisos continuam funcionando independentemente da classificação de risco.

## Indicadores utilizados

Para cada usuário com empréstimo em aberto, o sistema consulta:

- quantidade de devoluções concluídas;
- quantidade de devoluções concluídas após a data prevista;
- quantidade de empréstimos ainda abertos cuja data prevista já passou.

Uma devolução histórica é considerada atrasada quando:

```text
data_devolucao > data_prevista_devolucao
```

O status `devolvido` sozinho não informa se houve atraso, por isso a comparação entre as datas é utilizada.

## Classificação determinística

| Classificação | Regra | Lembrete adicional |
|---|---|---|
| `sem_historico` | nenhuma devolução concluída e nenhum empréstimo atualmente atrasado | nenhum |
| `baixo` | existe histórico concluído e nenhuma devolução atrasada | nenhum |
| `medio` | exatamente uma devolução anterior em atraso | 3 dias antes |
| `alto` | duas ou mais devoluções anteriores em atraso, ou pelo menos um empréstimo atualmente atrasado | 5 dias antes |

A regra é propositalmente simples e determinística. Os mesmos dados sempre produzem a mesma classificação, permitindo explicar e demonstrar a decisão durante a apresentação acadêmica.

## Lembretes adicionais

Quando o usuário possui risco `medio`, o sistema pode criar um lembrete adicional exatamente 3 dias antes do vencimento.

Quando possui risco `alto`, o sistema pode criar um lembrete adicional exatamente 5 dias antes do vencimento.

O texto enviado ao usuário é neutro: ele informa antecipadamente o vencimento, mas não expõe a classificação de risco nem acusa o usuário pelo histórico anterior.

Os lembretes adicionais são registrados na tabela `mensagens` com `tipo = 'outro'`, `direcao = 'enviada'` e `status = 'pendente'`. A decisão detalhada também é retornada por `verificar_prazos()` e registrada pelo logger da automação, incluindo classificação, indicadores e justificativa.

## Não duplicação

Antes de criar um lembrete de risco, a automação verifica se já existe para o mesmo empréstimo, data de referência e texto. Assim uma segunda execução no mesmo dia não cria outra mensagem pendente igual.

Caso uma tentativa anterior esteja marcada como `falha`, uma nova mensagem pode ser preparada para permitir nova tentativa controlada.

## Teste demonstrável

O script:

```powershell
.\.venv\Scripts\python.exe scripts\test_risco_atraso.py
```

cria dados temporários no PostgreSQL para usuários sem histórico, de risco baixo, médio e alto. Ele valida as classificações, os lembretes extras, a permanência do aviso obrigatório de 2 dias e a não duplicação. Ao final, remove os dados criados para o teste.

O teste apenas prepara registros de mensagens no banco. Ele não chama o serviço do WhatsApp e não envia mensagens reais.
