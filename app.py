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

# Rota para o login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        response = supabase.table('usuarios').select('id', 'email', 'senha', 'nome', 'foto_perfil').eq('email', email).execute()

        if response.data:
            usuario = response.data[0]
            if check_password_hash(usuario['senha'], senha):
                session['nome'] = usuario['nome']
                session['usuario_id'] = usuario['id']
                session['email'] = usuario['email']
                session['foto_perfil'] = usuario.get('foto_perfil', None)  # Armazenar foto de perfil se houver
                return redirect(url_for('home'))
            else:
                flash("Senha incorreta.", "error")
        else:
            flash("Email não encontrado.", "error")
    
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
    email = session.get('email', None)

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

        # Atualizar a foto de perfil no banco de dados
        supabase.table('usuarios').update({'foto_perfil': f'uploads/{filename}'}).eq('id', session['usuario_id']).execute()

        flash("Foto de perfil atualizada com sucesso!", "success")
        return redirect(url_for('perfil'))

    flash("Falha ao enviar a foto.", "error")
    return redirect(url_for('perfil'))

# Função para criar conta
@app.route('/criar_conta', methods=['GET', 'POST'])
def criar_conta():
    if request.method == 'POST':
        # Verifique se os campos existem no formulário
        nome = request.form.get('nome')  # Usando get() para evitar KeyError
        email = request.form.get('email')
        password = request.form.get('password')

        if not nome or not email or not password:
            flash('Todos os campos são obrigatórios!', 'error')
            return render_template('criarconta.html')

        # Processar a senha e criar o novo usuário
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Salvar no banco de dados ou fazer outra lógica aqui
        # Exemplo de resposta (não funcional sem o banco):
        # response = supabase.table('usuarios').insert({"nome": nome, "email": email, "senha": hashed_password}).execute()

        flash('Conta criada com sucesso!', 'success')
        return redirect(url_for('login'))

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
