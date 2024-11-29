from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
from datetime import timedelta
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)

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

@app.route('/api/partituras', methods=['GET'])
def get_partituras():
    response = supabase.table('partituras').select('id', 'estilo_musical', 'arquivo_url').execute()
    partituras = response.data
    return jsonify(partituras)

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

        # Verificar se todos os campos necessários foram preenchidos
        if not nome or not email or not senha:
            return "Todos os campos são obrigatórios."

        # Gerar o hash da senha para armazenar de forma segura
        hashed_senha = generate_password_hash(senha)

        # Criar conta no Supabase com o novo formato de parâmetros
        response = supabase.auth.sign_up({
            'email': email,
            'password': senha
        })

        if response.user is None:
            return f"Erro ao criar conta: {response.error['message']}"

        # Salvar o nome do usuário e a senha (hash) na tabela customizada no Supabase
        supabase.table('usuarios').insert({
            'email': email,
            'nome': nome,
            'senha': hashed_senha  # Armazenar a senha como hash
        }).execute()

        return render_template('aguarde_confirmacao.html')  # Página que diz ao usuário para confirmar o email

    return render_template('criarconta.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        # Tentar fazer login
        response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': senha
        })

        # Verificar se o login falhou
        if response.user is None:
            # Checar se o erro é relacionado ao email não confirmado
            if response.error and response.error.get('message') == 'Email not confirmed':
                return redirect(url_for('reenviar_confirmacao'))

            return f"Login falhou. Erro: {response.error['message']}"

        # Recuperar os dados do usuário
        user = supabase.table('usuarios').select('nome', 'foto_perfil').eq('email', email).single().execute()

        if user.data:
            session.permanent = True
            session['email'] = email
            session['nome'] = user.data['nome']
            session['foto_perfil'] = user.data['foto_perfil']
            return redirect(url_for('perfil'))
        else:
            return "Usuário não encontrado."

    return render_template('login.html')

@app.route('/reenviar_confirmacao', methods=['POST'])
def reenviar_confirmacao():
    email = session.get('email')

    if not email:
        return redirect(url_for('login'))

    response = supabase.auth.api.resend_confirmation_email(email)

    if response.error:
        return f"Erro ao reenviar o email de confirmação: {response.error['message']}"

    return "Email de confirmação reenviado com sucesso! Verifique sua caixa de entrada."

@app.route('/perfil')
def perfil():
    if 'email' in session:
        email = session['email']
        user_data = supabase.table('usuarios').select('nome', 'email', 'foto_perfil').eq('email', email).single().execute()

        if user_data.data:
            return render_template('perfil.html', nome=user_data.data['nome'], email=user_data.data['email'], foto_perfil=user_data.data['foto_perfil'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('nome', None)
    session.pop('foto_perfil', None)
    supabase.auth.sign_out()
    return redirect(url_for('login'))

@app.route('/apagarconta', methods=['GET', 'POST'])
def apagar_conta():
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        email = session['email']

        # Apagar a conta do Supabase
        response = supabase.auth.api.delete_user(email)

        # Verificar se houve erro
        if response.error:
            return f"Erro ao apagar a conta: {response.error['message']}"

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

        # Atualizar a foto de perfil do usuário no Supabase
        email = session['email']
        supabase.table('usuarios').update({
            'foto_perfil': f'uploads/{filename}'
        }).eq('email', email).execute()

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
