"""
config.py — Configurações alternativas da aplicação.

Define a classe Config com as variáveis de configuração do banco de dados.
Pode ser usada com app.config.from_object(Config) como alternativa
à configuração direta feita em app.py.
"""

import os

# Diretório base do projeto (onde este arquivo está)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configurações do Flask e SQLAlchemy."""

    # Caminho do banco SQLite (arquivo database.db na raiz do projeto)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "database.db")}'

    # Desativa o rastreamento de modificações do SQLAlchemy (economia de memória)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
