from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
from datetime import timedelta
from supabase import create_client, Client
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

# Carregar variáveis de ambiente de um arquivo .env
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Carregar as variáveis de ambiente
url = os.getenv("SUPABASE_URL", "https://zhuyytyhkmahjohqbsqd.supabase.co")
key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpodXl5dHloa21haGpvaHFic3FkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI4Nzg4NTMsImV4cCI6MjA0ODQ1NDg1M30.cyD6WqNNuGI4kPhtYSjBJ5TNennRxCnizcTrbRH-ufM")
supabase: Client = create_client(url, key)

# Função para verificar se o usuário está logado antes de cada requisição
@app.before_request
def verificar_login():
    # Se o usuário não estiver logado, redireciona para o login, exceto nas rotas 'login' e 'criar_conta'
    if 'nome' not in session and request.endpoint not in ['login', 'criar_conta']:
        return redirect(url_for('login'))

@app.route('/criar_conta', methods=['GET', 'POST'])
def criar_conta():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        senha_confirmacao = request.form['senha_confirmacao']

        # Verifique se as senhas coincidem
        if senha != senha_confirmacao:
            flash("As senhas não coincidem.", "error")
            return redirect(url_for('criar_conta'))

        # Verifique se o email já existe
        response = supabase.table('usuarios').select('id').eq('email', email).execute()
        if response.data:
            flash("Este email já está registrado.", "error")
            return redirect(url_for('criar_conta'))

        # Criptografe a senha
        senha_hash = generate_password_hash(senha)

        # Salve o usuário no banco de dados
        data = {
            'nome': nome,
            'email': email,
            'senha': senha_hash
        }

        try:
            supabase.table('usuarios').insert([data]).execute()
            flash("Conta criada com sucesso!", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Erro ao criar conta: {str(e)}", "error")
            return redirect(url_for('criar_conta'))

    return render_template('criarconta.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Implementar upload do arquivo aqui...

    return jsonify({'message': f'File {file.filename} carregado com sucesso!'}), 200

@app.route('/partituras/<estilo>')
def partituras_por_estilo(estilo):
    partituras = buscar_partituras(estilo=estilo)
    return render_template('partituras.html', partituras=partituras, estilo=estilo)

@app.route('/inserir_partitura', methods=['GET', 'POST'])
def inserir_partitura():
    if 'nome' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        estilo_musical = request.form.get('estilo_musical')
        file = request.files.get('arquivo_pdf')

        if not file:
            flash("Nenhum arquivo selecionado.", "error")
            return redirect(url_for('inserir_partitura'))

        if not estilo_musical:
            flash("O estilo musical é obrigatório.", "error")
            return redirect(url_for('inserir_partitura'))

        # Realiza o upload do arquivo para o Supabase Storage
        bucket = supabase.storage.from_('art-music')
        file_path_in_bucket = f"partituras/{file.filename}"

        try:
            bucket.upload(file_path_in_bucket, file)
            # Salvar o caminho do arquivo e o estilo musical no banco de dados
            data = {
                'arquivo_pdf': file_path_in_bucket,
                'estilo_musical': estilo_musical
            }

            response = supabase.table('partituras').insert([data]).execute()
            flash("Partitura inserida com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao inserir partitura: {str(e)}", "error")

        return redirect(url_for('home'))

    return render_template('inserir_partitura.html')

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
                session['email'] = usuario['email']
                return redirect(url_for('home'))
            else:
                flash("Senha incorreta.", "error")
        else:
            flash("Email não encontrado.", "error")
    
    return render_template('login.html')

@app.route('/')
def home():
    if 'nome' not in session:
        return redirect(url_for('login'))

    nome = session['nome']

    partituras = buscar_partituras()  # Agora retornando partituras com URLs assinadas

    return render_template('index.html', nome=nome, partituras=partituras)

@app.route('/trocarSenha', methods=['GET', 'POST'])
def trocarSenha():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        senha_atual = request.form['senha_atual']
        nova_senha = request.form['nova_senha']
        confirmar_nova_senha = request.form['confirmar_nova_senha']

        response = supabase.table('usuarios').select('senha').eq('id', session['usuario_id']).execute()

        if not response.data:
            flash("Erro ao localizar o usuário.", "error")
            return redirect(url_for('trocarSenha'))

        senha_armazenada = response.data[0]['senha']

        if not check_password_hash(senha_armazenada, senha_atual):
            flash("Senha atual incorreta.", "error")
            return redirect(url_for('trocarSenha'))

        if nova_senha != confirmar_nova_senha:
            flash("A nova senha e a confirmação não coincidem.", "error")
            return redirect(url_for('trocarSenha'))

        if not is_password_strong(nova_senha):
            flash("A nova senha não atende aos critérios de segurança.", "error")
            return redirect(url_for('trocarSenha'))

        nova_senha_hash = generate_password_hash(nova_senha, method='pbkdf2:sha256')
        supabase.table('usuarios').update({'senha': nova_senha_hash}).eq('id', session['usuario_id']).execute()

        flash("Senha alterada com sucesso!", "success")
        return redirect(url_for('perfil'))

    return render_template('mudar_senha.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Você foi desconectado com sucesso.", "success")
    return redirect(url_for('login'))

@app.route('/perfil')
def perfil():
    if 'nome' not in session:
        return redirect(url_for('login'))

    nome = session['nome']
    email = session['email']
    usuario_id = session['usuario_id'] 
    return render_template('perfil.html', nome=nome, email=email, id=usuario_id)

def is_password_strong(password):
    return bool(re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)[A-Za-z\d]{8,}$', password))

def buscar_partituras(estilo=None):
    try:
        query = supabase.table('partituras').select('arquivo_pdf')
        if estilo and estilo != 'Todos':
            query = query.eq('estilo_musical', estilo)
        
        response = query.execute()
        partituras = response.data if response.data else []

        for partitura in partituras:
            arquivo_url = partitura['arquivo_pdf']
            signed_url, error = get_signed_url(arquivo_url)
            if signed_url:
                partitura['arquivo_pdf'] = signed_url
            else:
                partitura['arquivo_pdf'] = None  # Em caso de erro ao gerar a URL assinada
        return partituras
    except Exception as e:
        return {'error': str(e)}

def get_signed_url(file_path_in_bucket, expiration_time=604800):
    bucket_name = 'art-music'

    signed_url_result = supabase.storage.from_(bucket_name).create_signed_url(file_path_in_bucket, expiration_time)
    
    if signed_url_result.error:
        return None, signed_url_result.error
    return signed_url_result.data['signed_url'], None

if __name__ == '__main__':
    app.run(debug=True)
