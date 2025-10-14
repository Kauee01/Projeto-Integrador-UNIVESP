import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from models import (
    db, Categoria, TipoProduto, Produto,
    TipoPagamento, Venda, ItemVenda, Usuario
)

# ===== Helpers / "Factories" simples =====

def make_categoria(nome="Salgados", descricao="Itens salgados"):
    c = Categoria(nome=nome, descricao=descricao)
    db.session.add(c)
    db.session.flush()
    return c

def make_tipo_produto(nome="Coxinha", preco=Decimal("7.50"), categoria=None, descricao="frango"):
    if categoria is None:
        categoria = make_categoria()
    tp = TipoProduto(nome=nome, categoria_id=categoria.id, preco=preco, descricao=descricao)
    db.session.add(tp)
    db.session.flush()
    return tp

def make_produto(tipo_produto=None):
    if tipo_produto is None:
        tipo_produto = make_tipo_produto()
    p = Produto(tipo_produto_id=tipo_produto.id)
    db.session.add(p)
    db.session.flush()
    return p

def make_tipo_pagamento(nome="Dinheiro"):
    t = TipoPagamento(nome=nome)
    db.session.add(t)
    db.session.flush()
    return t

def make_venda(tipo_pagamento=None, valor_total=Decimal("0.00")):
    if tipo_pagamento is None:
        tipo_pagamento = make_tipo_pagamento()
    v = Venda(tipo_pagamento_id=tipo_pagamento.id, valor_total=valor_total)
    db.session.add(v)
    db.session.flush()
    return v

def make_item_venda(venda=None, tipo_produto=None, quantidade=1, valor_produtos=Decimal("0.00")):
    if venda is None:
        venda = make_venda()
    if tipo_produto is None:
        tipo_produto = make_tipo_produto()
    iv = ItemVenda(
        venda_id=venda.id,
        tipo_produto_id=tipo_produto.id,
        quantidade=quantidade,
        valor_produtos=valor_produtos
    )
    db.session.add(iv)
    db.session.flush()
    return iv

def make_usuario(username="admin", senha_plana="123456"):
    u = Usuario(username=username)
    u.set_senha(senha_plana)
    db.session.add(u)
    db.session.flush()
    return u


# ====== TESTES ======

def test_usuario_password_hash_ok(session):
    u = make_usuario(username="joao", senha_plana="segredo")
    assert u.senha != "segredo"  # não guarda a senha em texto puro
    assert u.check_senha("segredo") is True
    assert u.check_senha("errada") is False


def test_usuario_username_unico(session):
    make_usuario(username="duplicado", senha_plana="x")
    with pytest.raises(IntegrityError):
        make_usuario(username="duplicado", senha_plana="y")
        db.session.commit()  # força o flush/commit para levantar a exceção


def test_categoria_unique_nome(session):
    make_categoria(nome="Bebidas")
    with pytest.raises(IntegrityError):
        make_categoria(nome="Bebidas")
        db.session.commit()


def test_relacao_tipo_produto_categoria_e_produtos(session):
    cat = make_categoria(nome="Doces")
    tipo = make_tipo_produto(nome="Brigadeiro", preco=Decimal("4.00"), categoria=cat)

    # cria 3 produtos físicos do mesmo tipo
    p1 = make_produto(tipo)
    p2 = make_produto(tipo)
    p3 = make_produto(tipo)

    # back_populates funcionando:
    assert p1.tipo_produto.id == tipo.id
    assert len(tipo.produtos) == 3
    assert {p.id for p in tipo.produtos} == {p1.id, p2.id, p3.id}

    # backref categoria:
    assert tipo.categoria.id == cat.id
    assert repr(cat) == f"<Categoria {cat.nome}>"


def test_produto_requer_tipo_produto(session):
    # tipo_produto_id é NOT NULL -> deve falhar criar sem FK
    p = Produto()  # sem tipo_produto_id
    db.session.add(p)
    with pytest.raises(IntegrityError):
        db.session.commit()


def test_delete_cascade_delete_orphan_produtos(session):
    """
    'produtos' em TipoProduto tem cascade="all, delete-orphan".
    Deletar o TipoProduto deve deletar os Produtos filhos.
    """
    tipo = make_tipo_produto(nome="Quibe", preco=Decimal("6.00"))
    p1 = make_produto(tipo)
    p2 = make_produto(tipo)

    # sanity
    assert db.session.get(Produto, p1.id) is not None
    assert db.session.get(Produto, p2.id) is not None

    # Deleta o pai
    db.session.delete(tipo)
    db.session.commit()

    # Filhos foram removidos
    assert db.session.get(Produto, p1.id) is None
    assert db.session.get(Produto, p2.id) is None
    # E o tipo também
    assert db.session.get(TipoProduto, tipo.id) is None


def test_venda_itens_relacionamento(session):
    tp = make_tipo_pagamento("Pix")
    tipo = make_tipo_produto(nome="Empada", preco=Decimal("8.00"))

    venda = make_venda(tipo_pagamento=tp, valor_total=Decimal("16.00"))
    item = make_item_venda(
        venda=venda,
        tipo_produto=tipo,
        quantidade=2,
        valor_produtos=Decimal("16.00")
    )

    # backrefs e relações
    assert item.venda.id == venda.id
    assert item.tipo_produto.id == tipo.id
    assert venda.tipo_pagamento.id == tp.id
    assert item in venda.itens
    assert tipo in [i.tipo_produto for i in venda.itens]

    # __repr__ básicos
    assert "<Venda " in repr(venda)
    assert "<ItemVenda " in repr(item)
    assert f"<TipoPagamento {tp.nome}>" == repr(tp)


def test_repr_produto(session):
    tipo = make_tipo_produto(nome="Enroladinho", preco=Decimal("5.50"))
    p = make_produto(tipo)
    # __repr__ usa o nome do tipo
    assert f"<Produto {p.id} - {tipo.nome}>" == repr(p)
