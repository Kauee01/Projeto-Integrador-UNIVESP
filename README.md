# Sistema de Gestão de Estoque e Vendas

Este é um sistema web desenvolvido com Flask para gerenciamento de estoque e vendas, criado como parte do Projeto Integrador da UNIVESP.

## 🚀 Funcionalidades

- Cadastro e gestão de produtos
- Controle de estoque
- Registro de vendas
- Gestão de pagamentos
- Sistema de autenticação de usuários
- Relatórios de vendas
- Feedback de vendas

## 🛠️ Tecnologias Utilizadas

- **Python 3.13**
- **Flask** - Framework web
- **SQLAlchemy** - ORM para banco de dados
- **Flask-Migrate** - Gerenciamento de migrações do banco de dados
- **SQLite** - Banco de dados
- **HTML/CSS/JavaScript** - Frontend
- **Bootstrap** - Framework CSS

## 📋 Pré-requisitos

- Python 3.x
- pip (gerenciador de pacotes Python)

## 🔧 Instalação

1. Clone o repositório:

    ```bash
    git clone https://github.com/Kauee01/Projeto-Integrador-UNIVESP.git
    cd Projeto-Integrador-UNIVESP
    ```

2. Crie um ambiente virtual (recomendado):

    ```bash
    python -m venv venv
    venv\Scripts\activate  # Windows
    ```

3. Instale as dependências:

    ```bash
    pip install -r requirements.txt
    ```

4. Configure o banco de dados:

    ```bash
    flask db upgrade
    ```

5. Execute a aplicação:

    ```bash
    python app.py
    ```

A aplicação estará disponível em `http://localhost:5000`

## 🗄️ Estrutura do Projeto

- `app.py` - Arquivo principal da aplicação
- `config.py` - Configurações do projeto
- `models.py` - Modelos do banco de dados
- `routes.py` - Rotas da aplicação
- `templates/` - Arquivos HTML
- `static/` - Arquivos estáticos (JS, CSS)
- `migrations/` - Scripts de migração do banco de dados
- `tests/` - Testes unitários

## 🧪 Testes

Para executar os testes:

```bash
pytest
```

## ✒️ Autores

- Desenvolvido como parte do Projeto Integrador da UNIVESP