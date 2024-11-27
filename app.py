from flask import Flask, render_template, request, redirect, url_for, session
from models import init_db, inserir_usuario, buscar_usuario, deletar_usuario
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

init_db()

@app.route('/')
def home():
    if 'nome' not in session:
        return redirect(url_for('login'))  # Redireciona para a página de login se não estiver logado
    
    nome = session['nome']
    return render_template('index.html', nome=nome)

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

        usuario = buscar_usuario(email, senha)
        if usuario:
            session['nome'] = usuario['nome']
            session['email'] = usuario['email']
            return redirect(url_for('home'))
        else:
            return render_template('login.html', erro="Login inválido. Verifique suas credenciais.")
    return render_template('login.html')

@app.route('/perfil')
def perfil():
    # Verifica se o usuário está logado
    if 'nome' not in session:
        return redirect(url_for('login'))
    
    nome = session['nome']
    email = session['email']

    # Aqui você pode adicionar mais informações do usuário se necessário
    return render_template('perfil.html', nome=nome, email=email)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

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

if __name__ == '__main__':
    app.run(debug=True)
