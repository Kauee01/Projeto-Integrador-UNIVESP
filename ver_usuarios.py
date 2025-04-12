import sqlite3

conn = sqlite3.connect('instance/database.db')
cursor = conn.cursor()

cursor.execute("SELECT id, username FROM usuarios")
usuarios = cursor.fetchall()

print("Usuários cadastrados:")
for u in usuarios:
    print(f"ID: {u[0]} | Usuário: {u[1]}")

conn.close()