# BiblioAvisa na AWS/Linux

A implantação Linux usa Docker Compose para substituir o fluxo local de `setup.bat` e `run.bat`.

## Estrutura

```text
AWS EC2 / Ubuntu
├── PostgreSQL 17        (rede interna Docker)
├── FastAPI + React      (porta pública 8000)
├── Webhook WhatsApp     (rede interna Docker)
├── Baileys              (rede interna Docker)
└── Automação diária     (opcional pelo .env)
```

O frontend não usa Vite em produção. O Dockerfile compila o React e o FastAPI entrega a interface e a API na mesma porta.

## Primeira instalação

Depois de clonar o repositório e entrar na branch `repositorio-principal`:

```bash
bash setup_linux.sh
```

Na primeira execução, se `.env` ainda não existir, o script cria o arquivo e pede para configurá-lo:

```bash
nano .env
```

Configure pelo menos `DB_PASSWORD`. Para o primeiro teste por endereço IP/HTTP mantenha:

```env
AUTH_COOKIE_SECURE=false
WHATSAPP_INBOUND_ENABLED=false
AUTOMACAO_ENABLED=false
```

Depois rode novamente:

```bash
bash setup_linux.sh
```

O script instala/valida Docker e Docker Compose, constrói as imagens, cria o volume do PostgreSQL e executa `scripts/init_db.py`. Nenhum dado de demonstração é inserido.

## Iniciar

```bash
bash run_linux.sh
```

A aplicação fica disponível por padrão em:

```text
http://IP_PUBLICO_DA_VM:8000
```

No Security Group da EC2, somente a porta necessária para a aplicação deve ser liberada para acesso externo. PostgreSQL, Baileys e webhook não precisam de portas públicas.

## Comandos úteis

```bash
bash run_linux.sh status
bash run_linux.sh logs
bash run_linux.sh restart
bash run_linux.sh stop
```

Para acompanhar apenas o Baileys e visualizar o QR Code na primeira vinculação:

```bash
docker compose -f docker-compose.aws.yml logs -f baileys
```

A sessão do WhatsApp fica no volume Docker `whatsapp_auth` e sobrevive a reinicializações normais dos containers.

## Atualização do código

Depois de um novo merge:

```bash
git switch repositorio-principal
git pull
bash run_linux.sh restart
```

O `run_linux.sh` reconstrói as imagens, inicia o PostgreSQL e executa novamente as migrações antes de subir os serviços.

## Automação e WhatsApp

Durante a implantação inicial, mantenha:

```env
WHATSAPP_INBOUND_ENABLED=false
AUTOMACAO_ENABLED=false
```

Depois de validar a interface, banco e Login na VM, faça a vinculação do Baileys e só então ative o recebimento de respostas e a automação de forma controlada.

## HTTPS

Enquanto o acesso estiver sendo testado diretamente pelo IP e porta 8000, use:

```env
AUTH_COOKIE_SECURE=false
```

Quando a aplicação estiver atrás de HTTPS, altere para:

```env
AUTH_COOKIE_SECURE=true
```

Depois reinicie:

```bash
bash run_linux.sh restart
```
