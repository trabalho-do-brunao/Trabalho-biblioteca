# CI/CD do BiblioAvisa

Este documento descreve a integração contínua e o deploy contínuo do BiblioAvisa.
O fluxo foi inspirado no exercício de GitHub Actions utilizado em aula, mas foi
adaptado para a arquitetura real do projeto: React/Vite, FastAPI/Python e
PostgreSQL.

## Fluxo

```text
feature branch / Pull Request
        |
        v
GitHub Actions - job testar
        |
        +-- Node 20
        +-- testes unitários JavaScript
        +-- testes de máscaras/validações
        +-- build do React
        +-- Python 3.12
        +-- validação de sintaxe
        +-- PostgreSQL 17 temporário
        +-- inicialização e teste da integração com o banco
        |
        v
GitHub Actions - job construir-imagem
        |
        +-- Docker Buildx
        +-- build completo do Dockerfile
        |
        v
merge/push em repositorio-principal
        |
        v
publicar-docker-hub (quando PUBLISH_ENABLED=true)
        |
        +-- autenticação por Secrets
        +-- biblioavisa:latest
        +-- biblioavisa:sha-<commit>
        |
        v
deploy-render (quando DEPLOY_ENABLED=true)
        |
        +-- Render Deploy Hook
        v
produção
```

O workflow também possui `workflow_dispatch`, permitindo executar o pipeline
manualmente pela aba **Actions > CI/CD BiblioAvisa > Run workflow** depois que a
configuração estiver presente em `repositorio-principal`.

## Arquivos principais

- `.github/workflows/cicd.yml`: pipeline CI/CD.
- `Dockerfile`: imagem full-stack do BiblioAvisa.
- `.dockerignore`: impede que segredos e arquivos locais entrem no contexto Docker.
- `frontend/scripts/validation.test.mjs`: suíte unitária com `node:test`.
- `frontend/src/services/api.js`: usa `127.0.0.1:8000` em desenvolvimento e a mesma origem da página em produção.
- `app/frontend.py`: entrega o build do React pelo FastAPI quando `frontend_dist` existe.

## Dockerfile

O Dockerfile é multi-stage:

1. `node:20-alpine` instala o frontend, roda os testes e executa `vite build`.
2. `python:3.12-slim` instala o backend e recebe apenas o conteúdo final de `dist`.

A aplicação final expõe uma única porta. O FastAPI responde `/api/*` e também
entrega o React compilado. Isso reduz a quantidade de serviços necessária para a
primeira publicação do projeto.

O WhatsApp/Baileys não é incluído nesta imagem web. Quando for publicado em
infraestrutura real, deve ser tratado como worker/serviço separado porque mantém
uma sessão persistente própria.

## CI - job `testar`

O workflow é disparado por:

- `pull_request` direcionado para `repositorio-principal`;
- `push` em `repositorio-principal`;
- execução manual por `workflow_dispatch`.

O nome do check principal é `testar`, permitindo usá-lo em um Ruleset da branch.

As etapas são:

1. checkout do código;
2. Node 20;
3. `npm install` no frontend;
4. `npm run test:unit`;
5. `npm run test:quality`;
6. `npm run build`;
7. Python 3.12;
8. instalação de `requirements.txt`;
9. `python -m compileall -q app scripts`;
10. criação de um `.env` exclusivamente de CI;
11. PostgreSQL 17 temporário;
12. `python scripts/init_db.py`;
13. `python scripts/test_db.py`.

O projeto ainda não versiona `frontend/package-lock.json`, então o pipeline usa
`npm install`. Quando o lockfile passar a ser versionado, o recomendado é trocar
para `npm ci` para builds ainda mais reproduzíveis.

Qualquer comando com código de saída diferente de zero encerra o job. Como os
jobs seguintes dependem de `testar`, uma falha bloqueia o build/publicação.

## Proteção de `repositorio-principal`

Criar um Ruleset em **Settings > Rules > Rulesets** com:

- Target: `repositorio-principal`;
- Require a pull request before merging;
- Require status checks to pass;
- check obrigatório: `testar`;
- Require branches to be up to date before merging;
- Block force pushes.

Com isso, um teste vermelho deixa de ser apenas um aviso e passa a impedir o merge.

## Publicação no Docker Hub

Criar no Docker Hub um repositório chamado `biblioavisa` e gerar um Personal Access Token
com permissão suficiente para leitura e escrita da imagem. Nunca salvar o token no
`.env`, Dockerfile, YAML ou README.

No GitHub, em **Settings > Secrets and variables > Actions > Secrets**, criar:

- `DOCKERHUB_USERNAME`: usuário do Docker Hub;
- `DOCKERHUB_TOKEN`: Personal Access Token do Docker Hub;
- `RENDER_DEPLOY_HOOK`: URL secreta do Deploy Hook do serviço Render, adicionada somente depois da criação do serviço.

Em **Variables**, usar duas chaves separadas:

- `PUBLISH_ENABLED=true`: habilita a publicação no Docker Hub;
- `DEPLOY_ENABLED=true`: habilita o disparo do deploy no Render.

A separação evita uma dependência circular na primeira configuração. O processo é:

1. configurar Docker Hub e os Secrets `DOCKERHUB_*`;
2. definir `PUBLISH_ENABLED=true` e deixar `DEPLOY_ENABLED=false`;
3. executar o workflow em `repositorio-principal` para publicar a primeira imagem;
4. criar o serviço Render apontando para a imagem `latest` já existente;
5. gerar o Deploy Hook e salvá-lo em `RENDER_DEPLOY_HOOK`;
6. definir `DEPLOY_ENABLED=true`;
7. a partir daí, cada execução aprovada publica a imagem e aciona o deploy.

Enquanto `PUBLISH_ENABLED` não for `true`, testes e build Docker continuam
funcionando normalmente, mas nenhuma imagem externa é enviada. Enquanto
`DEPLOY_ENABLED` não for `true`, a imagem pode ser publicada sem acionar o Render.

## Tags da imagem

Cada publicação em `repositorio-principal` gera:

- `<usuario>/biblioavisa:latest`;
- `<usuario>/biblioavisa:sha-<commit>`.

`latest` representa a versão atual de produção. A tag de SHA permite identificar
e restaurar exatamente a imagem correspondente a um commit.

## Render

Criar um Web Service no Render baseado em **Existing Image** e apontar para:

```text
docker.io/<usuario-docker-hub>/biblioavisa:latest
```

Configurar no serviço as variáveis de produção, principalmente:

- `APP_ENV=production`;
- `DB_HOST`;
- `DB_PORT`;
- `DB_NAME`;
- `DB_USER`;
- `DB_PASSWORD`.

Esses valores pertencem ao ambiente do Render e não devem ser versionados no Git.
O banco PostgreSQL de produção precisa existir e possuir a estrutura do BiblioAvisa.

Depois de criar o serviço, gerar um **Deploy Hook** no Render e salvar a URL no
Secret `RENDER_DEPLOY_HOOK` do GitHub.

Serviços Render baseados em imagem não acompanham automaticamente uma mudança da
tag `latest`. O job `deploy-render` chama o Deploy Hook após a publicação, fazendo
o Render baixar a imagem atualizada e recriar o serviço.

## Segurança

O `.dockerignore` exclui, entre outros:

- `.env` e arquivos locais de ambiente;
- `.venv`;
- `node_modules`;
- sessão `whatsapp_service/auth_info`;
- arquivos temporários e logs.

Credenciais de produção ficam somente em Secrets/variáveis do provedor.

## Como testar localmente o Docker

Na raiz do projeto:

```bash
docker build -t biblioavisa:local .
docker run --rm -p 8000:8000 biblioavisa:local
```

Depois abrir:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/api/health
```

As páginas React são servidas pelo mesmo container. Funcionalidades que acessam
o PostgreSQL exigem que as variáveis `DB_*` sejam fornecidas ao container.

## Dificuldades encontradas durante a implementação

A primeira execução real da PR do CI falhou ainda na configuração do Node. O
workflow havia sido escrito supondo a existência de `frontend/package-lock.json`
e tentou habilitar cache do npm usando esse caminho. Como o lockfile não estava
versionado, o `setup-node` interrompeu o job. A correção foi remover o cache baseado
em lockfile e usar `npm install`, mantendo o pipeline compatível com a estrutura real.

Na execução seguinte, o novo teste unitário encontrou outro problema: o arquivo
`validation.js` importava `./masks` sem a extensão `.js`. O Vite resolvia esse caminho,
mas o runner nativo do Node em modo ESM não. O import foi alterado para `./masks.js`,
ficando compatível tanto com o Vite quanto com o Node.

Após essas correções, os jobs `testar` e `construir-imagem` concluíram com sucesso,
incluindo testes JavaScript, build React, Python, PostgreSQL 17 e build Docker.

## Regra de promoção para produção

```text
código -> PR -> testar -> construir-imagem -> merge -> publicar -> deploy
```

Nenhuma etapa de publicação deve executar antes dos testes. Em caso de falha, a
imagem nova não é enviada e o Render permanece executando a versão anterior.
