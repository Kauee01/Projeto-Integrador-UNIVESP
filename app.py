"""
app.py — Ponto de entrada da aplicação Flask.

Responsável por:
- Criar a instância principal do Flask
- Configurar o banco de dados SQLite via SQLAlchemy
- Inicializar o sistema de migrações (Flask-Migrate)
- Registrar todas as rotas definidas em routes.py
- Expor o endpoint de health check (/health)
"""

from flask import Flask, jsonify
from flask_migrate import Migrate
from models import db
from routes import register_routes

# --- Criação da instância Flask ---
app = Flask(__name__)

# Chave secreta usada para assinar cookies de sessão (session)
app.secret_key = 'Univesp2025'

# --- Configuração do banco de dados SQLite ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# Desativa tracking de modificações (economia de memória)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Inicialização do banco e migrações ---
db.init_app(app)
migrate = Migrate(app, db)

# --- Registro de todas as rotas da aplicação ---
register_routes(app)


# --- Endpoint de health check (verificação de saúde da API) ---
@app.get("/health")
def health():
    """Retorna status 200 para confirmar que a aplicação está rodando."""
    return jsonify({"status": "ok"}), 200


# --- Inicialização do servidor de desenvolvimento ---
if __name__ == '__main__':
    app.run(debug=True)
