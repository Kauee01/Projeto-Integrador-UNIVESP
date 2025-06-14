from flask import Flask
from flask_migrate import Migrate
from models import db, Categoria, TipoProduto, Produto, TipoPagamento, Venda, ItemVenda
from routes import register_routes  # Importando a função que vai registrar as rotas
from flask_sqlalchemy import SQLAlchemy
from flask import render_template  # Importando a função que irá renderizar as páginas

# Criação da instância Flask
app = Flask(__name__)
app.secret_key = 'Univesp2025'

# Configurações do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializando o banco de dados
db.init_app(app)
migrate = Migrate(app, db)

# Registrando as rotas
register_routes(app)

# Iniciando a aplicação
if __name__ == '__main__':
    app.run(debug=True)
