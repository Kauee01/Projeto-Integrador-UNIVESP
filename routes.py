"""
routes.py — Definição de todas as rotas (endpoints) da aplicação.

Organização:
- Autenticação: login, cadastro de usuário, logout
- Home: página inicial com resumo do sistema
- Produtos: cadastro, edição e exclusão de produtos
- Estoque: painel de estoque, inventário (adicionar/remover)
- Vendas: registro de vendas, listagem, exclusão
- Pagamentos: cadastro e exclusão de tipos de pagamento
- Dashboard: painel administrativo com indicadores e gráficos
"""

from flask import request, jsonify, render_template, redirect, session, url_for, flash
from models import db, TipoProduto, Produto, Venda, ItemVenda, TipoPagamento, Categoria, Usuario
from datetime import datetime
from sqlalchemy import func


def register_routes(app):
    """Registra todas as rotas no app Flask recebido."""

    # =====================================================================
    # AUTENTICAÇÃO
    # =====================================================================

    @app.route('/')
    def login_view():
        """Exibe a página de login (página inicial da aplicação)."""
        return render_template('login.html')

    @app.route('/auth', methods=['POST'])
    def autenticar():
        """Processa o formulário de login.
        Valida usuário e senha, cria a sessão e redireciona para /home.
        """
        usuario = request.form['username']
        senha = request.form['senha']

        # Busca o usuário no banco pelo nome de usuário
        usuario_obj = Usuario.query.filter_by(username=usuario).first()

        if usuario_obj and usuario_obj.check_senha(senha):
            # Credenciais válidas — cria a sessão
            session['usuario'] = usuario
            session['is_admin'] = usuario_obj.is_admin
            return redirect(url_for('home'))
        else:
            # Credenciais inválidas — retorna erro na página de login
            return render_template('login.html', erro="Usuário ou senha inválidos")

    @app.route('/cadastrar-usuario', methods=['GET', 'POST'])
    def cadastrar_usuario():
        """Exibe formulário e processa o cadastro de novo usuário."""
        if request.method == 'POST':
            usuario = request.form['username']
            senha = request.form['senha']

            # Verifica se já existe um usuário com este nome
            if Usuario.query.filter_by(username=usuario).first():
                return render_template('cadastro.html', erro="Usuário já existe!")

            # Cria o novo usuário com senha em hash
            novo_usuario = Usuario(username=usuario)
            novo_usuario.set_senha(senha)

            db.session.add(novo_usuario)
            db.session.commit()

            # Redireciona para o login com mensagem de sucesso
            flash("Conta criada com sucesso! Faça login.", "success")
            return redirect(url_for('login_view'))

        return render_template('cadastro.html')

    @app.route('/logout')
    def logout():
        """Encerra a sessão do usuário e redireciona para o login."""
        session.pop('usuario', None)
        session.pop('is_admin', None)
        return redirect(url_for('login_view'))

    # =====================================================================
    # HOME
    # =====================================================================

    @app.route('/home')
    def home():
        """Página inicial com cards de resumo: estoque, vendidos e faturamento."""
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        # Total de unidades em estoque (conta registros na tabela Produto)
        total_estoque = db.session.query(func.count(Produto.id)).scalar() or 0

        # Total de unidades já vendidas (soma das quantidades em ItemVenda)
        total_vendido = db.session.query(
            func.sum(ItemVenda.quantidade)).scalar() or 0

        # Faturamento total (soma dos valores de todas as vendas)
        valor_total = db.session.query(
            func.sum(Venda.valor_total)).scalar() or 0.00

        return render_template(
            'home.html',
            usuario=session['usuario'],
            total_estoque=int(total_estoque),
            total_vendido=int(total_vendido),
            valor_total=f"{valor_total:.2f}"
        )

    # =====================================================================
    # PRODUTOS — Cadastro, Edição e Exclusão
    # =====================================================================

    @app.route('/cadastrar-produto', methods=['GET', 'POST'])
    def exibir_form_produto():
        """Exibe formulário e processa o cadastro de novo produto."""
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
                return render_template(
                    'cadastrar_produto.html',
                    erro="Todos os campos obrigatórios devem ser preenchidos",
                    categorias=categorias
                )

            # Cria o TipoProduto (modelo/tipo do produto)
            tipo = TipoProduto(
                nome=nome,
                descricao=descricao,
                preco=preco,
                categoria_id=categoria_id
            )
            db.session.add(tipo)
            db.session.commit()

            # Cria N registros de Produto para representar a quantidade em estoque
            # (cada registro = 1 unidade física)
            for _ in range(quantidade):
                produto = Produto(tipo_produto_id=tipo.id)
                db.session.add(produto)

            db.session.commit()
            return redirect(url_for('painel'))

        return render_template('cadastrar_produto.html', categorias=categorias)

    @app.route('/editar-tipo-produto/<int:tipo_produto_id>', methods=['GET', 'POST'])
    def editar_tipo_produto(tipo_produto_id):
        """Exibe formulário e processa a edição de preço de um tipo de produto.
        Requer confirmação com senha do usuário logado.
        """
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        tipo_produto = TipoProduto.query.get_or_404(tipo_produto_id)
        tipos = TipoProduto.query.all()

        if request.method == 'POST':
            novo_nome = request.form.get('nome')
            novo_preco = request.form.get('preco')
            senha = request.form.get('senha')

            # Valida a senha do usuário logado antes de permitir edição
            usuario = Usuario.query.filter_by(
                username=session['usuario']).first()
            if not usuario.check_senha(senha):
                return render_template(
                    'editar_produto.html',
                    tipo_produto=tipo_produto,
                    tipos=tipos,
                    erro="Senha incorreta."
                )

            # Atualiza o nome se fornecido
            if novo_nome:
                tipo_produto.nome = novo_nome

            # Atualiza o preço se fornecido e válido
            if novo_preco:
                try:
                    novo_preco = float(novo_preco)
                    if novo_preco <= 0:
                        raise ValueError("Preço inválido")
                    tipo_produto.preco = novo_preco
                except (ValueError, TypeError):
                    return render_template(
                        'editar_produto.html',
                        tipo_produto=tipo_produto,
                        tipos=tipos,
                        erro="Preço inválido."
                    )

            db.session.commit()
            return redirect(url_for('painel'))

        return render_template('editar_produto.html', tipo_produto=tipo_produto, tipos=tipos)

    @app.route('/excluir-produto/<int:produto_id>', methods=['POST'])
    def excluir_produto(produto_id):
        """Exclui uma unidade de produto do estoque.
        Impede a exclusão se o tipo de produto estiver vinculado a vendas.
        """
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        produto = Produto.query.get_or_404(produto_id)

        # Verifica se o tipo de produto já foi vendido (proteção de integridade)
        if ItemVenda.query.filter_by(tipo_produto_id=produto.tipo_produto_id).first():
            return "Este produto está relacionado a vendas e não pode ser excluído.", 400

        db.session.delete(produto)
        db.session.commit()
        return redirect(url_for('painel'))

    # =====================================================================
    # ESTOQUE — Painel e Inventário
    # =====================================================================

    @app.route('/painel')
    def painel():
        """Painel de estoque: lista todos os tipos de produto com
        quantidade em estoque, unidades vendidas e preço.
        """
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        tipos = TipoProduto.query.all()
        dados_estoque = []

        for tipo in tipos:
            # Conta quantas unidades físicas existem para este tipo
            quantidade_estoque = (
                db.session.query(func.count(Produto.id))
                .filter_by(tipo_produto_id=tipo.id)
                .scalar() or 0
            )

            # Soma a quantidade total vendida deste tipo
            qtd_vendida = (
                db.session.query(func.sum(ItemVenda.quantidade))
                .filter(ItemVenda.tipo_produto_id == tipo.id)
                .scalar() or 0
            )

            dados_estoque.append({
                'id': tipo.id,
                'tipo': tipo.nome,
                'estoque': quantidade_estoque,
                'vendido': qtd_vendida,
                'preco': float(tipo.preco)
            })

        return render_template('painel.html', produtos=dados_estoque)

    @app.route('/inventario-estoque', methods=['GET', 'POST'])
    def inventario_estoque():
        """Inventário: permite adicionar ou remover unidades do estoque."""
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        produtos = TipoProduto.query.all()

        if request.method == 'POST':
            sucesso = None
            erro = None

            produto_id_adicionar = request.form.get('produto_id_adicionar')
            quantidade_adicionar = request.form.get('quantidade_adicionar')
            produto_id_remover = request.form.get('produto_id_remover')
            quantidade_remover = request.form.get('quantidade_remover')

            # --- Adicionar ao Estoque ---
            if produto_id_adicionar and quantidade_adicionar:
                try:
                    quantidade_adicionar = int(quantidade_adicionar)
                    if quantidade_adicionar < 1:
                        erro = "A quantidade a adicionar deve ser maior que zero!"
                    else:
                        # Cria N registros de Produto (1 registro = 1 unidade física)
                        for _ in range(quantidade_adicionar):
                            novo_produto = Produto(
                                tipo_produto_id=produto_id_adicionar)
                            db.session.add(novo_produto)
                        db.session.commit()
                        sucesso = f"{quantidade_adicionar} unidade(s) adicionada(s) ao estoque!"
                except Exception as e:
                    db.session.rollback()
                    erro = f"Ocorreu um erro ao adicionar: {str(e)}"

            # --- Remover do Estoque ---
            elif produto_id_remover and quantidade_remover:
                try:
                    quantidade_remover = int(quantidade_remover)
                    if quantidade_remover < 1:
                        erro = "A quantidade a remover deve ser maior que zero!"
                    else:
                        # Busca as unidades a serem removidas (limitado à quantidade solicitada)
                        produtos_para_remover = (
                            Produto.query
                            .filter_by(tipo_produto_id=produto_id_remover)
                            .limit(quantidade_remover)
                            .all()
                        )

                        if len(produtos_para_remover) < quantidade_remover:
                            erro = "Não há quantidade suficiente para remover do estoque!"
                        else:
                            for produto in produtos_para_remover:
                                db.session.delete(produto)
                            db.session.commit()
                            sucesso = f"{quantidade_remover} unidade(s) removida(s) do estoque!"
                except Exception as e:
                    db.session.rollback()
                    erro = f"Ocorreu um erro ao remover: {str(e)}"

            # --- Nenhum campo preenchido ---
            elif not (produto_id_adicionar or produto_id_remover):
                erro = "Por favor, preencha ao menos um campo (Adicionar ou Remover)."

            return render_template(
                'inventario_estoque.html',
                produtos=produtos,
                sucesso=sucesso,
                erro=erro
            )

        return render_template('inventario_estoque.html', produtos=produtos)

    # =====================================================================
    # VENDAS — Registro, Listagem e Exclusão
    # =====================================================================

    @app.route('/registrar-venda', methods=['GET', 'POST'])
    def registrar_venda():
        """Exibe a tela de registro de venda (GET) ou processa uma venda via JSON (POST)."""
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        tipos_produto = TipoProduto.query.all()
        tipos_pagamento = TipoPagamento.query.all()

        # Monta a lista de produtos com estoque disponível para a tela
        total_geral = 0.0
        dados_produtos = []
        for tipo in tipos_produto:
            quantidade_estoque = (
                db.session.query(func.count(Produto.id))
                .filter_by(tipo_produto_id=tipo.id)
                .scalar() or 0
            )
            dados_produtos.append({
                'id': tipo.id,
                'nome': tipo.nome,
                'preco': tipo.preco,
                'quantidade': quantidade_estoque
            })

        if request.method == 'POST':
            # Recebe os dados da venda em formato JSON (enviado via fetch no JS)
            try:
                dados = request.get_json()
            except Exception as e:
                return jsonify({'error': f'Erro ao processar os dados. {str(e)}'}), 400

            tipo_pagamento_id = dados.get('tipo_pagamento_id')
            itens_venda = dados.get('itens', [])

            # Validação dos campos obrigatórios
            if not tipo_pagamento_id or not itens_venda:
                return jsonify({'error': 'Por favor, preencha todos os campos.'}), 400

            try:
                tipo_pagamento_id = int(tipo_pagamento_id)
            except ValueError:
                return jsonify({'error': 'Tipo de pagamento inválido.'}), 400

            total_geral = 0

            try:
                # Cria o registro da venda com valor_total = 0 (será atualizado após os itens)
                nova_venda = Venda(
                    tipo_pagamento_id=tipo_pagamento_id,
                    data=datetime.now(),
                    valor_total=0
                )
                db.session.add(nova_venda)
                db.session.commit()

                # Processa cada item da venda
                for item in itens_venda:
                    produto = TipoProduto.query.get(item['produto_id'])
                    if not produto:
                        return jsonify({'error': 'Produto não encontrado.'}), 404

                    # Verifica se há estoque suficiente
                    quantidade_estoque = (
                        db.session.query(func.count(Produto.id))
                        .filter_by(tipo_produto_id=produto.id)
                        .scalar() or 0
                    )
                    if item['quantidade'] > quantidade_estoque:
                        return jsonify({
                            'error': f'Estoque insuficiente para {produto.nome}. '
                            f'Disponível: {quantidade_estoque}.'
                        }), 400

                    # Calcula o subtotal do item
                    total_produto = produto.preco * item['quantidade']
                    total_geral += total_produto

                    # Cria o registro do item vendido
                    item_venda = ItemVenda(
                        venda_id=nova_venda.id,
                        tipo_produto_id=produto.id,
                        quantidade=item['quantidade'],
                        valor_produtos=produto.preco
                    )
                    db.session.add(item_venda)

                    # Remove as unidades vendidas do estoque (deleta N registros de Produto)
                    produtos_remover = (
                        Produto.query
                        .filter_by(tipo_produto_id=produto.id)
                        .limit(item['quantidade'])
                        .all()
                    )
                    for produto_remover in produtos_remover:
                        db.session.delete(produto_remover)

                # Atualiza o valor total da venda
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

    @app.route('/listar-vendas')
    def listar_vendas():
        """Lista todas as vendas realizadas, ordenadas por ID decrescente."""
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        vendas = Venda.query.order_by(Venda.id.desc()).all()
        return render_template('listar_vendas.html', vendas=vendas)

    @app.route('/excluir-venda/<int:venda_id>', methods=['POST'])
    def excluir_venda(venda_id):
        """Exclui uma venda e devolve os produtos ao estoque.
        Para cada item da venda, recria os registros de Produto correspondentes.
        """
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        venda = Venda.query.get_or_404(venda_id)

        try:
            # Devolve as unidades ao estoque (recria registros de Produto)
            itens = ItemVenda.query.filter_by(venda_id=venda.id).all()
            for item in itens:
                for _ in range(item.quantidade):
                    produto = Produto(tipo_produto_id=item.tipo_produto_id)
                    db.session.add(produto)

            # Remove os itens e a venda do banco
            ItemVenda.query.filter_by(venda_id=venda.id).delete()
            db.session.delete(venda)
            db.session.commit()

            return redirect(url_for('listar_vendas'))

        except Exception as e:
            db.session.rollback()
            return f"Erro ao excluir a venda: {str(e)}", 500

    # =====================================================================
    # PAGAMENTOS — Cadastro e Exclusão
    # =====================================================================

    @app.route('/cadastrar-pagamento', methods=['GET', 'POST'])
    def cadastrar_pagamento():
        """Exibe formulário e processa o cadastro de tipos de pagamento."""
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        tipos_pagamento = TipoPagamento.query.all()

        if request.method == 'POST':
            nome = request.form['nome']

            # Validação: nome obrigatório e único
            if not nome:
                return render_template(
                    'cadastrar_pagamento.html',
                    erro="Nome obrigatório",
                    tipos_pagamento=tipos_pagamento
                )
            if TipoPagamento.query.filter_by(nome=nome).first():
                return render_template(
                    'cadastrar_pagamento.html',
                    erro="Tipo já existe",
                    tipos_pagamento=tipos_pagamento
                )

            # Cria e salva o novo tipo de pagamento
            tipo = TipoPagamento(nome=nome)
            db.session.add(tipo)
            db.session.commit()

            # Recarrega a lista atualizada
            tipos_pagamento = TipoPagamento.query.all()
            return render_template(
                'cadastrar_pagamento.html',
                sucesso="Tipo de pagamento cadastrado com sucesso!",
                tipos_pagamento=tipos_pagamento
            )

        return render_template('cadastrar_pagamento.html', tipos_pagamento=tipos_pagamento)

    @app.route('/excluir-tipopagamento/<int:tipo_id>', methods=['POST'])
    def excluir_tipo_pagamento(tipo_id):
        """Exclui um tipo de pagamento.
        Impede a exclusão se já houver vendas vinculadas a este tipo.
        """
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        tipo = TipoPagamento.query.get_or_404(tipo_id)

        # Verifica se o tipo de pagamento está sendo usado em alguma venda
        if Venda.query.filter_by(tipo_pagamento_id=tipo.id).first():
            return "Este tipo de pagamento já foi usado em uma venda e não pode ser excluído.", 400

        db.session.delete(tipo)
        db.session.commit()
        return redirect(url_for('cadastrar_pagamento'))

    # =====================================================================
    # DASHBOARD — Painel Administrativo (somente admin)
    # =====================================================================

    @app.route('/dashboard')
    def dashboard():
        """Dashboard com indicadores de vendas, gráficos e alertas de estoque.
        Acessível apenas para usuários com is_admin = True.
        """
        if 'usuario' not in session:
            return redirect(url_for('login_view'))

        # Redireciona para home se o usuário não for admin
        if not session.get('is_admin'):
            return redirect(url_for('home'))

        # Mês selecionado no filtro (padrão: mês atual)
        mes_selecionado = request.args.get('mes')
        if not mes_selecionado:
            mes_selecionado = datetime.now().strftime('%Y-%m')

        # Lista de meses com vendas registradas (para o seletor de filtro)
        lista_meses = (
            db.session.query(func.strftime('%Y-%m', Venda.data).label('mes'))
            .distinct()
            .order_by(func.strftime('%Y-%m', Venda.data).desc())
            .all()
        )
        lista_meses = [item.mes for item in lista_meses if item.mes]

        # --- Indicadores principais do mês ---

        # Quantidade de vendas no mês
        total_vendas = (
            db.session.query(func.count(Venda.id))
            .filter(func.strftime('%Y-%m', Venda.data) == mes_selecionado)
            .scalar() or 0
        )

        # Faturamento total no mês (soma dos valores das vendas)
        faturamento_total = (
            db.session.query(func.sum(Venda.valor_total))
            .filter(func.strftime('%Y-%m', Venda.data) == mes_selecionado)
            .scalar() or 0
        )

        # Ticket médio (valor médio por venda)
        ticket_medio = (
            db.session.query(func.avg(Venda.valor_total))
            .filter(func.strftime('%Y-%m', Venda.data) == mes_selecionado)
            .scalar() or 0
        )

        # Total de unidades vendidas no mês
        quantidade_produtos_vendidos = (
            db.session.query(func.sum(ItemVenda.quantidade))
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .filter(func.strftime('%Y-%m', Venda.data) == mes_selecionado)
            .scalar() or 0
        )

        # --- Destaques do mês ---

        # Categoria que mais vendeu (por quantidade de unidades)
        categoria_mais_vendida = (
            db.session.query(
                Categoria.nome.label('categoria'),
                func.sum(ItemVenda.quantidade).label('quantidade_vendida')
            )
            .join(TipoProduto, TipoProduto.categoria_id == Categoria.id)
            .join(ItemVenda, ItemVenda.tipo_produto_id == TipoProduto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .filter(func.strftime('%Y-%m', Venda.data) == mes_selecionado)
            .group_by(Categoria.id, Categoria.nome)
            .order_by(func.sum(ItemVenda.quantidade).desc())
            .first()
        )

        # Produto que mais vendeu (por quantidade de unidades)
        produto_mais_vendido = (
            db.session.query(
                TipoProduto.nome.label('produto'),
                func.sum(ItemVenda.quantidade).label('quantidade_vendida')
            )
            .join(ItemVenda, ItemVenda.tipo_produto_id == TipoProduto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .filter(func.strftime('%Y-%m', Venda.data) == mes_selecionado)
            .group_by(TipoProduto.id, TipoProduto.nome)
            .order_by(func.sum(ItemVenda.quantidade).desc())
            .first()
        )

        # --- Dados para o gráfico de barras (vendas por categoria) ---
        categorias_vendas = (
            db.session.query(
                Categoria.nome,
                func.sum(ItemVenda.quantidade).label('quantidade_vendida')
            )
            .join(TipoProduto, TipoProduto.categoria_id == Categoria.id)
            .join(ItemVenda, ItemVenda.tipo_produto_id == TipoProduto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .filter(func.strftime('%Y-%m', Venda.data) == mes_selecionado)
            .group_by(Categoria.id, Categoria.nome)
            .order_by(func.sum(ItemVenda.quantidade).desc())
            .all()
        )

        # --- Drill-down: produtos vendidos por categoria (para clique no gráfico) ---
        produtos_por_categoria = (
            db.session.query(
                Categoria.nome.label('categoria'),
                TipoProduto.nome.label('produto'),
                func.sum(ItemVenda.quantidade).label('quantidade_vendida')
            )
            .join(TipoProduto, TipoProduto.categoria_id == Categoria.id)
            .join(ItemVenda, ItemVenda.tipo_produto_id == TipoProduto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .filter(func.strftime('%Y-%m', Venda.data) == mes_selecionado)
            .group_by(Categoria.nome, TipoProduto.nome)
            .order_by(Categoria.nome, func.sum(ItemVenda.quantidade).desc())
            .all()
        )

        # Organiza os produtos por categoria em um dicionário para uso no template
        produtos_categoria_dict = {}
        for item in produtos_por_categoria:
            if item.categoria not in produtos_categoria_dict:
                produtos_categoria_dict[item.categoria] = []
            produtos_categoria_dict[item.categoria].append({
                'produto': item.produto,
                'quantidade_vendida': int(item.quantidade_vendida or 0)
            })

        # --- Alerta de estoque baixo (≤ 5 unidades) ---
        estoque_baixo = []
        tipos = TipoProduto.query.all()
        for tipo in tipos:
            quantidade_estoque = (
                db.session.query(func.count(Produto.id))
                .filter_by(tipo_produto_id=tipo.id)
                .scalar() or 0
            )
            if quantidade_estoque <= 5:
                estoque_baixo.append({
                    'nome': tipo.nome,
                    'estoque': quantidade_estoque
                })

        # --- Renderiza o template com todos os dados ---
        return render_template(
            'dashboard.html',
            mes_selecionado=mes_selecionado,
            lista_meses=lista_meses,
            total_vendas=total_vendas,
            faturamento_total=float(faturamento_total or 0),
            ticket_medio=float(ticket_medio or 0),
            quantidade_produtos_vendidos=int(
                quantidade_produtos_vendidos or 0),
            categoria_mais_vendida=categoria_mais_vendida,
            produto_mais_vendido=produto_mais_vendido,
            categorias_vendas=categorias_vendas,
            produtos_categoria_dict=produtos_categoria_dict,
            estoque_baixo=estoque_baixo
        )
