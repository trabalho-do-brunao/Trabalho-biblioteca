# Fluxo principal e agendamento do BiblioAvisa

A Backlog 13 reúne as rotinas já implementadas em um único fluxo diário.

## Ordem da rotina

1. verifica prazos dos empréstimos e executa a análise de risco;
2. cria os avisos necessários no PostgreSQL;
3. processa a fila de mensagens pendentes pelo provedor de WhatsApp;
4. gera o relatório PDF do período configurado;
5. envia o PDF por e-mail, quando o envio automático estiver habilitado;
6. registra início, fim, resultados e falhas no log.

Cada etapa possui tratamento de erro próprio. Uma falha no WhatsApp, por exemplo, não impede a tentativa de geração do relatório.

## Configuração

As opções ficam somente no `.env` local:

```env
AUTOMACAO_ENABLED=false
AUTOMACAO_HORA=08:00
AUTOMACAO_TIMEZONE=America/Sao_Paulo
AUTOMACAO_ENVIAR_EMAIL=true
AUTOMACAO_RELATORIO_DIAS=0
```

`AUTOMACAO_ENABLED` fica `false` por padrão. Isso evita que uma instalação nova comece a enviar mensagens antes que banco, WhatsApp e destinatário de e-mail sejam conferidos.

`AUTOMACAO_RELATORIO_DIAS=0` gera o relatório apenas do dia. O valor `30`, por exemplo, usa o intervalo da data atual até 30 dias antes.

## Execução manual

O fluxo pode ser executado uma vez com:

```powershell
.\.venv\Scripts\python.exe -m app.main --executar-agora
```

Para validar a orquestração sem usar o Baileys e sem enviar e-mail:

```powershell
.\.venv\Scripts\python.exe -m app.main --executar-agora --simular-whatsapp --sem-email
```

A opção acima ainda processa a fila pendente do banco. Para testes automatizados controlados, prefira `scripts/test_fluxo_principal.py`, que restringe a execução aos dados temporários criados pelo próprio teste.

## Execução diária

Quando a automação estiver validada, altere somente no `.env` local:

```env
AUTOMACAO_ENABLED=true
```

A partir disso, `run.bat` passa a manter três partes em execução:

- webhook Python;
- serviço Baileys;
- APScheduler da rotina diária.

O agendador não executa a rotina imediatamente ao iniciar. Ele aguarda o horário definido em `AUTOMACAO_HORA`.

`Ctrl + C` no terminal do `run.bat` encerra os processos supervisionados.

## Teste da Backlog 13

```powershell
.\.venv\Scripts\python.exe scripts\test_fluxo_principal.py
```

O teste:

- cria empréstimos temporários no PostgreSQL;
- valida o job do APScheduler;
- cria o aviso obrigatório de dois dias;
- processa o aviso com provedor de WhatsApp simulado;
- gera um PDF real;
- mantém o e-mail desligado;
- simula uma falha de WhatsApp e confirma que o PDF ainda é gerado;
- remove os dados e PDFs temporários ao final.

Nenhuma mensagem externa ou e-mail real é enviado por esse teste.
