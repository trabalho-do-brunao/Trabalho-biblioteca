# BiblioAvisa — Sistema de Gestão de Biblioteca com Integração via WhatsApp

Este repositório integra dois trabalhos acadêmicos relacionados à automação e à gestão de bibliotecas. As propostas se complementam e serão desenvolvidas dentro do mesmo sistema.

---

## Trabalho 1 — Automação de Processos

### Integrantes do grupo

- Guilherme Granemann Benvenutti
- Matheus Guerelus Rizelo
- Matheus Henrique Predes Pereira
- João Pedro Lagos Muraro

### Resumo da automação proposta

Atualmente, o controle de empréstimos em muitas bibliotecas é feito de forma manual, o que dificulta o acompanhamento dos prazos de devolução e gera atrasos frequentes por parte dos usuários.

Este projeto propõe a automação desse processo por meio de um sistema que:

- Conecta-se a um banco de dados PostgreSQL contendo o cadastro de livros, usuários e empréstimos;
- Verifica diariamente, de forma automática, os empréstimos ativos e seus respectivos prazos de devolução;
- Identifica empréstimos próximos do vencimento ou em atraso;
- Envia lembretes e alertas automáticos via WhatsApp aos usuários;
- Permite que o usuário interaja pelo WhatsApp para renovar empréstimos e consultar sua situação;
- Gera relatórios em PDF com o resumo das notificações enviadas e envia por e-mail ao responsável pela biblioteca.

O objetivo é reduzir os atrasos na devolução, melhorar a comunicação com os usuários e diminuir o trabalho manual da equipe da biblioteca.

### Diferencial de automação

**Diferencial de automação:** o sistema não apenas realiza notificações programadas. Ele analisa automaticamente os dados dos empréstimos e o histórico de devoluções dos usuários para
identificar situações de risco de atraso. A partir dessa análise, determina o momento adequado para enviar lembretes personalizados através da API do WhatsApp.
Além disso, o usuário pode interagir com o sistema pelo próprio WhatsApp para consultar ou renovar seus empréstimos.

---

## Trabalho 2 — Tema 14: BiblioAvisa — Biblioteca

### Alunos

- Guilherme G. Benvenutti
- Matheus Henrique P. Pereira

### Cenário

Multas por atraso poderiam ser evitadas com um simples aviso.

### Requisitos do sistema

O sistema deve:

- Realizar o cadastro do acervo;
- Realizar o cadastro e controle de empréstimos;
- Enviar um aviso 2 dias antes do prazo de devolução;
- Enviar um aviso no dia do vencimento;
- Enviar um aviso após o vencimento;
- Permitir a renovação respondendo à mensagem;
- Receber e processar a resposta através de webhook.

### Entidades mínimas do banco de dados

- `usuarios`
- `livros`
- `emprestimos`
- `renovacoes`
- `mensagens`

### API externa

**Google Books API** — utilizada para buscar automaticamente os dados de um livro a partir do ISBN.

---

## Como os dois trabalhos se conectam

Os dois trabalhos serão implementados como partes do mesmo sistema. O cadastro do acervo e dos empréstimos forma a base da aplicação, enquanto a automação utiliza esses dados para acompanhar os prazos de devolução, enviar mensagens pelo WhatsApp, receber solicitações de renovação e gerar relatórios.

Fluxo geral planejado:

```text
Cadastro de usuário e acervo
          ↓
Registro do empréstimo
          ↓
Armazenamento no PostgreSQL
          ↓
Verificação automática dos prazos
          ↓
2 dias antes → aviso pelo WhatsApp
No vencimento → aviso pelo WhatsApp
Após vencimento → alerta pelo WhatsApp
          ↓
Usuário pode responder solicitando renovação
          ↓
Webhook recebe a resposta
          ↓
Sistema registra a renovação
          ↓
Relatório das atividades
```

---

## Tecnologias e ferramentas previstas

- **Python** — linguagem principal da aplicação e das automações;
- **PostgreSQL** — armazenamento de usuários, livros, empréstimos, renovações e mensagens;
- **psycopg2 ou SQLAlchemy** — conexão entre Python e PostgreSQL;
- **Google Books API** — busca dos dados do livro pelo ISBN;
- **Requests** — comunicação com APIs via HTTP;
- **WhatsApp Business API ou Twilio API for WhatsApp** — envio e recebimento de mensagens;
- **Webhook** — recebimento das respostas dos usuários;
- **APScheduler** — execução automática da verificação de prazos;
- **ReportLab ou FPDF** — geração de relatórios em PDF;
- **SMTP** — envio do relatório por e-mail;
- **Git / GitHub** — versionamento e controle do código;
- **Figma** — prototipação da interface e dos fluxos.

---

## Estrutura planejada do projeto

```text
Trabalho-biblioteca/
│
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── database/
│   ├── db.sql
│   └── seed.sql
│
├── app/
│   ├── main.py
│   ├── db.py
│   │
│   ├── services/
│   │   ├── google_books.py
│   │   ├── whatsapp.py
│   │   ├── email_service.py
│   │   └── relatorio.py
│   │
│   └── automation/
│       └── verificar_prazos.py
│
├── docs/
│   ├── fluxogramas/
│   └── imagens/
│
└── tests/
```

A estrutura poderá ser ajustada conforme o projeto evoluir.

---

## Pré-requisitos previstos

- Python 3.10+
- PostgreSQL 14+
- Git
- Conta/configuração para a API do WhatsApp escolhida

### Clonar o repositório

```bash
git clone https://github.com/trabalho-do-brunao/Trabalho-biblioteca.git
cd Trabalho-biblioteca
```

---

## Lista de tarefas do projeto

### 1. Configuração do ambiente

- [x] Criar repositório no GitHub
- [ ] Configurar ambiente virtual Python (`venv`)
- [ ] Criar `requirements.txt`
- [ ] Criar `.env.example`
- [ ] Criar `.gitignore`

### 2. Banco de dados — PostgreSQL

- [x] Criar estrutura inicial do banco
- [x] Criar tabelas `usuarios`, `livros` e `emprestimos`
- [ ] Adequar o banco às entidades exigidas pelo BiblioAvisa
- [ ] Criar tabela `renovacoes`
- [ ] Criar/adequar tabela `mensagens`
- [ ] Separar dados de teste em `seed.sql`

### 3. Conexão Python ↔ PostgreSQL

- [ ] Criar módulo `db.py`
- [ ] Configurar conexão por variáveis de ambiente
- [ ] Buscar empréstimos ativos
- [ ] Registrar e atualizar empréstimos
- [ ] Registrar renovações
- [ ] Registrar mensagens enviadas e recebidas

### 4. Cadastro de acervo e Google Books

- [ ] Criar consulta à Google Books API pelo ISBN
- [ ] Buscar título, autor e demais dados disponíveis
- [ ] Permitir conferência dos dados antes do cadastro
- [ ] Salvar o livro no PostgreSQL

### 5. Lógica de verificação de prazos

- [ ] Identificar empréstimos com vencimento em 2 dias
- [ ] Identificar empréstimos que vencem no dia
- [ ] Identificar empréstimos atrasados
- [ ] Evitar mensagens duplicadas para o mesmo evento

### 6. Integração com WhatsApp

- [ ] Configurar WhatsApp Business API ou Twilio
- [ ] Criar serviço de envio de mensagens
- [ ] Criar mensagens de lembrete e atraso
- [ ] Implementar webhook para receber respostas
- [ ] Processar comando de renovação
- [ ] Registrar mensagens no banco

### 7. Relatórios

- [ ] Gerar relatório em PDF
- [ ] Incluir informações sobre empréstimos e mensagens
- [ ] Enviar relatório por e-mail ao responsável

### 8. Agendamento automático

- [ ] Configurar APScheduler ou alternativa equivalente
- [ ] Executar a verificação de prazos automaticamente
- [ ] Criar `main.py` para orquestrar o fluxo da aplicação

### 9. Testes

- [ ] Testar conexão com o banco
- [ ] Testar Google Books API
- [ ] Testar envio e recebimento de mensagens
- [ ] Testar renovação via webhook
- [ ] Testar geração de PDF
- [ ] Testar fluxo completo

### 10. Documentação e entrega

- [ ] Atualizar o README conforme o desenvolvimento
- [ ] Comentar o código quando necessário
- [ ] Adicionar fluxogramas e materiais de apoio
- [ ] Registrar evidências do sistema funcionando
