from flask import request, jsonify, render_template, redirect, session, url_for, flash
from models import db, TipoProduto, Produto, Venda, ItemVenda, TipoPagamento, Categoria, Usuario
from datetime import datetime
from sqlalchemy import func

def register_routes(app):
    @app.route('/excluir-produto/<int:produto_id>', methods=['POST'])
    def excluir_produto(produto_id):
        if 'usuario' not in session:
            return redirect(url_for('login_view'))
        produto = Produto.query.get_or_404(produto_id)
        # Verifica se o produto está relacionado a vendas
        if ItemVenda.query.filter_by(tipo_produto_id=produto.tipo_produto_id).first():
            return "Este produto está relacionado a vendas e não pode ser excluído.", 400
        db.session.delete(produto)
        db.session.commit()
        print(f"Produto com id {produto_id} excluído do banco de dados.")  # Verificação de exclusão
        return redirect(url_for('painel'))

    @app.route('/excluir-tipopagamento/<int:tipo_id>', methods=['POST'])
    def excluir_tipo_pagamento(tipo_id):
        if 'usuario' not in session:
            return redirect(url_for('login_view'))
        tipo = TipoPagamento.query.get_or_404(tipo_id)
        if Venda.query.filter_by(tipo_pagamento_id=tipo.id).first():
            return "Este tipo de pagamento já foi usado em uma venda e não pode ser excluído.", 400
        db.session.delete(tipo)
        db.session.commit()
        return redirect(url_for('cadastrar_pagamento'))

    @app.route('/editar-tipo-produto/<int:tipo_produto_id>', methods=['GET', 'POST'])
    def editar_tipo_produto(tipo_produto_id):
        if 'usuario' not in session:
            return redirect(url_for('login_view'))
        
        tipo_produto = TipoProduto.query.get_or_404(tipo_produto_id)
        tipos = TipoProduto.query.all()
        
        if request.method == 'POST':
            novo_nome = request.form.get('nome')
            novo_preco = request.form.get('preco')
            senha = request.form.get('senha')
            
            usuario = Usuario.query.filter_by(username=session['usuario']).first()
            if not usuario.check_senha(senha):
                return render_template('editar_produto.html', tipo_produto=tipo_produto, tipos=tipos, erro="Senha incorreta.")
            
            if novo_nome:
                tipo_produto.nome = novo_nome
            
            if novo_preco:
                try:
                    novo_preco = float(novo_preco)
                    if novo_preco <= 0:
                        raise ValueError("Preço inválido")
                    tipo_produto.preco = novo_preco
                except (ValueError, TypeError):
                    return render_template('editar_produto.html', tipo_produto=tipo_produto, tipos=tipos, erro="Preço inválido.")
            
            db.session.commit()
            return redirect(url_for('painel'))
        
        return render_template('editar_produto.html', tipo_produto=tipo_produto, tipos=tipos)

    @app.route('/')
    def login_view():
        return render_template('login.html')

    @app.route('/auth', methods=['POST'])
    def autenticar():
        usuario = request.form['username']
        senha = request.form['senha']
        usuario_obj = Usuario.query.filter_by(username=usuario).first()
        if usuario_obj and usuario_obj.check_senha(senha):
            session['usuario'] = usuario
            return redirect(url_for('home'))
        else:
            return render_template('login.html', erro="Usuário ou senha inválidos")

    @app.route('/cadastrar-usuario', methods=['GET', 'POST'])
    def cadastrar_usuario():
        if request.method == 'POST':
            usuario = request.form['username']
            senha = request.form['senha']

            # Verificar se o usuário já existe
            usuario_existente = Usuario.query.filter_by(username=usuario).first()
            if usuario_existente:
                return render_template('cadastro.html', erro="Usuário já existe!")

            # Criar novo usuário
            novo_usuario = Usuario(username=usuario)
            novo_usuario.set_senha(senha)

            # Adicionar e salvar no banco de dados
            db.session.add(novo_usuario)
            db.session.commit()

            return render_template('cadastro.html', sucesso="Conta criada com sucesso! Faça login.")

        return render_template('cadastro.html')

    @app.route('/logout')
    def logout():
        session.pop('usuario', None)
        return redirect(url_for('login_view'))

    @app.route('/home')
    def home():
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        # Calcula o total de produtos em estoque
        total_estoque = db.session.query(func.count(Produto.id)).scalar() or 0

        # Calcula o total de produtos vendidos
        total_vendido = db.session.query(func.sum(ItemVenda.quantidade)).scalar() or 0

        # Calcula o valor total das vendas
        valor_total = db.session.query(func.sum(Venda.valor_total)).scalar() or 0.00

        return render_template(
            'home.html',
            usuario=session['usuario'],
            total_estoque=int(total_estoque),
            total_vendido=int(total_vendido),
            valor_total=f"{valor_total:.2f}"
        )

    @app.route('/cadastrar-produto', methods=['GET', 'POST'])
    def exibir_form_produto():
        if 'usuario' not in session:
            return redirect(url_for('login_view'))
        categorias = Categoria.query.all()
        if request.method == 'POST':
            nome = request.form['nome']
            descricao = request.form.get('descricao', '')
            preco = request.form['preco']
            categoria_id = request.form['categoria_id']
            quantidade = int(request.form['quantidade'])

            # Validação dos campos obrigatórios
            if not nome or not preco or not categoria_id or quantidade <= 0:
                return render_template('cadastrar_produto.html', erro="Todos os campos obrigatórios devem ser preenchidos", categorias=categorias)

            # Cria o TipoProduto
            tipo = TipoProduto(nome=nome, descricao=descricao, preco=preco, categoria_id=categoria_id)
            db.session.add(tipo)
            db.session.commit()

            # Cria múltiplos registros de Produto para representar a quantidade
            for _ in range(quantidade):
                produto = Produto(tipo_produto_id=tipo.id)
                db.session.add(produto)

            db.session.commit()
            return redirect(url_for('painel'))

        return render_template('cadastrar_produto.html', categorias=categorias)

    @app.route('/registrar-venda', methods=['GET', 'POST'])
    def registrar_venda():
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        tipos_produto = TipoProduto.query.all()
        tipos_pagamento = TipoPagamento.query.all()

        total_geral = 0.0
        dados_produtos = []
        for tipo in tipos_produto:
            quantidade_estoque = db.session.query(func.count(Produto.id)).filter_by(tipo_produto_id=tipo.id).scalar() or 0
            dados_produtos.append({
                'id': tipo.id,
                'nome': tipo.nome,
                'preco': tipo.preco,
                'quantidade': quantidade_estoque
            })

        if request.method == 'POST':
            try:
                dados = request.get_json()
            except Exception as e:
                return jsonify({'error': f'Erro ao processar os dados. {str(e)}'}), 400

            tipo_pagamento_id = dados.get('tipo_pagamento_id')
            itens_venda = dados.get('itens', [])

            if not tipo_pagamento_id or not itens_venda:
                return jsonify({'error': 'Por favor, preencha todos os campos.'}), 400

            try:
                tipo_pagamento_id = int(tipo_pagamento_id)
            except ValueError:
                return jsonify({'error': 'Erro ao processar os dados. Certifique-se de que os valores estão corretos.'}), 400

            total_geral = 0
            try:
                nova_venda = Venda(tipo_pagamento_id=tipo_pagamento_id, data=datetime.now(), valor_total=0)
                db.session.add(nova_venda)
                db.session.commit()

                for item in itens_venda:
                    produto = TipoProduto.query.get(item['produto_id'])
                    if not produto:
                        return jsonify({'error': f'Produto não encontrado.'}), 404

                    quantidade_estoque = db.session.query(func.count(Produto.id)).filter_by(tipo_produto_id=produto.id).scalar() or 0
                    if item['quantidade'] > quantidade_estoque:
                        return jsonify({'error': f'Estoque insuficiente para o produto {produto.nome}. Estoque disponível: {quantidade_estoque}.'}), 400

                    total_produto = produto.preco * item['quantidade']
                    total_geral += total_produto

                    item_venda = ItemVenda(
                        venda_id=nova_venda.id,
                        tipo_produto_id=produto.id,
                        quantidade=item['quantidade'],
                        valor_produtos=produto.preco
                    )
                    db.session.add(item_venda)

                    produtos = Produto.query.filter_by(tipo_produto_id=produto.id).limit(item['quantidade']).all()
                    for produto_remover in produtos:
                        db.session.delete(produto_remover)

                nova_venda.valor_total = total_geral
                db.session.commit()

                return jsonify({'success': True}), 200

            except Exception as e:
                db.session.rollback()
                return jsonify({'error': f'Erro ao registrar a venda: {str(e)}'}), 500

        return render_template(
            'registrar_venda.html',
            produtos=dados_produtos,
            pagamentos=tipos_pagamento,
            total_geral=total_geral
        )

    @app.route('/cadastrar-pagamento', methods=['GET', 'POST'])
    def cadastrar_pagamento():
        if 'usuario' not in session:
            return redirect(url_for('login_view'))
        tipos_pagamento = TipoPagamento.query.all()
        if request.method == 'POST':
            nome = request.form['nome']
            if not nome:
                return render_template('cadastrar_pagamento.html', erro="Nome obrigatório", tipos_pagamento=tipos_pagamento)
            if TipoPagamento.query.filter_by(nome=nome).first():
                return render_template('cadastrar_pagamento.html', erro="Tipo já existe", tipos_pagamento=tipos_pagamento)
            tipo = TipoPagamento(nome=nome)
            db.session.add(tipo)
            db.session.commit()
            tipos_pagamento = TipoPagamento.query.all()
            return render_template('cadastrar_pagamento.html', sucesso="Tipo de pagamento cadastrado com sucesso!", tipos_pagamento=tipos_pagamento)
        return render_template('cadastrar_pagamento.html', tipos_pagamento=tipos_pagamento)

    @app.route('/listar-vendas')
    def listar_vendas():
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        # Carrega as vendas com todos os itens e seus detalhes
        vendas = Venda.query.order_by(Venda.data.desc()).all()  # Ordenando por data
        
        return render_template('listar_vendas.html', vendas=vendas)

    @app.route('/inventario-estoque', methods=['GET', 'POST'])
    def inventario_estoque():
        if 'usuario' not in session:
            return redirect(url_for('login_view'))
        
        produtos = TipoProduto.query.all()
        produtos_estoque = Produto.query.all()
        
        if request.method == 'POST':
            sucesso = None
            erro = None
            mensagem = None
            
            produto_id_adicionar = request.form.get('produto_id_adicionar')
            quantidade_adicionar = request.form.get('quantidade_adicionar')
            produto_id_remover = request.form.get('produto_id_remover')
            quantidade_remover = request.form.get('quantidade_remover')
            
            # Adicionar ao Estoque
            if produto_id_adicionar and quantidade_adicionar:
                try:
                    quantidade_adicionar = int(quantidade_adicionar)
                    if quantidade_adicionar < 1:
                        erro = "A quantidade a adicionar deve ser maior que zero!"
                    else:
                        for _ in range(quantidade_adicionar):
                            novo_produto = Produto(tipo_produto_id=produto_id_adicionar)
                            db.session.add(novo_produto)
                        db.session.commit()
                        sucesso = f"{quantidade_adicionar} unidade(s) adicionada(s) ao estoque!"
                        mensagem = f"{quantidade_adicionar} unidade(s) do produto foi(m) adicionada(s) ao estoque."
                except Exception as e:
                    db.session.rollback()
                    erro = f"Ocorreu um erro ao adicionar: {str(e)}"
            
            # Remover do Estoque
            elif produto_id_remover and quantidade_remover:
                try:
                    quantidade_remover = int(quantidade_remover)
                    if quantidade_remover < 1:
                        erro = "A quantidade a remover deve ser maior que zero!"
                        return render_template('inventario_estoque.html', produtos=produtos, sucesso=sucesso, erro=erro, produtos_estoque=produtos_estoque)
                    
                    produtos_para_remover = Produto.query.filter_by(tipo_produto_id=produto_id_remover).limit(quantidade_remover).all()
                    if len(produtos_para_remover) < quantidade_remover:
                        erro = "Não há quantidade suficiente para remover do estoque!"
                    else:
                        for produto in produtos_para_remover:
                            db.session.delete(produto)
                        db.session.commit()
                        sucesso = f"{quantidade_remover} unidade(s) removida(s) do estoque!"
                        mensagem = f"{quantidade_remover} unidade(s) do produto foi(m) removida(s) do estoque."
                except Exception as e:
                    db.session.rollback()
                    erro = f"Ocorreu um erro ao remover: {str(e)}"
            
            # Caso nada seja preenchido
            elif not (produto_id_adicionar or produto_id_remover):
                erro = "Por favor, preencha ao menos um campo (Adicionar ou Remover)."
            
            return render_template('inventario_estoque.html', produtos=produtos, sucesso=sucesso, erro=erro, mensagem=mensagem, produtos_estoque=produtos_estoque)
        
        return render_template('inventario_estoque.html', produtos=produtos, produtos_estoque=produtos_estoque)

    @app.route('/painel')
    def painel():
        if 'usuario' not in session:
            return redirect(url_for('login_view'))
        
        tipos = TipoProduto.query.all()
        dados_estoque = []
        
        for tipo in tipos:
            quantidade_estoque = db.session.query(func.count(Produto.id)).filter_by(tipo_produto_id=tipo.id).scalar() or 0
            qtd_vendida = db.session.query(func.sum(ItemVenda.quantidade))\
                .filter(ItemVenda.tipo_produto_id == tipo.id)\
                .scalar() or 0
            
            dados_estoque.append({
                'id': tipo.id,
                'tipo': tipo.nome,
                'estoque': quantidade_estoque,
                'vendido': qtd_vendida,
                'preco': float(tipo.preco)
            })
        
        return render_template('painel.html', produtos=dados_estoque)
    
    @app.route('/excluir-venda/<int:venda_id>', methods=['POST'])
    def excluir_venda(venda_id):
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        venda = Venda.query.get_or_404(venda_id)

        try:
            itens = ItemVenda.query.filter_by(venda_id=venda.id).all()

            for item in itens:
                for _ in range(item.quantidade):
                    produto = Produto(tipo_produto_id=item.tipo_produto_id)
                    db.session.add(produto)

            ItemVenda.query.filter_by(venda_id=venda.id).delete()
            db.session.delete(venda)
            db.session.commit()

            return redirect(url_for('listar_vendas'))

        except Exception as e:
            db.session.rollback()
            return f"Erro ao excluir a venda: {str(e)}", 500