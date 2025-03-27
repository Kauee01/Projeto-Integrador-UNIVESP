from flask import request, jsonify
from models import db, Produto, Venda
from datetime import datetime
import pytz


def register_routes(app):
    @app.route('/produtos', methods=['GET'])
    def get_produtos():
        produtos = Produto.query.all()
        return jsonify([{'id': p.id, 'nome': p.nome, 'quantidade': p.quantidade, 'preco': p.preco} for p in produtos])

    @app.route('/produto/<int:id>', methods=['GET'])
    def get_produto(id):
        produto = Produto.query.get(id)
        if not produto:
            return jsonify({'erro': 'Produto nao encontrado'}), 404
        return jsonify({'id': produto.id, 'nome': produto.nome, 'quantidade': produto.quantidade, 'preco': produto.preco})

    @app.route('/produto', methods=['POST'])
    def add_produto():
        data = request.json
        novo_produto = Produto(nome=data['nome'], descricao=data.get('descricao', ''), quantidade=data['quantidade'], preco=data['preco'])
        db.session.add(novo_produto)
        db.session.commit()
        return jsonify({'message': 'Produto adicionado'}), 201

    @app.route('/produto/<int:id>', methods=['PUT'])
    def update_produto(id):
        produto = Produto.query.get(id)
        if not produto:
            return jsonify({'erro': 'Produto não encontrado'}), 404
        data = request.json
        produto.nome = data.get('nome', produto.nome)
        produto.quantidade = data.get('quantidade', produto.quantidade)
        produto.preco = data.get('preco', produto.preco)
        db.session.commit()
        return jsonify({'mensagem': 'Produto atualizado'})

    @app.route('/produto/<int:id>', methods=['DELETE'])
    def delete_produto(id):
        produto = Produto.query.get(id)
        if not produto:
            return jsonify({'erro': 'Produto não encontrado'}), 404
        db.session.delete(produto)
        db.session.commit()
        return jsonify({'mensagem': 'Produto deletado'})

    @app.route('/vender_produto', methods=['POST'])
    def vender_produto():
        data = request.json
        produto_id = data.get('produto_id')  # Obtém o ID do produto do corpo da requisição
        quantidade_vendida = data.get('quantidade', 1)  # Quantidade padrão 1
    
        if not produto_id:
            return jsonify({'erro': 'É necessário fornecer o produto_id'}), 400
    
        produto = Produto.query.get(produto_id)
    
        if produto and produto.quantidade >= quantidade_vendida:
            produto.quantidade -= quantidade_vendida  # Atualiza estoque
            preco_total = produto.preco * quantidade_vendida  # Calcula o preço total de venda
    
            brasil_tz = pytz.timezone('America/Sao_Paulo')
            data_local = datetime.now(brasil_tz)  # Data atual com fuso horário de São Paulo
            
            nova_venda = Venda(produto_id=produto_id, quantidade=quantidade_vendida, preco_total=preco_total, data=data_local)  # Registra a venda com a data com o fuso horário local
            db.session.commit()
    
            return jsonify({'message': 'Venda registrada com sucesso'}), 200
        else:
            return jsonify({'message': 'Produto não encontrado ou estoque insuficiente'}), 400
