# BiblioAvisa — Sistema de Gestão de Biblioteca com Integração via WhatsApp

Este repositório integra dois trabalhos acadêmicos relacionados à automação e à gestão de bibliotecas. As propostas se complementam e são desenvolvidas dentro do mesmo sistema e do mesmo banco de dados PostgreSQL.

> **Primeira instalação?** O fluxo recomendado é simples: obter a pasta do projeto, executar `setup.bat` e depois executar `run.bat`.

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

Os dois trabalhos são implementados como partes do mesmo sistema. O cadastro do acervo e dos empréstimos forma a base da aplicação, enquanto a automação utiliza esses dados para acompanhar os prazos de devolução, enviar mensagens pelo WhatsApp, receber solicitações de renovação e gerar relatórios.

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
Sistema valida o usuário no PostgreSQL
          ↓
Sistema registra a renovação
          ↓
Relatório das atividades
```

---

## Tecnologias utilizadas

- **Python 3.10+** — aplicação, regras de negócio, automações, API FastAPI e webhook;
- **PostgreSQL 14+** — armazenamento dos dados do sistema;
- **psycopg2** — conexão entre Python e PostgreSQL;
- **FastAPI + Uvicorn** — API HTTP consumida pelo frontend;
- **Google Books API** — consulta de livros pelo ISBN;
- **Requests** — comunicação HTTP no backend;
- **Node.js 20+** — frontend e serviço local de WhatsApp;
- **Baileys** — integração não oficial com WhatsApp Web por sessão vinculada;
- **APScheduler** — agendamento das automações;
- **ReportLab** — geração dos relatórios em PDF;
- **SMTP** — envio de relatórios por e-mail;
- **React + Vite** — interface web do sistema;
- **Docker + GitHub Actions** — build e integração contínua;
- **Git / GitHub** — versionamento e colaboração;
- **Figma** — prototipação das telas e fluxos.

---

# Instalação em um computador novo

## 1. Pré-requisitos

Antes de iniciar, o computador precisa possuir:

- **Python 3.10 ou superior**;
- **PostgreSQL 14 ou superior** com o serviço em execução;
- **Node.js 20 ou superior** com npm;
- **Git**, caso o projeto seja obtido por clone.

O pgAdmin 4 é opcional. Ele pode ser usado para visualizar o banco, mas não precisa permanecer aberto para o sistema funcionar.

## 2. Obter a pasta do projeto

### Opção A — clonar com Git

No PowerShell:

```powershell
git clone https://github.com/trabalho-do-brunao/Trabalho-biblioteca.git
cd Trabalho-biblioteca
git switch repositorio-principal
```

### Opção B — baixar pelo GitHub

Também é possível baixar o repositório como ZIP pelo GitHub, extrair a pasta e abrir um PowerShell na raiz do projeto.

Ao terminar esta etapa, o terminal deve estar na pasta onde existem:

```text
setup.bat
run.bat
README.md
requirements.txt
frontend/
whatsapp_service/
```

## 3. Executar o instalador automático

Na raiz do projeto:

```powershell
.\setup.bat
```

**Não é necessário criar o `.env` manualmente antes disso.** O próprio `setup.bat` cria o arquivo a partir de `.env.example` quando necessário e preserva o `.env` caso ele já exista.

O instalador prepara backend e frontend:

```text
setup.bat
   ↓
confere Python, Node.js e npm
   ↓
cria .venv se necessário
   ↓
instala/atualiza requirements.txt
   ↓
instala/atualiza dependências do Baileys com npm.cmd
   ↓
instala/atualiza dependências do React/Vite com npm.cmd
   ↓
cria .env e frontend/.env quando ainda não existem
   ↓
abre o .env para preencher os valores locais necessários
   ↓
cria/atualiza/valida o PostgreSQL e aplica as migrações
```

Na primeira execução, quando o Bloco de Notas abrir o `.env`, preencha apenas os valores locais necessários, principalmente a senha do PostgreSQL. Salve o arquivo e volte para a janela do instalador.

O `.env` contém informações locais e não deve ser enviado ao GitHub. Não copie credenciais reais para `.env.example`.

O `setup.bat` é reutilizável. Ele pode ser executado novamente após um `git pull` para sincronizar dependências e aplicar novas migrações sem apagar o `.env` ou os dados existentes em uma execução normal.

## 4. Iniciar o sistema

Depois que o `setup.bat` terminar com sucesso:

```powershell
.\run.bat
```

O `run.bat` utiliza automaticamente o Python da `.venv`; não é necessário ativar o ambiente virtual manualmente e não é necessário abrir vários terminais.

Ele inicia e supervisiona:

```text
run.bat
   ↓
scripts/iniciar_servicos.py
   ├── API FastAPI       → http://127.0.0.1:8000
   ├── Frontend React    → http://127.0.0.1:5173
   ├── Webhook WhatsApp  → http://127.0.0.1:3002
   ├── Baileys           → http://127.0.0.1:3001
   └── Automação diária  → opcional, conforme o .env
```

O terminal mostra os endereços dos serviços durante a inicialização. Para acessar a aplicação em desenvolvimento, abra:

```text
http://127.0.0.1:5173
```

A API pode ser verificada em:

```text
http://127.0.0.1:8000/api/health
```

Para encerrar todos os processos iniciados pelo `run.bat`, pressione:

```text
Ctrl + C
```

O inicializador encerra API, Vite, Baileys, webhook e automação de forma centralizada.

### Verificação de portas

Antes de iniciar os serviços, o BiblioAvisa verifica as portas usadas localmente:

```text
8000 → API FastAPI
5173 → Frontend React/Vite
3002 → Webhook WhatsApp
3001 → Baileys
```

Se uma delas já estiver ocupada, o `run.bat` interrompe a inicialização e informa qual porta e qual serviço estão em conflito. Isso normalmente significa que outra instância do BiblioAvisa, Vite, FastAPI ou Baileys ainda está aberta.

## Resumo da primeira instalação

```powershell
git clone https://github.com/trabalho-do-brunao/Trabalho-biblioteca.git
cd Trabalho-biblioteca
git switch repositorio-principal
.\setup.bat
.\run.bat
```

Se o projeto tiver sido baixado como ZIP, basta entrar na pasta extraída e executar:

```powershell
.\setup.bat
.\run.bat
```

---

## Primeira conexão com o WhatsApp

A sessão do Baileys é local e não é enviada ao GitHub. Em um computador novo, o `run.bat` pode exibir um QR Code no terminal.

No WhatsApp da conta utilizada pelo BiblioAvisa, abra **Aparelhos/Dispositivos conectados**, escolha a opção de vincular um aparelho e escaneie o QR Code.

Depois da vinculação, a sessão fica em `whatsapp_service/auth_info`, pasta ignorada pelo Git.

---

## Recebimento de respostas do WhatsApp

O envio de mensagens funciona independentemente do recebimento automático. Para permitir que o sistema processe respostas como `RENOVAR`, edite o `.env` local e utilize:

```env
WHATSAPP_INBOUND_ENABLED=true
```

Depois de alterar essa opção, reinicie:

```powershell
.\run.bat
```

A autorização não é feita por telefone no `.env`. O BiblioAvisa consulta a tabela `usuarios`: somente usuários ativos cadastrados podem entrar no fluxo de renovação; contatos desconhecidos ou usuários inativos são ignorados silenciosamente.

Os leitores podem ser administrados diretamente pela tela **Usuários** da interface web.

---

# Uso diário

Em um computador que já passou pelo `setup.bat`, normalmente basta atualizar o código e iniciar o sistema:

```powershell
git switch repositorio-principal
git pull
.\run.bat
```

Se uma atualização trouxer dependências ou migrações novas, ou se houver dúvida sobre o ambiente local:

```powershell
.\setup.bat
.\run.bat
```

Como o `setup.bat` é reutilizável, não é necessário executar `pip install`, `npm install` ou recriar `.env` manualmente no fluxo normal.

---

## Estrutura principal do projeto

```text
Trabalho-biblioteca/
│
├── README.md
├── setup.bat                    # prepara backend, frontend, .env e banco
├── run.bat                      # inicia todos os serviços locais
├── requirements.txt
├── Dockerfile
├── .env.example                 # modelo sem credenciais reais
├── .github/workflows/           # CI/CD GitHub Actions
│
├── app/
│   ├── api.py                   # API FastAPI
│   ├── db.py
│   ├── routes/                  # endpoints HTTP
│   ├── repositories/            # acesso ao PostgreSQL
│   ├── services/                # regras e integrações
│   ├── automation/              # verificações e notificações
│   └── webhooks/                # respostas do WhatsApp
│
├── frontend/                    # React + Vite
│   ├── src/
│   └── package.json
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
│   └── scripts de teste
│
├── whatsapp_service/
│   ├── package.json
│   ├── server.js
│   └── auth_info/               # sessão local, ignorada pelo Git
│
├── docs/
└── tests/
```

---

## Banco de dados

O banco padrão é `ecf`, utilizando o schema `public`.

As tabelas principais incluem:

- `usuarios`;
- `livros`;
- `emprestimos`;
- `renovacoes`;
- `mensagens`;
- `administradores`;
- `sessoes_admin`.

O `scripts/init_db.py` cria o banco quando permitido, executa a estrutura base quando necessário, aplica as migrações em ordem e valida a estrutura esperada. Ele não apaga os dados existentes durante uma inicialização normal.

---

## Autenticação administrativa

As contas que acessam o painel são separadas dos leitores da biblioteca. O Login usa uma sessão com cookie `HttpOnly`, e as senhas são persistidas somente em formato de hash.

Na primeira instalação, enquanto ainda não existir nenhuma conta administrativa, é possível utilizar a tela de Cadastro. Contas adicionais são criadas por um administrador autenticado em **Configurações → Cadastrar administrador**.

---

## Solução rápida de problemas

### `run.bat` informa que `.venv` ou `node_modules` não existe

Execute novamente:

```powershell
.\setup.bat
```

### PowerShell bloqueia `npm.ps1`

O fluxo normal não depende de `npm.ps1`. O `setup.bat` utiliza `npm.cmd` para preparar tanto o frontend quanto o serviço WhatsApp.

### Erro de conexão com PostgreSQL

Confira se o serviço PostgreSQL está iniciado. Depois execute:

```powershell
.\setup.bat
```

Se o instalador indicar erro de credenciais, corrija somente o `.env` local e execute novamente.

### Porta 8000, 5173, 3001 ou 3002 já está em uso

O `run.bat` agora identifica a porta ocupada antes de iniciar o restante do sistema. Feche a instância antiga indicada no terminal e execute novamente:

```powershell
.\run.bat
```

As portas 3001 e 3002 podem ser ajustadas pelas configurações do `.env` quando necessário. As portas 8000 e 5173 são as portas locais padrão do backend e frontend durante o desenvolvimento.

### WhatsApp não processa `RENOVAR`

Confira se `WHATSAPP_INBOUND_ENABLED=true`, se o remetente é um usuário ativo cadastrado e se o terminal indica que o Baileys está conectado.

### WhatsApp pede QR Code novamente

A sessão é local a cada computador. Se a pasta de sessão não existir ou a conta tiver sido desvinculada, uma nova vinculação será necessária.

---

## Segurança e arquivos locais

Nunca envie ao GitHub:

- `.env`;
- senhas do PostgreSQL;
- chaves de API;
- credenciais SMTP;
- números reais usados apenas em testes;
- arquivos da sessão `whatsapp_service/auth_info`.

O `.env.example` deve conter somente nomes de variáveis e valores de exemplo seguros.

---

## Estado atual do desenvolvimento

Já estão integrados o banco PostgreSQL, cadastro e gestão de usuários, acervo com Google Books, empréstimos e devoluções, Dashboard, notificações e renovação pelo WhatsApp, relatórios em PDF/e-mail, análise de risco, agendamento das automações, autenticação administrativa e a interface React + Vite.

O projeto também possui testes automatizados e um pipeline GitHub Actions que valida frontend, backend, PostgreSQL e a imagem Docker antes das etapas de publicação/deploy configuradas.

A limpeza dos dados de demonstração do `database/seed.sql` será realizada somente após as validações finais do sistema, mantendo depois apenas o registro de teste controlado definido pelo grupo.

---

## Interface web

A interface é implementada em **React + Vite** e consome a API FastAPI. As regras de negócio definitivas permanecem no backend Python.

Atualmente a interface possui Login/Cadastro administrativo, Dashboard, Usuários, Livros, Empréstimos, WhatsApp, Relatórios e Configurações, com validações, máscaras, tooltips e tratamento controlado de erros.
