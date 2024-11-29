from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
from datetime import timedelta
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Inicialização do Flask
app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)

# Configuração de sessão e upload de arquivos
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Credenciais do Supabase
url = "https://zhuyytyhkmahjohqbsqd.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpodXl5dHloa21haGpvaHFic3FkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI4Nzg4NTMsImV4cCI6MjA0ODQ1NDg1M30.cyD6WqNNuGI4kPhtYSjBJ5TNennRxCnizcTrbRH-ufM"
supabase: Client = create_client(url, key)

# Função para registrar o filtro personalizado no Flask
def extrair_nome_arquivo(url):
    return url.split("/")[-1]

app.jinja_env.filters['nome_arquivo'] = extrair_nome_arquivo

# Função de buscar partituras no Supabase
def buscar_partituras(estilo=None):
    if estilo and estilo != 'Todos':
        response = supabase.table('partituras').select('arquivo_url').eq('estilo_musical', estilo).execute()
    else:
        response = supabase.table('partituras').select('arquivo_url').execute()
    return response.data if response.data else []

# Rota para a pesquisa
@app.route('/pesquisa', methods=['GET'])
def pesquisa():
    query = request.args.get('q', '').lower()
    response = supabase.table('partituras').select('arquivo_url').execute()
    partituras = response.data if response.data else []
    partituras_resultados = [partitura for partitura in partituras if query in partitura['arquivo_url'].lower()]
    return render_template('index.html', partituras=partituras_resultados)

# Rota para o login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        response = supabase.table('usuarios').select('id', 'email', 'senha', 'nome').eq('email', email).execute()

        if response.data:
            usuario = response.data[0]
            if check_password_hash(usuario['senha'], senha):
                session['nome'] = usuario['nome']
                session['usuario_id'] = usuario['id']
                session['email'] = usuario['email']  # Salvar o e-mail na sessão
                return redirect(url_for('home'))
            else:
                return render_template('login.html', erro="Senha incorreta.")
        else:
            return render_template('login.html', erro="Email não encontrado.")
    
    return render_template('login.html')

# Rota para a página inicial
@app.route('/')
def home():
    if 'nome' not in session:
        return redirect(url_for('login'))

    nome = session['nome']
    foto_perfil = session.get('foto_perfil', None)

    response = supabase.table('partituras').select('arquivo_url').execute()
    partituras = response.data if response.data else []

    return render_template('index.html', nome=nome, foto_perfil=foto_perfil, partituras=partituras)

# Função para logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Função para perfil do usuário
@app.route('/perfil')
def perfil():
    if 'nome' not in session:
        return redirect(url_for('login'))

    nome = session['nome']
    foto_perfil = session.get('foto_perfil', None)
    email = session.get('email', None)  # Recupera o e-mail da sessão

    return render_template('perfil.html', nome=nome, foto_perfil=foto_perfil, email=email)

# Rota para upload de foto de perfil
@app.route('/upload_foto', methods=['POST'])
def upload_foto():
    if 'nome' not in session:
        return redirect(url_for('login'))

    foto = request.files.get('foto_perfil')

    if foto:
        filename = secure_filename(foto.filename)
        foto_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        foto.save(foto_path)

        # Atualizar a foto de perfil na sessão
        session['foto_perfil'] = f'uploads/{filename}'

        # Você pode também atualizar a foto de perfil no banco de dados, se necessário
        supabase.table('usuarios').update({'foto_perfil': f'uploads/{filename}'}).eq('id', session['usuario_id']).execute()

        return redirect(url_for('perfil'))

    return render_template('perfil.html', erro="Falha ao enviar a foto.")

# Função para criar conta
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        # Lógica para criar a conta do usuário
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='sha256')

        new_user = {
            "username": username,
            "email": email,
            "password": password
        }

        # Verificar se o e-mail já existe
        response = supabase.table('usuarios').select('id').eq('email', email).execute()
        if response.data:
            flash('Email já cadastrado!', 'error')
            return render_template('criarconta.html')

        # Adicionar usuário ao banco de dados
        response = supabase.table('usuarios').insert(new_user).execute()

        if response.status_code == 201:
            return redirect(url_for('login'))

        flash('Erro ao criar conta, tente novamente.', 'error')
    
    return render_template('criarconta.html')

# Função para pegar todas as partituras
@app.route('/partituras')
def partituras():
    response = supabase.table('partituras').select('arquivo_url').execute()
    partituras = response.data if response.data else []
    return jsonify(partituras)

# Função de busca de partituras com base no estilo
@app.route('/partituras/estilo/<estilo>')
def partituras_por_estilo(estilo):
    partituras = buscar_partituras(estilo)
    return jsonify(partituras)

# Rota para renderizar a página de inserir partitura
@app.route('/inserir_partitura', methods=['GET', 'POST'])
def inserir_partitura():
    if 'nome' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        estilo_musical = request.form['estilo_musical']
        arquivo_url = request.form['arquivo_url']
        
        # Insere a nova partitura no Supabase
        new_partitura = {
            'estilo_musical': estilo_musical,
            'arquivo_url': arquivo_url
        }
        response = supabase.table('partituras').insert(new_partitura).execute()
        
        if response.status_code == 201:
            flash('Partitura inserida com sucesso!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Erro ao inserir partitura.', 'error')
    
    return render_template('inserir_partitura.html')


if __name__ == '__main__':
    app.run(debug=True)
