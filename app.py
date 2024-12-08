from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from datetime import timedelta
from supabase import create_client, Client
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

url = os.getenv("SUPABASE_URL", "https://zhuyytyhkmahjohqbsqd.supabase.co")
key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpodXl5dHloa21haGpvaHFic3FkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI4Nzg4NTMsImV4cCI6MjA0ODQ1NDg1M30.cyD6WqNNuGI4kPhtYSjBJ5TNennRxCnizcTrbRH-ufM")
supabase: Client = create_client(url, key)

@app.before_request
def verificar_login():
    if 'nome' not in session and request.endpoint not in ['login', 'criar_conta']:
        return redirect(url_for('login'))

@app.route('/criar_conta', methods=['GET', 'POST'])
def criar_conta():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        senha_confirmacao = request.form['senha_confirmacao']

        if senha != senha_confirmacao:
            flash("As senhas não coincidem.", "error")
            return redirect(url_for('criar_conta'))

        response = supabase.table('usuarios').select('id').eq('email', email).execute()
        if response.data:
            flash("Este email já está registrado.", "error")
            return redirect(url_for('criar_conta'))

        senha_hash = generate_password_hash(senha)

        data = {'nome': nome, 'email': email, 'senha': senha_hash}
        try:
            supabase.table('usuarios').insert([data]).execute()
            flash("Conta criada com sucesso!", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Erro ao criar conta: {str(e)}", "error")
            return redirect(url_for('criar_conta'))

    return render_template('criarconta.html')

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
    return render_template('index.html', nome=nome)

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

@app.route('/inserir_partitura', methods=['GET', 'POST'])
def inserir_partitura():
    if request.method == 'POST':
        titulo = request.form['titulo']
        compositor = request.form['compositor']
        genero = request.form['genero']

        dados_partitura = {
            'titulo': titulo,
            'compositor': compositor,
            'genero': genero,
            'usuario_id': session['usuario_id'],
        }

        try:
            supabase.table('partituras').insert([dados_partitura]).execute()
            flash("Partitura inserida com sucesso!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"Erro ao inserir partitura: {str(e)}", "error")
            return redirect(url_for('inserir_partitura'))

    return render_template('inserir_partitura.html')

if __name__ == '__main__':
    app.run(debug=True)
