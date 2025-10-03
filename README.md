🎟️ SenhaFacil

SenhaFacil é um sistema de gerenciamento de filas de atendimento em tempo real, desenvolvido com Django e Channels.
O objetivo é modernizar e otimizar a experiência de espera em ambientes como clínicas e laboratórios, permitindo que pacientes acompanhem sua posição na fila diretamente de seus dispositivos.

✨ Funcionalidades

Emissão de Senhas: Pacientes podem gerar senhas para diferentes tipos de atendimento (ex: Normal, Prioritário).

Acompanhamento em Tempo Real: A tela do paciente se conecta via WebSocket e é atualizada instantaneamente quando sua senha é chamada.

Painel do Atendente: Interface segura para visualização das filas e chamada do próximo paciente.

Diferenciação Visual: Cores e badges para diferenciar tipos de atendimento e status.

Administração via Django Admin: Gerenciamento de filas e configurações diretamente pelo painel administrativo.

🛠️ Tecnologias Utilizadas

Backend: Python, Django

Tempo Real: Django Channels, Daphne (ASGI Server)

Banco de Dados: PostgreSQL

Frontend: HTML, Bootstrap 5, JavaScript

Versionamento: Git & GitHub

🚀 Instalação e Configuração

Siga os passos abaixo para configurar o ambiente de desenvolvimento local:

🔹 Pré-requisitos

Python 3.11+

Git

PostgreSQL

🔹 Passo a Passo

1. Clone o repositório 
git clone https://github.com/pabloaugussto/sistemadefila.git
cd sistemadefila
2. Crie e ative o ambiente virtual
# Criar o ambiente
python -m venv venv
# Ativar no Windows
venv\Scripts\activate
3. Instale as dependências
pip install -r requirements.txt

4. Configure o Banco de Dados

Certifique-se de que o PostgreSQL está em execução.

Crie um banco de dados, por exemplo: minhasenha_db.

5. Configure as variáveis de ambiente

Renomeie o arquivo .env.example para .env.

Preencha com suas credenciais:
SECRET_KEY='sua_chave_secreta_aqui'
DEBUG=True
DB_NAME='minhasenha_db'
DB_USER='seu_usuario_postgres'
DB_PASSWORD='sua_senha_postgres'
DB_HOST='localhost'
DB_PORT='5432'

6. Aplique as migrações
python manage.py migrate
7. Crie um superusuário (para acessar o admin)
python manage.py createsuperuser

Como Executar o Projeto
🔹 Opção 1 (Recomendada - Script run.bat)
# Ativar ambiente virtual
venv\Scripts\activate

# Iniciar servidor
daphne -p 8000 minhasenha.asgi:application

✒️ Autor

Pablo Augusto
🔗 GitHub
