from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
from datetime import timedelta
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from waitress import serve

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
    file_name = secure_filename(file.filename)  # Nome seguro do arquivo
    file_path_in_bucket = f"files/{file_name}"  # Caminho do arquivo no bucket

    # Fazendo upload do arquivo
    result = supabase.storage.from_(bucket_name).upload(file_path_in_bucket, file.stream.read())
    if result.get("error"):  # Corrigido o acesso a mensagens de erro
        return None, result["error"]["message"]
    else:
        return file_path_in_bucket, None

# Função para salvar o caminho do arquivo no banco de dados
def save_file_path_to_db(file_path_in_bucket):
    data = {'arquivo_path': file_path_in_bucket}

    # Salvando no banco de dados
    result = supabase.table('arquivos').insert([data]).execute()
    if result.get("error"):
        return result["error"]["message"]
    return None

# Função para gerar URL assinada com tempo de expiração personalizado
def get_signed_url(file_path_in_bucket, expiration_time=604800):
    bucket_name = 'art-music'
    signed_url_result = supabase.storage.from_(bucket_name).create_signed_url(file_path_in_bucket, expiration_time)

    if signed_url_result.get("error"):
        return None, signed_url_result["error"]["message"]
    return signed_url_result["data"]["signed_url"], None

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

@app.route('/get_signed_url', methods=['GET'])
def get_url():
    file_path_in_bucket = request.args.get('file_path')
    if not file_path_in_bucket:
        return jsonify({'error': 'file_path is required'}), 400

    expiration_time = int(request.args.get('expiration_time', 604800))
    signed_url, error = get_signed_url(file_path_in_bucket, expiration_time=expiration_time)
    if error:
        return jsonify({'error': str(error)}), 500

    return jsonify({'signed_url': signed_url}), 200

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
    partituras = buscar_partituras()

    return render_template('index.html', nome=nome, foto_perfil=foto_perfil, partituras=partituras)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/perfil')
def perfil():
    if 'nome' not in session:
        return redirect(url_for('login'))

    nome = session['nome']
    foto_perfil = session.get('foto_perfil', None)
    email = session.get('email', None)

    return render_template('perfil.html', nome=nome, foto_perfil=foto_perfil, email=email)

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

@app.route('/partituras')
def partituras():
    partituras = buscar_partituras()
    return jsonify(partituras)

@app.route('/partituras/estilo/<estilo>')
def partituras_por_estilo(estilo):
    partituras = buscar_partituras(estilo)
    return jsonify(partituras)

if __name__ == "__main__":
    app.run(debug=True)
