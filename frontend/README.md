# Frontend do BiblioAvisa

Base web criada com React + Vite. O React cuida da interface; regras de negócio, persistência e automações continuam no backend Python.

## Preparação

Na raiz do repositório, execute `setup.bat` para atualizar as dependências Python. Depois instale as dependências do frontend:

```powershell
cd frontend
npm.cmd install
Copy-Item .env.example .env
```

O uso de `npm.cmd` evita o bloqueio de `npm.ps1` que pode existir em computadores Windows com política de execução restrita.

## Desenvolvimento

Abra dois terminais na raiz do projeto.

Terminal 1 — API Python:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 — React/Vite:

```powershell
cd frontend
npm.cmd run dev
```

Abra `http://127.0.0.1:5173`. O Dashboard mostra o estado da conexão com `/api/health`.

## Configuração

`frontend/.env` é local e ignorado pelo Git. A variável disponível inicialmente é:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Não coloque senhas, tokens ou credenciais no frontend. Dados sensíveis continuam somente no `.env` da raiz e no backend Python.
