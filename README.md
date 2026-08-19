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
