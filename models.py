import sqlite3


def init_db():
    try:
        conn = sqlite3.connect('database.db') 
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        print("Banco de dados inicializado com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")

def inserir_usuario(nome, email, senha):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO usuarios (nome, email, senha)
            VALUES (?, ?, ?)
        ''', (nome, email, senha))
        conn.commit()
        conn.close()
        return None 
    except sqlite3.IntegrityError as e:
        return "Email já cadastrado."
    except Exception as e:
        return f"Erro ao inserir usuário: {e}"

def buscar_usuario(email, senha):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT nome, email
            FROM usuarios
            WHERE email = ? AND senha = ?
        ''', (email, senha))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            return {"nome": resultado[0], "email": resultado[1]}
        return None 
    except Exception as e:
        print(f"Erro ao buscar usuário: {e}")
        return None


def deletar_usuario(email):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM usuarios
            WHERE email = ?
        ''', (email,))

        conn.commit()
        
        if cursor.rowcount == 0:
            print("Usuário não encontrado.")
            return "Usuário não encontrado."
        print(f"Usuário com email {email} deletado com sucesso.")
        conn.close()
        return None
    except Exception as e:
        print(f"Erro ao deletar usuário: {e}")
        return str(e)
