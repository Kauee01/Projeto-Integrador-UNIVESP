from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Categoria(db.Model):
    __tablename__ = 'categoria'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    tipos_produto = db.relationship('TipoProduto', backref='categoria', lazy=True)

    def __repr__(self):
        return f"<Categoria {self.nome}>"

class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    tipo_produto_id = db.Column(db.Integer, db.ForeignKey('tipo_produto.id'), nullable=False)
    tipo_produto = db.relationship('TipoProduto', backref=db.backref('produtos_tipo', lazy=True))  # Renomeando o backref
    
    # Adicionando a coluna quantidade
    quantidade = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<Produto {self.id} - {self.tipo_produto.nome}>'



class TipoProduto(db.Model):
    __tablename__ = 'tipo_produto'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False, unique=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    descricao = db.Column(db.Text)

    produtos = db.relationship('Produto', back_populates='tipo_produto', cascade="all, delete-orphan")





class TipoPagamento(db.Model):
    __tablename__ = 'tipo_pagamento'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False, unique=True)

    vendas = db.relationship('Venda', backref='tipo_pagamento', lazy=True)

    def __repr__(self):
        return f"<TipoPagamento {self.nome}>"

class Venda(db.Model):
    __tablename__ = 'venda'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    tipo_pagamento_id = db.Column(db.Integer, db.ForeignKey('tipo_pagamento.id'), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2))

    itens = db.relationship('ItemVenda', backref='venda', lazy=True)

    def __repr__(self):
        return f"<Venda {self.id} em {self.data}>"

class ItemVenda(db.Model):
    __tablename__ = 'item_venda'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id'), nullable=False)
    tipo_produto_id = db.Column(db.Integer, db.ForeignKey('tipo_produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_produtos = db.Column(db.Numeric(10, 2))

    tipo_produto = db.relationship('TipoProduto', backref='itens_venda', lazy=True)

    def __repr__(self):
        return f"<ItemVenda {self.quantidade}x tipo_produto {self.tipo_produto_id}>"