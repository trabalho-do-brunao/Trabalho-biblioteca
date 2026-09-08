# Autenticação administrativa

A autenticação do painel é separada dos usuários da biblioteca. A tabela `usuarios` continua sendo usada para leitores, empréstimos e WhatsApp. As contas que entram no painel ficam em `administradores`.

## Primeira configuração

Depois de atualizar o projeto, execute `setup.bat` normalmente. Ele aplica a migração que cria as tabelas `administradores` e `sessoes_admin` sem apagar os dados existentes.

Crie a primeira conta administrativa pela raiz do projeto:

```powershell
.\.venv\Scripts\python.exe scripts\criar_admin.py
```

O script solicita nome, e-mail e senha localmente. A senha não é exibida durante a digitação e não é armazenada em texto puro.

Depois, use esse e-mail e essa senha na tela `/login`.

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
- as APIs de usuários, livros, empréstimos, dashboard, WhatsApp e relatórios exigem sessão válida;
- logout remove a sessão do banco e apaga o cookie;
- não há cadastro administrativo público pela tela de login.
