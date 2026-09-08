# BiblioAvisa — Sistema de Gestão de Biblioteca com Integração via WhatsApp

O **BiblioAvisa** é um sistema web para gestão de biblioteca que reúne cadastro de usuários, acervo, empréstimos, devoluções, automações de prazo, notificações por WhatsApp, renovação por resposta, relatórios em PDF/e-mail e autenticação administrativa.

O projeto utiliza **React + Vite** no frontend, **FastAPI/Python** no backend e **PostgreSQL** como banco de dados.

> **Execução local no Windows:** depois de configurar o ambiente, normalmente basta usar `setup.bat` uma vez e `run.bat` para iniciar o sistema.

---

## Trabalhos acadêmicos integrados

Este repositório reúne dois trabalhos desenvolvidos sobre a mesma aplicação.

### Trabalho 1 — Automação de Processos

**Integrantes**

- Guilherme Granemann Benvenutti
- Matheus Guerelus Rizelo
- Matheus Henrique Predes Pereira
- João Pedro Lagos Muraro

O foco é automatizar o acompanhamento dos empréstimos, verificar prazos, enviar notificações pelo WhatsApp, receber solicitações de renovação e gerar relatórios das atividades.

### Diferencial de automação

**Diferencial de automação:** o sistema não apenas realiza notificações programadas. Ele analisa automaticamente os dados dos empréstimos e o histórico de devoluções dos usuários para
identificar situações de risco de atraso. A partir dessa análise, determina o momento adequado para enviar lembretes personalizados através da API do WhatsApp.
Além disso, o usuário pode interagir com o sistema pelo próprio WhatsApp para consultar ou renovar seus empréstimos.

### Trabalho 2 — Tema 14: BiblioAvisa — Biblioteca

**Alunos**

- Guilherme G. Benvenutti
- Matheus Henrique P. Pereira

O trabalho exige cadastro do acervo, controle de empréstimos, avisos antes/no/após o vencimento e renovação por resposta no WhatsApp através de webhook.

---

# Estado atual do sistema

Atualmente já estão implementados:

- Login e cadastro administrativo;
- sessão com cookie `HttpOnly` e senha armazenada com hash;
- Dashboard com indicadores reais do PostgreSQL;
- cadastro, consulta, edição e ativação/inativação de usuários;
- cadastro e consulta de livros;
- busca de livros por ISBN usando Google Books;
- controle de quantidade total e exemplares disponíveis;
- criação de empréstimos;
- devolução de exemplares;
- histórico de empréstimos;
- identificação automática de empréstimos atrasados;
- avisos de prazo por WhatsApp;
- renovação de empréstimos por resposta;
- histórico das mensagens do WhatsApp na interface;
- geração de relatório PDF por período;
- abertura e download do relatório pela interface;
- envio de relatório por e-mail;
- análise de risco de atraso;
- agendamento das rotinas automáticas;
- validações, máscaras, tooltips e tratamento de erros no frontend;
- testes automatizados de frontend, backend e PostgreSQL;
- pipeline de CI/CD com GitHub Actions;
- build Docker da aplicação.

## Próximas etapas

O desenvolvimento entrou na fase de preparação para implantação:

1. remover os dados permanentes de demonstração do `database/seed.sql`;
2. deixar apenas um registro controlado de teste definido pelo grupo;
3. criar o fluxo de instalação e inicialização para Linux/AWS equivalente ao `setup.bat` e `run.bat`;
4. publicar a versão atualizada na AWS;
5. validar o WhatsApp e a automação ponta a ponta já na VM.

---

# Fluxo principal

```text
Administrador faz login
          ↓
Cadastro de usuários e livros
          ↓
Registro do empréstimo
          ↓
PostgreSQL
          ↓
Verificação automática dos prazos
          ↓
2 dias antes → aviso pelo WhatsApp
No vencimento → aviso pelo WhatsApp
Após vencimento → alerta pelo WhatsApp
          ↓
Usuário pode responder RENOVAR
          ↓
Webhook recebe a resposta
          ↓
Sistema valida usuário e empréstimo
          ↓
Renovação registrada no PostgreSQL
          ↓
Dashboard / WhatsApp / Relatórios atualizados
```

---

# Tecnologias utilizadas

- **Python 3.10+** — backend, serviços, automações e webhook;
- **FastAPI + Uvicorn** — API HTTP;
- **PostgreSQL 14+** — banco de dados;
- **psycopg2** — integração Python/PostgreSQL;
- **React 18 + Vite** — frontend web;
- **React Router** — navegação da interface;
- **Lucide React** — ícones;
- **Node.js 20+** — frontend e serviço WhatsApp;
- **Baileys** — integração local com WhatsApp Web;
- **Google Books API** — busca de livros por ISBN;
- **APScheduler** — agendamento das automações;
- **ReportLab** — geração de PDFs;
- **SMTP** — envio de relatórios por e-mail;
- **Docker** — empacotamento da aplicação;
- **GitHub Actions** — testes, build e CI/CD;
- **Git / GitHub** — versionamento e colaboração;
- **Figma** — referência visual da interface.

---

# Interface web

A aplicação possui as seguintes áreas principais:

```text
/login
/cadastro
/dashboard
/livros
/usuarios
/emprestimos
/whatsapp
/relatorios
/configuracoes
```

A navegação interna usa uma barra lateral com:

```text
BIBLIOTECA
Dashboard
Livros
Usuários
Empréstimos
WhatsApp
Relatórios
Configurações
Sair
```

As regras de negócio permanecem no backend. O React faz validações imediatas para melhorar a experiência, mas operações como disponibilidade de estoque, empréstimo, devolução, autenticação e renovação são confirmadas novamente pelo Python/PostgreSQL.

---

# Banco de dados

O banco padrão é `ecf`, usando o schema `public`.

Tabelas principais:

- `usuarios` — leitores da biblioteca;
- `livros` — acervo;
- `emprestimos` — empréstimos e devoluções;
- `renovacoes` — histórico das renovações;
- `mensagens` — mensagens enviadas/recebidas;
- `administradores` — contas que acessam o painel;
- `sessoes_admin` — sessões administrativas.

As migrações ficam em:

```text
database/migrations/
```

O `scripts/init_db.py` cria a estrutura quando necessário, aplica as migrações e valida as tabelas existentes sem apagar dados durante uma inicialização normal.

> O `database/seed.sql` ainda contém dados de demonstração usados durante o desenvolvimento. Essa carga será removida antes da implantação final na AWS.

---

# Autenticação administrativa

Os administradores são separados dos usuários/leitores da biblioteca.

A autenticação utiliza:

- senha armazenada com PBKDF2-HMAC-SHA256 e salt;
- sessão com token aleatório;
- somente o hash do token armazenado no banco;
- cookie `HttpOnly` no navegador;
- expiração de sessão configurável;
- bloqueio das rotas administrativas sem login;
- logout com invalidação da sessão.

Na primeira instalação, se ainda não existir nenhuma conta administrativa, a tela `/cadastro` permite criar o primeiro acesso.

Depois disso, novas contas administrativas são criadas por um administrador autenticado em:

```text
Configurações → Cadastrar administrador
```

---

# Instalação local — Windows

## Pré-requisitos

Antes de executar o projeto, instale:

- Python 3.10 ou superior;
- PostgreSQL 14 ou superior;
- Node.js 20 ou superior;
- Git.

O pgAdmin é opcional.

## Clonar o repositório

```powershell
git clone https://github.com/trabalho-do-brunao/Trabalho-biblioteca.git
cd Trabalho-biblioteca
git switch repositorio-principal
```

## Preparar o ambiente

Na raiz do projeto:

```powershell
.\setup.bat
```

O `setup.bat`:

```text
verifica Python, Node.js e npm
          ↓
cria .venv quando necessário
          ↓
instala requirements.txt
          ↓
instala dependências do Baileys
          ↓
instala dependências React/Vite
          ↓
cria .env quando necessário
          ↓
aplica estrutura e migrações do PostgreSQL
          ↓
valida o banco
```

O arquivo `.env` é local e deve ser preservado entre atualizações.

## Iniciar o sistema

```powershell
.\run.bat
```

O `run.bat` usa automaticamente o Python da `.venv` e inicia tudo em um único terminal:

```text
API FastAPI       → http://127.0.0.1:8000
Frontend React    → http://127.0.0.1:5173
Webhook WhatsApp  → http://127.0.0.1:3002
Baileys            → http://127.0.0.1:3001
Automação diária   → conforme configuração do .env
```

Abra no navegador:

```text
http://127.0.0.1:5173
```

Para testar a API:

```text
http://127.0.0.1:8000/api/health
```

Para encerrar todos os serviços:

```text
Ctrl + C
```

## Portas ocupadas

Antes de iniciar, o sistema verifica:

```text
8000 → FastAPI
5173 → React/Vite
3002 → Webhook
3001 → Baileys
```

Se alguma já estiver em uso, o `run.bat` informa exatamente qual serviço está em conflito antes de iniciar o restante da aplicação.

---

# Uso diário no Windows

Em um computador já configurado:

```powershell
git switch repositorio-principal
git pull
.\run.bat
```

Quando uma atualização trouxer mudanças de dependências ou banco:

```powershell
.\setup.bat
.\run.bat
```

Não é necessário ativar a `.venv` manualmente para usar `run.bat`.

Para executar um script Python diretamente sem ativar o ambiente:

```powershell
.\.venv\Scripts\python.exe scripts\nome_do_script.py
```

---

# Configuração local

As configurações privadas ficam no `.env`.

Principais grupos de configuração:

```text
Aplicação
PostgreSQL
Google Books
Baileys / WhatsApp
Webhook
SMTP / E-mail
Automação diária
Autenticação
```

Nunca coloque credenciais reais em `.env.example`.

Também não envie ao GitHub:

- `.env`;
- senha do PostgreSQL;
- credenciais SMTP;
- tokens/chaves de APIs;
- sessão do WhatsApp;
- números reais utilizados somente em testes.

A sessão do Baileys fica em:

```text
whatsapp_service/auth_info/
```

Essa pasta é local e ignorada pelo Git.

---

# WhatsApp

O serviço Node/Baileys roda localmente na porta `3001`.

O backend Python utiliza esse serviço para enviar mensagens e o webhook local recebe respostas na porta `3002`.

Para processar respostas recebidas, configure no `.env`:

```env
WHATSAPP_INBOUND_ENABLED=true
```

Somente usuários ativos cadastrados no PostgreSQL entram no fluxo de renovação. Contatos desconhecidos ou usuários inativos são ignorados.

O teste real completo do WhatsApp será realizado novamente depois da implantação na AWS.

---

# Automação

A rotina principal pode ser executada automaticamente pelo APScheduler.

Ela realiza, em sequência:

```text
verificação dos empréstimos
          ↓
análise de risco
          ↓
criação das notificações
          ↓
envio pelo WhatsApp
          ↓
geração de relatório PDF
          ↓
envio por e-mail, quando habilitado
```

A automação permanece controlada pelas opções do `.env`.

---

# Relatórios

A tela de Relatórios permite:

- selecionar período;
- gerar relatório em PDF;
- abrir o PDF no navegador;
- baixar o arquivo;
- enviar o relatório por e-mail.

As credenciais SMTP nunca são expostas no frontend.

---

# Testes

Os principais testes Python ficam em `scripts/` e usam dados temporários controlados.

Entre os fluxos validados estão:

- conexão PostgreSQL;
- gestão de livros;
- empréstimos, devoluções e estoque;
- Dashboard;
- histórico do WhatsApp;
- relatórios;
- autenticação;
- detecção de portas do inicializador.

O frontend também possui testes unitários e verificações de qualidade executadas pelo npm.

---

# GitHub Actions / CI/CD

O workflow principal está em:

```text
.github/workflows/cicd.yml
```

Ele é executado em `push` e `pull_request` para `repositorio-principal`.

Fluxo atual:

```text
Código no GitHub
      ↓
Testes React/JavaScript
      ↓
Build React
      ↓
Python + PostgreSQL temporário
      ↓
Testes de integração
      ↓
Build Docker
      ↓
Publicação/deploy quando habilitados
```

A CI utiliza ambiente próprio de teste e não depende de credenciais reais de WhatsApp, e-mail ou banco local.

O build Docker só acontece depois do job de testes passar.

---

# Docker

O `Dockerfile` utiliza build em duas etapas:

```text
node:20-alpine
      ↓
testes + build do React/Vite
      ↓
python:3.12-slim
      ↓
FastAPI + frontend compilado
```

Na imagem final, o FastAPI serve a API e também o frontend compilado pela mesma aplicação.

A porta padrão da imagem é:

```text
8000
```

---

# AWS / Linux

A implantação final será feita em uma VM Linux na AWS.

O projeto já possui Docker e pipeline de CI/CD, mas os arquivos `setup.bat` e `run.bat` são específicos do Windows.

A próxima etapa será criar o equivalente Linux para:

```text
instalar/preparar dependências
inicializar PostgreSQL
aplicar migrações
compilar frontend
iniciar FastAPI
iniciar webhook
iniciar Baileys
iniciar automação
manter os serviços em execução na VM
```

Depois dessa implantação será feito o teste ponta a ponta do WhatsApp diretamente na VM.

---

# Estrutura principal

```text
Trabalho-biblioteca/
│
├── README.md
├── setup.bat
├── run.bat
├── Dockerfile
├── requirements.txt
├── .env.example
│
├── .github/
│   └── workflows/
│       └── cicd.yml
│
├── app/
│   ├── api.py
│   ├── db.py
│   ├── routes/
│   ├── repositories/
│   ├── services/
│   ├── automation/
│   └── webhooks/
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── database/
│   ├── db.sql
│   ├── migrations/
│   └── seed.sql
│
├── scripts/
│   ├── init_db.py
│   ├── iniciar_servicos.py
│   ├── criar_admin.py
│   └── testes auxiliares
│
├── whatsapp_service/
│   ├── package.json
│   ├── server.js
│   └── auth_info/
│
└── docs/
```

---

# Resumo

O BiblioAvisa atualmente possui uma aplicação web funcional com integração entre:

```text
React
  ↓
FastAPI / Python
  ↓
PostgreSQL
  ↓
Google Books / WhatsApp / E-mail
```

O foco atual não é mais criar as telas principais, e sim preparar a versão definitiva do banco e a implantação em Linux/AWS para realizar a validação final do sistema completo.