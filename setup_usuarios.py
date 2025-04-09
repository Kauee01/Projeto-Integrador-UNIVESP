import sqlite3
from werkzeug.security import generate_password_hash

# Caminho do banco de dados
caminho_banco = 'instance/database.db'

# Dados do usuário de teste
username = 'admin'
senha_plana = '1234'
senha_hash = generate_password_hash(senha_plana)

# Conexão com o banco
conn = sqlite3.connect(caminho_banco)
cursor = conn.cursor()

# Criar tabela se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL
)
""")

# Inserir usuário admin
cursor.execute("INSERT OR IGNORE INTO usuarios (username, senha) VALUES (?, ?)", (username, senha_hash))

conn.commit()
conn.close()

print("✅ Tabela 'usuarios' criada e usuário 'admin' adicionado com sucesso.")
