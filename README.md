SenhaFacil 🎟️
Um sistema de gerenciamento de filas de atendimento em tempo real, desenvolvido com Django e Channels. O objetivo é modernizar e otimizar a experiência de espera em ambientes como clínicas e laboratórios, permitindo que pacientes acompanhem sua posição na fila através de seus próprios dispositivos.

✨ Funcionalidades
Emissão de Senhas: Pacientes podem gerar senhas para diferentes tipos de atendimento (ex: Normal, Prioritário).

Acompanhamento em Tempo Real: A tela do paciente se conecta via WebSocket e é atualizada instantaneamente quando sua senha é chamada.

Painel do Atendente: Uma interface segura para atendentes visualizarem as filas de espera e chamarem o próximo paciente.

Diferenciação Visual: Interfaces que utilizam cores e badges para diferenciar tipos de atendimento e status.

Administração via Django Admin: Gerenciamento de tipos de filas diretamente pelo painel de administrador.

🛠️ Tecnologias Utilizadas
Backend: Python, Django

Tempo Real: Django Channels, Daphne (ASGI Server)

Banco de Dados: PostgreSQL

Frontend: HTML, Bootstrap 5, JavaScript

Versionamento: Git & GitHub

🚀 Instalação e Configuração
Siga os passos abaixo para configurar o ambiente de desenvolvimento local.

Pré-requisitos
Python 3.11+

Git

PostgreSQL

Passo a Passo
Clone o repositório:

Bash

git clone https://github.com/pabloaugussto/sistemadefila.git
cd sistemadefila
Crie e ative o ambiente virtual:

Bash

# Criar o ambiente
python -m venv venv

# Ativar no Windows
venv\Scripts\activate
Instale as dependências:

Bash

pip install -r requirements.txt
Configure o Banco de Dados:

Certifique-se de que o PostgreSQL está rodando.

Crie um novo banco de dados para o projeto. Ex: minhasenha_db.

Configure as Variáveis de Ambiente:

Renomeie o arquivo .env.example para .env.

Abra o arquivo .env e preencha com suas credenciais do PostgreSQL.

Snippet de código

SECRET_KEY='coloque_uma_chave_secreta_aqui'
DEBUG=True
DB_NAME='minhasenha_db'
DB_USER='seu_usuario_postgres'
DB_PASSWORD='sua_senha_postgres'
DB_HOST='localhost'
DB_PORT='5432'
Aplique as migrações:

Bash

python manage.py migrate
Crie um superusuário para acessar o painel de admin:

Bash

python manage.py createsuperuser
▶️ Como Executar o Projeto
Após a configuração, você pode iniciar o servidor.

Opção 1 (Recomendada - Script run.bat)
Na pasta raiz do projeto, execute o script que criamos:

Bash

run.bat
Ele irá ativar o ambiente virtual e iniciar o servidor Daphne automaticamente.

Opção 2 (Manual - Daphne)
Se preferir, execute os comandos manualmente:

Bash

# 1. Ative o ambiente virtual
venv\Scripts\activate

# 2. Inicie o servidor Daphne
daphne -p 8000 minhasenha.asgi:application
Após iniciar o servidor, a aplicação estará disponível em http://127.0.0.1:8000/.

📈 Próximos Passos
[ ] Implementar sistema de cadastro e login para pacientes (com CPF).

[ ] Criar um painel público (modo TV) para exibir as senhas chamadas.

[ ] Desenvolver a funcionalidade de "Finalizar Atendimento" no painel do atendente.

[ ] Criar um dashboard administrativo com relatórios (tempo médio de espera, etc.).

✒️ Autor
Pablo Augusto - GitHub