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

## 1. Pré-requisitos

Antes de iniciar, o computador precisa possuir:

- **Python 3.10 ou superior**;
- **PostgreSQL 14 ou superior** com o serviço em execução;
- **Node.js 20 ou superior** com npm;
- **Git**, caso o projeto seja obtido por clone.

O pgAdmin 4 é opcional. Ele pode ser usado para visualizar o banco, mas não precisa permanecer aberto para o sistema funcionar.

## 2. Obter a pasta do projeto

Há duas formas simples.

### Opção A — clonar com Git

No PowerShell:

```powershell
git clone https://github.com/trabalho-do-brunao/Trabalho-biblioteca.git
cd Trabalho-biblioteca
git switch repositorio-principal
```

### Opção B — baixar a pasta pelo GitHub

Também é possível baixar o repositório como ZIP pelo GitHub, extrair a pasta em um local de sua preferência e abrir um PowerShell dentro da pasta extraída.

Ao terminar esta etapa, o terminal deve estar na raiz do projeto, onde existem os arquivos:

```text
setup.bat
run.bat
README.md
requirements.txt
```

## 3. Executar o instalador automático

Na raiz do projeto, execute:

```powershell
.\setup.bat
```

**Não crie o `.env` manualmente antes disso.** O próprio `setup.bat` cria o arquivo a partir de `.env.example` quando necessário e preserva o arquivo caso ele já exista.

O instalador faz automaticamente a preparação do projeto:

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
cria .env se ainda não existir
   ↓
abre o .env para preencher os valores locais necessários
   ↓
cria/valida o PostgreSQL e as tabelas
```

Na primeira execução, quando o Bloco de Notas abrir o `.env`, preencha os valores locais necessários, principalmente a senha do PostgreSQL. Salve o arquivo e volte para a janela do instalador.

O `.env` contém informações locais e não deve ser enviado ao GitHub. Não copie credenciais reais para `.env.example`.

O `setup.bat` pode ser executado novamente no futuro. Ele preserva o `.env`, atualiza as dependências e valida o banco sem apagar os dados existentes em uma execução normal.

## 4. Iniciar o sistema

Depois que o `setup.bat` terminar com sucesso, execute:

```powershell
.\run.bat
```

O `run.bat` utiliza automaticamente o Python da `.venv`; não é necessário ativar o ambiente virtual manualmente.

Ele inicia no mesmo terminal:

```text
run.bat
   ↓
scripts/iniciar_servicos.py
   ├── Webhook Python  → 127.0.0.1:3002
   └── Baileys         → 127.0.0.1:3001
```

O resultado esperado inclui mensagens semelhantes a:

```text
[WEBHOOK] [OK] http://127.0.0.1:3002/webhook/whatsapp
[BAILEYS] [OK] Serviço Baileys local em http://127.0.0.1:3001
[BAILEYS] [OK] WhatsApp conectado pelo Baileys.
```

Para encerrar os serviços, pressione:

```text
Ctrl + C
```

## Resumo da primeira instalação

Para quem já possui Python, PostgreSQL, Node.js e Git instalados, o processo principal é:

```powershell
git clone https://github.com/trabalho-do-brunao/Trabalho-biblioteca.git
cd Trabalho-biblioteca
git switch repositorio-principal
.\setup.bat
.\run.bat
```

Se o projeto tiver sido baixado como ZIP, basta entrar na pasta extraída e executar os dois BATs na mesma ordem:

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

Depois de alterar essa opção, encerre e execute novamente:

```powershell
.\run.bat
```

A autorização não é feita por telefone no `.env`. O BiblioAvisa consulta a tabela `usuarios`: somente usuários ativos cadastrados podem entrar no fluxo de renovação; contatos desconhecidos ou usuários inativos são ignorados silenciosamente.

Enquanto a interface web ainda não estiver pronta, um usuário pode ser cadastrado com:

```powershell
.venv\Scripts\python.exe scripts\cadastrar_usuario.py
```

---

# Uso diário

Em um computador que já passou pelo `setup.bat`, normalmente basta atualizar o código e iniciar o sistema.

Se o projeto foi clonado com Git:

```powershell
git switch repositorio-principal
git pull
.\run.bat
```

Se uma atualização trouxer mudanças de dependências, ou se houver dúvida sobre o ambiente local, execute novamente:

```powershell
.\setup.bat
.\run.bat
```

Como o `setup.bat` é reutilizável, não é necessário executar `pip install`, `npm install` ou recriar `.env` manualmente como parte do fluxo normal.

---

## Estrutura principal do projeto

```text
Trabalho-biblioteca/
│
├── README.md
├── setup.bat                    # prepara Python, Node/Baileys, .env e PostgreSQL
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

### `run.bat` informa que `.venv` ou `node_modules` não existe

Execute novamente o instalador:

```powershell
.\setup.bat
```

### PowerShell bloqueia `npm.ps1`

O fluxo normal não precisa executar `npm install` manualmente. O `setup.bat` chama `npm.cmd` diretamente e evita esse bloqueio do PowerShell.

### Erro de conexão com PostgreSQL

Confira se o serviço PostgreSQL está iniciado. Depois execute:

```powershell
.\setup.bat
```

Se o instalador indicar erro de credenciais, corrija somente o `.env` local e execute o `setup.bat` novamente.

### Portas 3001 ou 3002 já estão em uso

Feche instâncias antigas do BiblioAvisa ou terminais que ainda estejam executando os serviços e rode novamente:

```powershell
.\run.bat
```

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

Já estão implementados o banco de dados, cadastro de usuários, integração com Google Books, empréstimos e devoluções, verificação dos prazos obrigatórios, envio pelo WhatsApp via Baileys, renovação por resposta, relatórios em PDF e o inicializador conjunto `run.bat`.

As próximas etapas incluem envio de relatório por e-mail, diferencial de análise de risco, agendamento/orquestração do fluxo principal, interface web e testes/documentação finais.

---

## Interface web

A interface escolhida para o projeto será **web**, baseada nas telas desenhadas no Figma. A implementação prevista utilizará React + Vite e consumirá o backend Python sem duplicar as regras de negócio já existentes.

O objetivo é permitir pela interface operações como cadastro e consulta de usuários, busca e cadastro de livros por ISBN, empréstimos, devoluções, consulta de atrasos, mensagens e relatórios.
