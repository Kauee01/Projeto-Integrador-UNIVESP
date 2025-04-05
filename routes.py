from flask import request, jsonify, render_template
from models import db, TipoProduto, Produto, Venda, ItemVenda, TipoPagamento, Categoria
from datetime import datetime
import pytz
from sqlalchemy import func

def register_routes(app):
    # ---------- PRODUTO ----------  
    @app.route('/produtos', methods=['POST'])
    def adicionar_produto():
        data = request.get_json()
        tipo_produto_id = data.get('tipo_produto_id')
        quantidade = data.get('quantidade', 1)  # Agora também aceitamos a quantidade

        if not tipo_produto_id:
            return jsonify({'erro': 'tipo_produto_id é obrigatório'}), 400

        novo_produto = Produto(tipo_produto_id=tipo_produto_id, quantidade=quantidade)
        db.session.add(novo_produto)
        db.session.commit()

        return jsonify({'mensagem': 'Produto criado com sucesso', 'id': novo_produto.id}), 201

    @app.route('/produtos', methods=['GET'])
    def listar_produtos():
        produtos = Produto.query.all()
        return jsonify([{
            'id': p.id,
            'tipo_produto_id': p.tipo_produto.id,
            'nome_tipo_produto': p.tipo_produto.nome,
            'preco': str(p.tipo_produto.preco),
            'quantidade': p.quantidade  # Exibe a quantidade também
        } for p in produtos])

    # ---------- VENDA ----------
    @app.route('/vendas', methods=['POST'])
    def registrar_venda():
        data = request.get_json()
        tipo_pagamento_id = data.get('tipo_pagamento_id')
        itens = data.get('itens')  # Lista de dicts: [{'tipo_produto_id': 1, 'quantidade': 2}, ...]

        if not tipo_pagamento_id or not itens:
            return jsonify({'erro': 'tipo_pagamento_id e itens são obrigatórios'}), 400

        brasil_tz = pytz.timezone('America/Sao_Paulo')
        data_venda = datetime.now(brasil_tz)

        nova_venda = Venda(tipo_pagamento_id=tipo_pagamento_id, data=data_venda)
        db.session.add(nova_venda)
        db.session.flush()  # Garante nova_venda.id disponível antes de adicionar ItemVenda

        valor_total = 0

        for item in itens:
            tipo_produto_id = item.get('tipo_produto_id')
            quantidade = item.get('quantidade', 1)

            tipo = TipoProduto.query.get(tipo_produto_id)
            if not tipo:
                continue

            valor_produtos = float(tipo.preco) * quantidade
            valor_total += valor_produtos

            item_venda = ItemVenda(
                venda_id=nova_venda.id,
                tipo_produto_id=tipo_produto_id,
                quantidade=quantidade,
                valor_produtos=valor_produtos
            )
            db.session.add(item_venda)

            # Atualizando a quantidade de produtos no estoque
            produto = Produto.query.filter_by(tipo_produto_id=tipo_produto_id).first()
            if produto:
                produto.quantidade -= quantidade
                db.session.commit()

        nova_venda.valor_total = valor_total
        db.session.commit()

        return jsonify({
            'mensagem': 'Venda registrada com sucesso',
            'venda_id': nova_venda.id,
            'valor_total': str(valor_total)
        }), 201

    # ---------- LISTAR VENDAS ----------------------------------
    @app.route('/vendas', methods=['GET'])
    def listar_vendas():
        vendas = Venda.query.all()
        return jsonify([{
            'id': v.id,
            'data': v.data.isoformat(),
            'tipo_pagamento': v.tipo_pagamento.nome,
            'valor_total': str(v.valor_total),
            'itens': [{
                'tipo_produto': i.tipo_produto.nome,
                'quantidade': i.quantidade,
                'valor': str(i.valor_produtos)
            } for i in v.itens]
        } for v in vendas])

    # ---------- CATEGORIA ---------------------
    @app.route('/categorias', methods=['POST'])
    def criar_categorias():
        data = request.get_json()

        # Se for um dicionário, transformamos em lista com um item
        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            return jsonify({'erro': 'Formato inválido. Esperado objeto ou lista de objetos.'}), 400

        categorias_criadas = []
        erros = []

        for item in data:
            nome = item.get('nome')
            descricao = item.get('descricao', '')

            if not nome:
                erros.append({'erro': 'Nome da categoria é obrigatório', 'categoria': item})
                continue

            if Categoria.query.filter_by(nome=nome).first():
                erros.append({'erro': f'Categoria "{nome}" já existe', 'categoria': item})
                continue

            nova_categoria = Categoria(nome=nome, descricao=descricao)
            db.session.add(nova_categoria)
            categorias_criadas.append(nova_categoria)

        db.session.commit()

        return jsonify({
            'mensagem': f'{len(categorias_criadas)} categoria(s) criada(s) com sucesso',
            'categorias': [{'id': c.id, 'nome': c.nome} for c in categorias_criadas],
            'erros': erros
        }), 201

    # ---------- TIPO PAGAMENTO ---------------------
    @app.route('/tipopagamento', methods=['POST'])
    def criar_tipo_pagamento():
        data = request.get_json()

        # Se for um dicionário, transformamos em lista com um item
        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            return jsonify({'erro': 'Formato inválido. Esperado objeto ou lista de objetos.'}), 400

        tipos_pagamento_criados = []
        erros = []

        for item in data:
            nome = item.get('nome')

            if not nome:
                erros.append({'erro': 'Nome do tipo de pagamento é obrigatório', 'tipo_pagamento': item})
                continue

            # Verifica se o nome já existe
            if TipoPagamento.query.filter_by(nome=nome).first():
                erros.append({'erro': f'Tipo de pagamento "{nome}" já existe', 'tipo_pagamento': item})
                continue

            novo_tipo_pagamento = TipoPagamento(nome=nome)
            db.session.add(novo_tipo_pagamento)
            tipos_pagamento_criados.append(novo_tipo_pagamento)

        db.session.commit()

        return jsonify({
            'mensagem': f'{len(tipos_pagamento_criados)} tipo(s) de pagamento criado(s) com sucesso',
            'tipos_pagamento': [{'id': t.id, 'nome': t.nome} for t in tipos_pagamento_criados],
            'erros': erros
        }), 201

    # ---------------------------------- PAINEL FRONT END -----------------------------------------
    @app.route('/painel')
    def painel():
        tipos = TipoProduto.query.all()

        dados_estoque = []
        for tipo in tipos:
            # Recalcule a quantidade de estoque com os dados mais recentes
            qtd_estoque = db.session.query(func.sum(Produto.quantidade)).filter_by(tipo_produto_id=tipo.id).scalar() or 0
            qtd_vendida = sum(item.quantidade for item in tipo.itens_venda)
            dados_estoque.append({
                'tipo': tipo.nome,
                'estoque': qtd_estoque,
                'vendido': qtd_vendida,
                'preco': float(tipo.preco)
            })

        return render_template('painel.html', produtos=dados_estoque)

    @app.route('/tipoproduto', methods=['POST'])
    def criar_tipo_produto():
        data = request.get_json()

        if not isinstance(data, list):
            return jsonify({'erro': 'Formato de requisição inválido. Esperado uma lista de produtos.'}), 400

        for produto in data:
            nome = produto.get('nome')
            categoria_id = produto.get('categoria_id')
            preco = produto.get('preco')
            descricao = produto.get('descricao', '')

            if not nome or not categoria_id or not preco:
                return jsonify({'erro': 'nome, categoria_id e preco são obrigatórios'}), 400

            # Verifica se nome já existe
            if TipoProduto.query.filter_by(nome=nome).first():
                return jsonify({'erro': f'Já existe um tipo de produto com o nome {nome}'}), 400

            tipo = TipoProduto(nome=nome, categoria_id=categoria_id, preco=preco, descricao=descricao)
            db.session.add(tipo)

        db.session.commit()

        return jsonify({'mensagem': 'Tipos de produto criados com sucesso'}), 201
