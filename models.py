from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    quantidade = db.Column(db.Integer, default=0)
    preco = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Produto {self.nome}>"

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_total = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, nullable=True)

    produto = db.relationship('Produto', backref='vendas')

    def __repr__(self):
        return f"<Venda {self.quantidade}x {self.produto.nome} em {self.data}>"
