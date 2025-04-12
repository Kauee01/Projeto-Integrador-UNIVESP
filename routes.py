from flask import request, jsonify, render_template, redirect, session, url_for
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

    @app.route('/editar-produto/<int:produto_id>', methods=['GET', 'POST'])
    def editar_produto(produto_id):
        if 'usuario' not in session:
            return redirect(url_for('login_view'))
        produto = Produto.query.get_or_404(produto_id)
        tipos = TipoProduto.query.all()
        if request.method == 'POST':
            novo_tipo_id = request.form['tipo_produto_id']
            novo_preco = request.form['preco']

            # Atualiza o tipo_produto_id do produto
            produto.tipo_produto_id = novo_tipo_id

            # Atualiza o preço do TipoProduto associado
            tipo = TipoProduto.query.get(novo_tipo_id)
            if tipo:
                tipo.preco = novo_preco

            db.session.commit()
            return redirect(url_for('painel'))

        return render_template('editar_produto.html', produto=produto, tipos=tipos)

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

    @app.route('/registrar-venda', methods=['GET'])
    def registrar_venda_view():
        if 'usuario' not in session:
            return redirect(url_for('login_view'))
        tipos = TipoProduto.query.all()
        pagamentos = TipoPagamento.query.all()
        return render_template('registrar_venda.html', tipos=tipos, pagamentos=pagamentos)

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
    def listar_vendas_html():
        if 'usuario' not in session:
            return redirect(url_for('login_view'))
        vendas = Venda.query.all()
        return render_template('listar_vendas.html', vendas=vendas)

    @app.route('/adicionar-estoque', methods=['GET', 'POST'])
    def adicionar_estoque():
        if 'usuario' not in session:
            return redirect(url_for('login_view'))
        tipos = TipoProduto.query.all()
        if request.method == 'POST':
            tipo_produto_id = request.form['tipo_produto_id']
            quantidade = int(request.form['quantidade'])

            # Validação dos dados
            if not tipo_produto_id or quantidade <= 0:
                return render_template('adicionar_estoque.html', erro="Dados inválidos", produtos=tipos)

            # Cria novos registros de Produto para representar a quantidade adicionada
            for _ in range(quantidade):
                novo_produto = Produto(tipo_produto_id=tipo_produto_id)
                db.session.add(novo_produto)

            db.session.commit()
            return render_template('adicionar_estoque.html', sucesso="Estoque atualizado com sucesso", produtos=tipos)

        return render_template('adicionar_estoque.html', produtos=tipos)

    @app.route('/painel')
    def painel():
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        tipos = TipoProduto.query.all()
        dados_estoque = []

        for tipo in tipos:
            # Conta a quantidade de produtos para este tipo_produto_id
            quantidade_estoque = db.session.query(func.count(Produto.id)).filter_by(tipo_produto_id=tipo.id).scalar() or 0

            # Calcula a quantidade vendida
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