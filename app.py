from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import timedelta
from models import init_db, inserir_usuario, deletar_usuario
from supabase import create_client, Client

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()

url = "https://zhuyytyhkmahjohqbsqd.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpodXl5dHloa21haGpvaHFic3FkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI4Nzg4NTMsImV4cCI6MjA0ODQ1NDg1M30.cyD6WqNNuGI4kPhtYSjBJ5TNennRxCnizcTrbRH-ufM"
supabase: Client = create_client(url, key)

def extrair_nome_arquivo(url):
    return url.split("/")[-1]

app.jinja_env.filters['nome_arquivo'] = extrair_nome_arquivo



def buscar_partituras(estilo=None):
    if estilo and estilo != 'Todos':
        response = supabase.table('partituras').select('arquivo_url').eq('estilo_musical', estilo).execute()
    else:
        response = supabase.table('partituras').select('arquivo_url').execute()
    
    return response.data if response.data else []

@app.route('/partituras/<estilo>', methods=['GET'])
def partituras_por_estilo(estilo):
    if estilo == 'Todos':
        response = supabase.table('partituras').select('arquivo_url').execute()
    else:
        response = supabase.table('partituras').select('arquivo_url').eq('estilo_musical', estilo).execute()

    partituras = response.data if response.data else []
    for partitura in partituras:
        partitura['nome_arquivo'] = partitura['arquivo_url'].split('/')[-1]

    return render_template('partituras.html', partituras=partituras, estilo=estilo)


@app.route('/')
def home():
    if 'nome' not in session:
        return redirect(url_for('login'))
    
    nome = session['nome']
    foto_perfil = session.get('foto_perfil', None)

    response = supabase.table('partituras').select('arquivo_url').execute()
    partituras = response.data if response.data else []

    return render_template('index.html', nome=nome, foto_perfil=foto_perfil, partituras=partituras)


@app.route('/criarconta', methods=['GET', 'POST'])
def criar_conta():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        resultado = inserir_usuario(nome, email, senha)
        if resultado:
            return f"Erro ao criar conta: {resultado}"

        return redirect(url_for('home'))
    return render_template('criarconta.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            session.permanent = True
            session['email'] = email
            session['nome'] = usuario[1]
            session['foto_perfil'] = usuario[4]
            return redirect(url_for('perfil'))
        else:
            return "Login falhou. Verifique suas credenciais."

    return render_template('login.html')

@app.route('/perfil')
def perfil():
    if 'email' in session:
        email = session['email']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nome, email, foto_perfil FROM usuarios WHERE email = ?", (email,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            return render_template('perfil.html', nome=usuario[0], email=usuario[1], foto_perfil=usuario[2])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('nome', None)
    session.pop('foto_perfil', None)
    return redirect(url_for('login'))

@app.route('/apagarconta', methods=['GET', 'POST'])
def apagar_conta():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        email = session['email']
        
        resultado = deletar_usuario(email)
        if resultado:
            print(f"Resultado: {resultado}")
            return f"Erro ao apagar a conta: {resultado}"
        
        session.clear()
        return redirect(url_for('home'))
    
    return render_template('apagarconta.html')

@app.route('/upload_foto', methods=['POST'])
def upload_foto():
    if 'foto_perfil' not in request.files:
        return "Nenhum arquivo enviado."

    file = request.files['foto_perfil']
    if file.filename == '':
        return "Nenhuma imagem selecionada."

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''UPDATE usuarios SET foto_perfil = ? WHERE email = ?''', (f'uploads/{filename}', session['email']))
        conn.commit()
        conn.close()

        session['foto_perfil'] = f'uploads/{filename}'
        return redirect(url_for('perfil'))

@app.route('/pesquisa', methods=['GET'])
def pesquisa():
    query = request.args.get('q', '').lower()
    
    partituras_resultados = [partitura for partitura in partituras if query in partitura['arquivo_url'].lower()]
    
    return render_template('index.html', partituras=partituras_resultados)

@app.route('/inserir_partitura', methods=['GET', 'POST'])
def inserir_partitura():
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        estilo_musical = request.form['estilo_musical']
        arquivo_url = request.form['arquivo_url']

        response = supabase.table('partituras').insert({
            'estilo_musical': estilo_musical,
            'arquivo_url': arquivo_url
        }).execute()

        if response.status_code == 201:
            return redirect(url_for('home'))
        else:
            return f"Erro ao inserir partitura: {response.error_message}"

    return render_template('inserir_partitura.html')

if __name__ == '__main__':
    app.run(debug=True)
