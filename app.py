from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
from datetime import timedelta
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
url = "https://zhuyytyhkmahjohqbsqd.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpodXl5dHloa21haGpvaHFic3FkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI4Nzg4NTMsImV4cCI6MjA0ODQ1NDg1M30.cyD6WqNNuGI4kPhtYSjBJ5TNennRxCnizcTrbRH-ufM"
supabase: Client = create_client(url, key)

# Função para fazer upload do arquivo
def upload_file(file):
    bucket_name = 'art-music'  # Nome do seu bucket
    file_name = file.filename  # Nome do arquivo
    file_path_in_bucket = f"files/{file_name}"  # Caminho do arquivo dentro do bucket

    # Fazendo upload do arquivo
    result = supabase.storage.from_(bucket_name).upload(file_path_in_bucket, file)
    
    if result.error:  # Checa se há um erro
        return None, result.error
    else:
        return file_path_in_bucket, None

    
# Função para salvar o caminho do arquivo no banco de dados
def save_file_path_to_db(file_path_in_bucket):
    data = {'arquivo_path': file_path_in_bucket}
    
    # Salvando no banco de dados
    result = supabase.from_('arquivos').insert([data]).execute()
    
    if result.error:  # Checa se há um erro
        return result.error
    return None


# Função para gerar URL assinada com tempo de expiração personalizado
def get_signed_url(file_path_in_bucket, expiration_time=604800):
    bucket_name = 'art-music'  # Nome do seu bucket
    
    # Gerando URL assinada válida por um determinado tempo (em segundos)
    signed_url_result = supabase.storage.from_(bucket_name).create_signed_url(file_path_in_bucket, expiration_time)
    
    if signed_url_result.error:  # Checa se há um erro
        return None, signed_url_result.error
    return signed_url_result.data['signed_url'], None


# Rota para upload de arquivos
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Realizando o upload
    file_path_in_bucket, error = upload_file(file)
    
    if error:
        return jsonify({'error': str(error)}), 500
    
    # Salvando o caminho no banco de dados
    error = save_file_path_to_db(file_path_in_bucket)

    if error:
        return jsonify({'error': str(error)}), 500
    
    return jsonify({'message': f'File {file.filename} carregado com sucesso!'}), 200

# Rota para obter a URL assinada
@app.route('/get_signed_url', methods=['GET'])
def get_url():
    file_path_in_bucket = request.args.get('file_path')
    
    if not file_path_in_bucket:
        return jsonify({'error': 'file_path is required'}), 400
    
    # Tempo de expiração configurado
    expiration_time = int(request.args.get('expiration_time', 604800))
    
    signed_url, error = get_signed_url(file_path_in_bucket, expiration_time=expiration_time)
    
    if error:
        return jsonify({'error': str(error)}), 500
    
    return jsonify({'signed_url': signed_url}), 200

# Exemplo de uso
#file_path = 'caminho/do/seu/arquivo.jpg'  # Substitua pelo caminho real do arquivo
#upload_file(file_path)

def extrair_nome_arquivo(url):
    return url.split("/")[-1]

app.jinja_env.filters['nome_arquivo'] = extrair_nome_arquivo

def buscar_partituras(estilo=None):
    query = supabase.table('partituras').select('arquivo_url')
    if estilo and estilo != 'Todos':
        query = query.eq('estilo_musical', estilo)
    
    response = query.execute()
    return response.data if response.data else []

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
                session['foto_perfil'] = usuario.get('foto_perfil', None)
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
    foto_perfil = session.get('foto_perfil', None)

    response = supabase.table('partituras').select('arquivo_url').execute()
    partituras = buscar_partituras()

    return render_template('index.html', nome=nome, foto_perfil=foto_perfil, partituras=partituras)

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

        nova_senha_hash = generate_password_hash(nova_senha, method='pbkdf2:sha256')
        supabase.table('usuarios').update({'senha': nova_senha_hash}).eq('id', session['usuario_id']).execute()

        flash("Senha alterada com sucesso!", "success")
        return redirect(url_for('perfil'))

    return render_template('mudar_senha.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/perfil')
def perfil():
    if 'nome' not in session:
        return redirect(url_for('login'))

    nome = session['nome']
    email = session['email']
    foto_perfil = session.get('foto_perfil', None)
    usuario_id = session['usuario_id'] 
    return render_template('perfil.html', nome=nome, foto_perfil=foto_perfil, email=email, id=usuario_id)


@app.route('/upload_foto', methods=['POST'])
def upload_foto():
    if 'nome' not in session:
        return redirect(url_for('login'))

    foto = request.files.get('foto_perfil')

    if foto:
        filename = secure_filename(foto.filename)
        foto_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        foto.save(foto_path)

        session['foto_perfil'] = f'uploads/{filename}'

        supabase.table('usuarios').update({'foto_perfil': f'uploads/{filename}'}).eq('id', session['usuario_id']).execute()

        flash("Foto de perfil atualizada com sucesso!", "success")
        return redirect(url_for('perfil'))

    flash("Falha ao enviar a foto.", "error")
    return redirect(url_for('perfil'))

@app.route('/criar_conta', methods=['GET', 'POST'])
def criar_conta():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        password = request.form.get('password')

        if not nome or not email or not password:
            flash('Todos os campos são obrigatórios!', 'error')
            return render_template('criarconta.html')

        response = supabase.table('usuarios').select('id').eq('email', email).execute()
        if response.data:
            flash('Email já cadastrado!', 'error')
            return render_template('criarconta.html')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = {
            'nome': nome,
            'email': email,
            'senha': hashed_password
        }
        response = supabase.table('usuarios').insert(new_user).execute()

        if response.status_code != 200:
            flash(f'Erro ao criar conta. Tente novamente. {response.data}', 'error')
        else:
            flash('Conta criada com sucesso!', 'success')
            return redirect(url_for('login'))

    return render_template('criarconta.html')


@app.route('/partituras')
def partituras():
    partituras = buscar_partituras()
    return jsonify(partituras)

@app.route('/partituras/estilo/<estilo>') 
def partituras_por_estilo(estilo):
    partituras = buscar_partituras(estilo)
    return jsonify(partituras)

@app.route('/inserir_partitura', methods=['GET', 'POST'])
def inserir_partitura():
    if 'nome' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        estilo_musical = request.form['estilo_musical']
        arquivo_pdf = request.files['arquivo_pdf']

        if arquivo_pdf:
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            filename = secure_filename(arquivo_pdf.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            arquivo_pdf.save(file_path)

            file_url = url_for('static', filename=f'PDF_PARTITURAS/{filename}')
            
            new_partitura = {
                'estilo_musical': estilo_musical,
                'arquivo_url': file_url
            }

            response = supabase.table('partituras').insert(new_partitura).execute()

            if response.data and len(response.data) > 0:
                flash('Partitura inserida com sucesso!', 'success')
                return redirect(url_for('home'))
            else:
                flash(f"Erro ao inserir partitura: {response.error_message or 'Erro desconhecido'}", 'error')

        else:
            flash('Nenhum arquivo foi enviado.', 'error')

    return render_template('inserir_partitura.html')

if __name__ == "__main__":
    app.run(debug=True)