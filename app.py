from flask import Flask
from flask_migrate import Migrate
from models import db, Produto
from routes import register_routes  # Importando a função que vai registrar as rotas


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializando o banco de dados
db.init_app(app)
migrate = Migrate(app, db)

# Registrando as rotas
register_routes(app)

@app.route('/')
def home():
    return "Bem-vindo à página inicial do Sistema de Estoque!"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria o banco de dados nas primeiras execuções
    app.run(debug=True)
