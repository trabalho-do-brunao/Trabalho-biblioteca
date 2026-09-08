# Autenticação administrativa

A autenticação do painel é separada dos usuários da biblioteca. A tabela `usuarios` continua sendo usada para leitores, empréstimos e WhatsApp. As contas que entram no painel ficam em `administradores`.

## Primeira configuração

Depois de atualizar o projeto, execute `setup.bat` normalmente. Ele aplica as migrações de autenticação sem apagar os dados existentes.

Quando ainda não existe nenhum administrador, a tela `/cadastro` permite criar a primeira conta. O formulário solicita nome, sobrenome, CPF, data de nascimento, WhatsApp, e-mail e senha. CPF, telefone e data são validados novamente pelo backend antes da gravação.

Também continua disponível o script local para criação da primeira conta:

```powershell
.\.venv\Scripts\python.exe scripts\criar_admin.py
```

Depois que existe pelo menos um administrador, o cadastro público é bloqueado. Novas contas só podem ser criadas por um administrador autenticado em **Configurações → Cadastrar administrador**.

## Sessão

O login cria uma sessão com duração padrão de 8 horas. A duração pode ser ajustada no `.env`:

```env
AUTH_SESSION_HOURS=8
```

O navegador recebe apenas um cookie `HttpOnly`. O token puro da sessão não é salvo no PostgreSQL: o banco mantém apenas seu hash SHA-256.

Em `APP_ENV=production`, o cookie é marcado como `Secure`, portanto a implantação de produção deve usar HTTPS.

## Segurança

- senhas usam PBKDF2-HMAC-SHA256 com salt aleatório;
- a senha nunca é retornada pela API;
- contas administrativas são separadas dos leitores da biblioteca;
- o primeiro cadastro público só é permitido enquanto não existir administrador;
- cadastros posteriores exigem uma sessão administrativa válida;
- as APIs de usuários, livros, empréstimos, dashboard, WhatsApp e relatórios exigem sessão válida;
- logout remove a sessão do banco e apaga o cookie;
- CPF e e-mail possuem proteção contra duplicidade no banco.
