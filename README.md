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
**Diferencial de automação:** o sistema não apenas realiza notificações programadas. Ele analisa automaticamente os dados dos empréstimos e o histórico de devoluções dos usuários para
identificar situações de risco de atraso. A partir dessa análise, determina o momento adequado para enviar lembretes personalizados através da API do WhatsApp.
Além disso, o usuário pode interagir com o sistema pelo próprio WhatsApp para consultar ou renovar seus empréstimos. 

---
Tecnologias e Ferramentas Que Serão Utilizadas
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
git clone https://github.com/trabalho-do-brunao/Trabalho-biblioteca.git
cd Trabalho-biblioteca
```


## Lista de Tarefas do Projeto

### 1. Configuração do ambiente
- [ ] Criar repositório no GitHub
- [ ] Configurar ambiente virtual Python (venv)
- [ ] Criar requirements.txt com as bibliotecas do projeto
- [ ] Criar arquivo .env.example com as variáveis necessárias (sem valores reais)

### 2. Banco de dados (PostgreSQL)
- [ ] Modelar as tabelas: livros, usuarios, emprestimos, notificacoes
- [ ] Escrever o script schema.sql de criação das tabelas
- [ ] Popular o banco com dados de teste (mock de livros/usuários/empréstimos)

### 3. Conexão Python ↔ PostgreSQL
- [ ] Criar módulo db.py com a conexão (psycopg2 ou SQLAlchemy)
- [ ] Função para buscar todos os empréstimos ativos
- [ ] Função para atualizar status de um empréstimo (ex: renovado)

### 4. Lógica de verificação de prazos
- [ ] Função que compara data atual com data de devolução
- [ ] Classificar cada empréstimo: "em dia", "próximo do vencimento", "atrasado"
- [ ] Montar a lista de empréstimos que precisam de notificação

### 5. Integração com WhatsApp
- [ ] Criar conta/sandbox na WhatsApp Business API (ou Twilio)
- [ ] Criar módulo whatsapp.py para envio de mensagens
- [ ] Criar templates de mensagem (lembrete e alerta de atraso)
- [ ] Implementar recebimento de respostas (webhook) para comandos como "renovar"
- [ ] Registrar cada envio na tabela notificacoes (log)

### 6. Geração de relatório
- [ ] Criar módulo relatorio.py com ReportLab ou FPDF
- [ ] Gerar PDF com resumo das notificações enviadas no dia

### 7. Envio de e-mail
- [ ] Criar módulo email_service.py (smtplib ou biblioteca similar)
- [ ] Enviar o PDF gerado como anexo ao responsável da biblioteca

### 8. Agendamento automático
- [ ] Configurar APScheduler (ou cron) para rodar a verificação diariamente
- [ ] Criar main.py que orquestra todo o fluxo (conectar → verificar → notificar → relatório → e-mail)

### 9. Testes
- [ ] Testar conexão com o banco
- [ ] Testar envio de mensagem via WhatsApp (ambiente sandbox)
- [ ] Testar geração e envio do relatório
- [ ] Testar o fluxo completo de ponta a ponta

### 10. Documentação e entrega
- [ ] Atualizar o README conforme o código avança
- [ ] Comentar o código
- [ ] Criar prints/GIF do sistema funcionando (se pedido na entrega)
- [ ] Revisar se o fluxo do código bate com o fluxograma da Entrega 1
