"""
models.py — Modelos do banco de dados (SQLAlchemy).

Define todas as tabelas do sistema:
- Categoria: categorias de produtos (ex: Bebidas, Lanches)
- TipoProduto: tipos/modelos de produto com nome, preço e categoria
- Produto: unidades individuais em estoque (cada registro = 1 unidade física)
- TipoPagamento: formas de pagamento aceitas (ex: Dinheiro, Pix)
- Venda: registro de cada venda realizada
- ItemVenda: itens de uma venda (produto, quantidade, valor unitário)
- Usuario: usuários do sistema com autenticação por hash de senha
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Instância global do SQLAlchemy (inicializada em app.py via db.init_app)
db = SQLAlchemy()


class Categoria(db.Model):
    """Categoria de produtos (ex: Bebidas, Lanches, Sobremesas)."""
    __tablename__ = 'categoria'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False, unique=True)
    descricao = db.Column(db.String(255))

    # Relacionamento: uma categoria possui vários tipos de produto
    tipos_produto = db.relationship(
        'TipoProduto', backref='categoria', lazy=True)

    def __repr__(self):
        return f"<Categoria {self.nome}>"


class TipoProduto(db.Model):
    """Tipo/modelo de produto com nome, preço e categoria."""
    __tablename__ = 'tipo_produto'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False, unique=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey(
        'categoria.id'), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    descricao = db.Column(db.Text)

    # Relacionamento: um tipo de produto possui várias unidades em estoque
    # cascade="all, delete-orphan" garante que ao excluir o tipo, as unidades são removidas
    produtos = db.relationship(
        'Produto', back_populates='tipo_produto', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TipoProduto {self.nome}>"


class Produto(db.Model):
    """Unidade individual de produto em estoque.
    Cada registro representa 1 unidade física. A quantidade em estoque
    é calculada contando os registros com o mesmo tipo_produto_id.
    """
    __tablename__ = 'produtos'

    id = db.Column(db.Integer, primary_key=True)
    tipo_produto_id = db.Column(db.Integer, db.ForeignKey(
        'tipo_produto.id'), nullable=False)

    # Relacionamento inverso com TipoProduto
    tipo_produto = db.relationship('TipoProduto', back_populates='produtos')

    def __repr__(self):
        return f'<Produto {self.id} - {self.tipo_produto.nome}>'


class TipoPagamento(db.Model):
    """Forma de pagamento aceita pelo sistema (ex: Dinheiro, Pix, Cartão)."""
    __tablename__ = 'tipo_pagamento'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False, unique=True)

    # Relacionamento: um tipo de pagamento pode estar em várias vendas
    vendas = db.relationship('Venda', backref='tipo_pagamento', lazy=True)

    def __repr__(self):
        return f"<TipoPagamento {self.nome}>"


class Venda(db.Model):
    """Registro de uma venda realizada."""
    __tablename__ = 'venda'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    tipo_pagamento_id = db.Column(db.Integer, db.ForeignKey(
        'tipo_pagamento.id'), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2))

    # Relacionamento: uma venda possui vários itens
    itens = db.relationship('ItemVenda', backref='venda', lazy=True)

    def __repr__(self):
        return f"<Venda {self.id} em {self.data}>"


class ItemVenda(db.Model):
    """Item individual de uma venda (produto vendido, quantidade e valor unitário)."""
    __tablename__ = 'item_venda'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('venda.id'), nullable=False)
    tipo_produto_id = db.Column(db.Integer, db.ForeignKey(
        'tipo_produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    # Valor unitário no momento da venda
    valor_produtos = db.Column(db.Numeric(10, 2))

    # Relacionamento: cada item aponta para o tipo de produto vendido
    tipo_produto = db.relationship(
        'TipoProduto', backref='itens_venda', lazy=True)

    def __repr__(self):
        return f"<ItemVenda {self.quantidade}x tipo_produto {self.tipo_produto_id}>"


class Usuario(db.Model):
    """Usuário do sistema com autenticação por senha hash (Werkzeug)."""
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    # Armazena hash, não a senha em texto
    senha = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Usuario {self.username}>"

    def set_senha(self, senha):
        """Gera e armazena o hash da senha usando Werkzeug."""
        self.senha = generate_password_hash(senha)

    def check_senha(self, senha):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.senha, senha)
