from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import timedelta
from models import init_db, inserir_usuario, deletar_usuario

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()

@app.route('/')
def home():
    if 'nome' not in session:
        return redirect(url_for('login'))
    
    nome = session['nome']
    foto_perfil = session.get('foto_perfil', None)
    return render_template('index.html', nome=nome, foto_perfil=foto_perfil)

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

if __name__ == '__main__':
    app.run(debug=True)
