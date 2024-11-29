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
                senha TEXT NOT NULL,
                foto_perfil TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("Banco de dados inicializado com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")

def inserir_usuario(nome, email, senha, foto_perfil=None):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, foto_perfil)
            VALUES (?, ?, ?, ?)
        ''', (nome, email, senha, foto_perfil))
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
            SELECT nome, email, foto_perfil
            FROM usuarios
            WHERE email = ? AND senha = ?
        ''', (email, senha))
        resultado = cursor.fetchone()
        conn.close()

        if resultado:
            return {"nome": resultado[0], "email": resultado[1], "foto_perfil": resultado[2]}
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

def adicionar_coluna_foto_perfil():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('''
            ALTER TABLE usuarios
            ADD COLUMN foto_perfil TEXT
        ''')
        conn.commit()
        conn.close()
        print("Coluna 'foto_perfil' adicionada com sucesso.")
    except Exception as e:
        print(f"Erro ao adicionar a coluna 'foto_perfil': {e}")

def create_musicas():
    try:
        conn = sqlite3.connect('database.db') 
        cursor = conn.cursor()

        # Criação das tabelas com a nova coluna de estilo
        cursor.execute('''CREATE TABLE IF NOT EXISTS bandas (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nome TEXT NOT NULL,
                            genero TEXT NOT NULL)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS partituras (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            banda_id INTEGER,
                            partitura TEXT,
                            estilo TEXT NOT NULL,
                            FOREIGN KEY(banda_id) REFERENCES bandas(id))''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS cifras (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            banda_id INTEGER,
                            cifra TEXT,
                            estilo TEXT NOT NULL,
                            FOREIGN KEY(banda_id) REFERENCES bandas(id))''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS tablaturas (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            banda_id INTEGER,
                            tablatura TEXT,
                            estilo TEXT NOT NULL,
                            FOREIGN KEY(banda_id) REFERENCES bandas(id))''')

        # Inserção das bandas
        cursor.execute('''INSERT OR IGNORE INTO bandas (nome, genero) VALUES
                        ('Oficina G3', 'gospel'), 
                        ('Vocal Livre', 'gospel'),
                        ('Diante do Trono', 'gospel'),
                        ('Preto no Branco', 'gospel')''')

        # Inserção de partituras, cifras e tablaturas com estilo
        cursor.execute('''INSERT OR IGNORE INTO partituras (banda_id, partitura, estilo) VALUES
                        (1, 'Partitura 1a', 'Gospel'), (1, 'Partitura 1b', 'Gospel'),
                        (2, 'Partitura 2a', 'Gospel'), (2, 'Partitura 2b', 'Gospel')''')

        cursor.execute('''INSERT OR IGNORE INTO cifras (banda_id, cifra, estilo) VALUES
                        (1, 'Cifra 1a', 'Gospel'), (1, 'Cifra 1b', 'Gospel'),
                        (2, 'Cifra 2a', 'Gospel'), (2, 'Cifra 2b', 'Gospel')''')

        cursor.execute('''INSERT OR IGNORE INTO tablaturas (banda_id, tablatura, estilo) VALUES
                        (1, 'Tablatura 1a', 'Gospel'), (1, 'Tablatura 1b', 'Gospel'),
                        (2, 'Tablatura 2a', 'Gospel'), (2, 'Tablatura 2b', 'Gospel')''')

        conn.commit()
        conn.close()
        print("Tabelas criadas e registros adicionados com sucesso.")

    except Exception as e:
        print(f'Erro ao criar os registros das bandas: {e}')
