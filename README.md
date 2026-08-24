# BiblioAvisa — Sistema de Gestão de Biblioteca com Integração via WhatsApp

Este repositório integra dois trabalhos acadêmicos relacionados à automação e à gestão de bibliotecas. As propostas se complementam e são desenvolvidas dentro do mesmo sistema e do mesmo banco de dados PostgreSQL.

> **Quer apenas iniciar o projeto em um computador que já está configurado?** Vá direto para [Uso diário](#uso-diário).

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

- **Python 3.10+** — aplicação, regras de negócio, automações e webhook;
- **PostgreSQL 14+** — armazenamento dos dados do sistema;
- **psycopg2** — conexão entre Python e PostgreSQL;
- **Google Books API** — consulta de livros pelo ISBN;
- **Requests** — comunicação HTTP no backend;
- **Node.js 20+** — execução do serviço local de WhatsApp;
- **Baileys** — integração não oficial com WhatsApp Web por sessão vinculada;
- **APScheduler** — agendamento das automações;
- **ReportLab** — geração dos relatórios em PDF;
- **SMTP** — envio de relatórios por e-mail;
- **React + Vite** — tecnologia planejada para a interface web;
- **Git / GitHub** — versionamento e colaboração;
- **Figma** — prototipação das telas e fluxos.

---

# Instalação em um computador novo

Esta seção contém o caminho completo desde o clone até o `run.bat`.

## 1. Pré-requisitos

Instale antes de clonar o projeto:

- **Git**;
- **Python 3.10 ou superior**;
- **PostgreSQL 14 ou superior**;
- **Node.js 20 ou superior**, acompanhado do npm;
- um editor como **Visual Studio Code** é recomendado, mas não obrigatório.

O servidor PostgreSQL precisa estar em execução. O pgAdmin 4 é opcional: ele serve para visualizar e administrar o banco, mas não precisa ficar aberto enquanto o sistema roda.

Para conferir as instalações no PowerShell:

```powershell
git --version
python --version
node --version
npm --version
```

## 2. Clonar o repositório

```powershell
git clone https://github.com/trabalho-do-brunao/Trabalho-biblioteca.git
cd Trabalho-biblioteca
```

A branch principal de desenvolvimento do projeto é `repositorio-principal`.

Confira com:

```powershell
git branch --show-current
```

Se necessário:

```powershell
git switch repositorio-principal
git pull
```

## 3. Preparar Python, `.env` e PostgreSQL

Na raiz do projeto, execute:

```powershell
.\setup.bat
```

O `setup.bat`:

1. localiza o Python instalado;
2. cria `.venv` caso ainda não exista;
3. instala/atualiza `requirements.txt`;
4. cria `.env` a partir de `.env.example` somente se o arquivo ainda não existir;
5. preserva um `.env` já existente;
6. executa `scripts/init_db.py` para criar/validar o banco e as tabelas.

Na primeira execução, o `.env` será aberto para configuração. **Nunca envie esse arquivo ao GitHub.**

No mínimo, confira os dados do PostgreSQL:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecf
DB_USER=postgres
DB_PASSWORD=SUA_SENHA_LOCAL
DB_MAINTENANCE_NAME=postgres
```

Para utilizar a consulta por ISBN, configure também sua própria chave:

```env
GOOGLE_BOOKS_API_KEY=SUA_CHAVE_LOCAL
```

Para permitir que usuários ativos cadastrados no PostgreSQL respondam às mensagens de renovação:

```env
WHATSAPP_INBOUND_ENABLED=true
```

Com `WHATSAPP_INBOUND_ENABLED=false`, o serviço continua podendo enviar mensagens, mas não processa respostas recebidas.

As variáveis SMTP podem permanecer vazias enquanto a funcionalidade de e-mail não estiver configurada.

## 4. Instalar as dependências do WhatsApp

O serviço Baileys utiliza Node.js e possui dependências próprias. Na primeira instalação do computador, execute:

```powershell
cd whatsapp_service
npm install
cd ..
```

A pasta `node_modules` é local e não é enviada ao GitHub.

## 5. Iniciar o BiblioAvisa

Com o ambiente preparado, basta executar na raiz:

```powershell
.\run.bat
```

Não é necessário ativar manualmente o `.venv` para usar o `run.bat`. Ele utiliza diretamente o Python do ambiente virtual.

O inicializador sobe no mesmo terminal:

```text
run.bat
   ↓
scripts/iniciar_servicos.py
   ├── Webhook Python    → 127.0.0.1:3002
   └── Serviço Baileys   → 127.0.0.1:3001
```

Para encerrar os dois serviços:

```text
Ctrl + C
```

## 6. Primeira conexão com o WhatsApp neste computador

A sessão do Baileys fica somente no computador local e não é enviada ao GitHub. Por isso, em um computador novo, o terminal poderá exibir um QR Code.

No WhatsApp da conta que será usada pelo BiblioAvisa, abra a área de **Aparelhos/Dispositivos conectados**, escolha a opção de vincular um aparelho e escaneie o QR Code exibido no terminal.

Depois da primeira vinculação, a sessão é mantida em `whatsapp_service/auth_info` e normalmente não será necessário escanear o QR novamente naquele computador.

## 7. Cadastrar usuários autorizados a responder pelo WhatsApp

O BiblioAvisa não utiliza uma lista de telefones no `.env`. A autorização é feita pelo próprio banco de dados.

Somente um telefone pertencente a um **usuário ativo** da tabela `usuarios` pode entrar no fluxo de renovação. Contatos desconhecidos ou usuários inativos são ignorados silenciosamente.

Enquanto a interface web ainda não estiver pronta, um usuário pode ser cadastrado pelo terminal:

```powershell
.venv\Scripts\python.exe scripts\cadastrar_usuario.py
```

O script solicita nome, telefone e e-mail opcional e utiliza as mesmas validações do backend.

---

# Uso diário

Depois que o computador já passou pela instalação inicial, normalmente basta entrar na pasta do projeto e executar:

```powershell
git switch repositorio-principal
git pull
.\run.bat
```

Se o `git pull` trouxer alterações em `requirements.txt`, rode novamente:

```powershell
.\setup.bat
```

Se trouxer alterações em `whatsapp_service/package.json` ou `package-lock.json`, rode:

```powershell
cd whatsapp_service
npm install
cd ..
```

Depois, volte ao uso normal com:

```powershell
.\run.bat
```

---

## Estrutura principal do projeto

```text
Trabalho-biblioteca/
│
├── README.md
├── setup.bat                    # prepara Python, .env e PostgreSQL
├── run.bat                      # inicia os serviços locais
├── requirements.txt
├── .env.example                 # modelo sem credenciais reais
├── .gitignore
│
├── app/
│   ├── db.py
│   ├── repositories/            # acesso aos dados do PostgreSQL
│   ├── services/                # regras e integrações da aplicação
│   ├── automation/              # verificações e envio de notificações
│   └── webhooks/                # recebimento das respostas do WhatsApp
│
├── database/
│   ├── db.sql
│   └── seed.sql
│
├── scripts/
│   ├── init_db.py
│   ├── iniciar_servicos.py
│   ├── cadastrar_usuario.py
│   ├── cadastrar_livro_isbn.py
│   ├── gerar_relatorio_pdf.py
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

A estrutura continuará evoluindo com a implementação da interface web.

---

## Banco de dados

O banco padrão é `ecf`, utilizando o schema `public`.

As tabelas principais são:

- `usuarios`;
- `livros`;
- `emprestimos`;
- `renovacoes`;
- `mensagens`.

O `scripts/init_db.py` cria o banco quando permitido, executa `database/db.sql`, aplica os dados de demonstração de forma segura e valida a estrutura esperada. Ele não deve apagar dados existentes durante uma inicialização normal.

---

## Solução rápida de problemas

### `run.bat` informa que `.venv` não existe

Execute:

```powershell
.\setup.bat
```

### Erro de conexão com PostgreSQL

Confira se o serviço PostgreSQL está iniciado e revise `DB_HOST`, `DB_PORT`, `DB_USER` e `DB_PASSWORD` no `.env` local.

### `node` não foi encontrado

Instale Node.js 20 ou superior e abra um novo terminal.

### `node_modules` não existe

Execute:

```powershell
cd whatsapp_service
npm install
cd ..
```

### Portas 3001 ou 3002 já estão em uso

Feche instâncias antigas do BiblioAvisa ou terminais que ainda estejam executando o Baileys/webhook e rode novamente:

```powershell
.\run.bat
```

### WhatsApp não processa `RENOVAR`

Confira se:

- `WHATSAPP_INBOUND_ENABLED=true` no `.env`;
- o telefone do remetente está cadastrado na tabela `usuarios`;
- o usuário está com `ativo = true`;
- o Baileys aparece como conectado no terminal.

### WhatsApp pede QR Code novamente

A sessão é local a cada computador. Se ela não existir ou tiver sido desvinculada, uma nova vinculação será necessária.

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

Já estão implementados o banco de dados, cadastro de usuários, integração com Google Books, empréstimos e devoluções, verificação dos prazos obrigatórios, envio pelo WhatsApp via Baileys, renovação por resposta, relatórios em PDF e o inicializador conjunto `run.bat`.

As próximas etapas incluem envio de relatório por e-mail, diferencial de análise de risco, agendamento/orquestração do fluxo principal, interface web e testes/documentação finais.

---

## Interface web

A interface escolhida para o projeto será **web**, baseada nas telas desenhadas no Figma. A implementação prevista utilizará React + Vite e consumirá o backend Python sem duplicar as regras de negócio já existentes.

O objetivo é permitir pela interface operações como cadastro e consulta de usuários, busca e cadastro de livros por ISBN, empréstimos, devoluções, consulta de atrasos, mensagens e relatórios.
