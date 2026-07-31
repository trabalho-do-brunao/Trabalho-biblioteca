Sistema de Gestão de Biblioteca com Integração via WhatsApp

Integrantes do Grupo:
Guilherme Granemann Benvenutti
Matheus Guerelus Rizelo
Matheus Henrique Predes Pereira
João Pedro Lagos Muraro

---
Resumo da Automação Proposta
Atualmente, o controle de empréstimos em muitas bibliotecas é feito de forma manual, o que dificulta o acompanhamento dos prazos de devolução e gera atrasos frequentes por parte dos usuários.
Este projeto propõe a automação desse processo por meio de um sistema que:
Conecta-se a um banco de dados PostgreSQL contendo o cadastro de livros, usuários e empréstimos;
Verifica diariamente, de forma automática, os empréstimos ativos e seus respectivos prazos de devolução;
Identifica empréstimos próximos do vencimento ou em atraso;
Envia lembretes e alertas automáticos via WhatsApp aos usuários;
Permite que o usuário interaja pelo WhatsApp (renovar empréstimo, consultar situação);
Gera relatórios em PDF com o resumo das notificações enviadas e envia por e-mail ao responsável pela biblioteca.
O objetivo é reduzir os atrasos na devolução, melhorar a comunicação com os usuários e diminuir o trabalho manual da equipe da biblioteca.
---

Tecnologias e Ferramentas Utilizadas
Python — linguagem principal da automação
PostgreSQL — banco de dados para armazenamento de livros, usuários e empréstimos
psycopg2 / SQLAlchemy — conexão do Python com o PostgreSQL
WhatsApp Business API (ou Twilio API for WhatsApp) — envio e recebimento de mensagens
Requests — comunicação com serviços via HTTP
APScheduler — agendamento da verificação diária de prazos
ReportLab / FPDF — geração de relatórios em PDF
Git / GitHub — versionamento e controle do código
Figma — prototipação da interface/fluxo de interação
---
Instruções de Instalação, Dependências e Execução
Pré-requisitos
Python 3.10+
PostgreSQL 14+ instalado e em execução
Conta configurada na WhatsApp Business API (ou Twilio, para testes)
Git instalado
1. Clonar o repositório
```
git clone https://github.com/<usuario-ou-organizacao>/<nome-do-repositorio>.git
cd <nome-do-repositorio>
```
2. Criar e ativar um ambiente virtual
```
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```
3. Instalar as dependências
```
pip install -r requirements.txt
```
4. Configurar as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=biblioteca
DB_USER=seu_usuario
DB_PASSWORD=sua_senha

WHATSAPP_API_URL=https://api.suaprovedora.com
WHATSAPP_API_TOKEN=seu_token_aqui

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app
```
5. Criar o banco de dados e as tabelas
```
psql -U seu_usuario -d postgres -f database/schema.sql
```
6. Executar o projeto
```
python main.py
```
