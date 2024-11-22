from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "armazenamento.db"))
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config['SECRET_KEY'] = 'chave'
db = SQLAlchemy(app)

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(150), nullable=False)

@app.route('/')
def home():
    return render_template('index.html', name=current_user.nickname)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nickname = request.form['nickaname']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(nickname=nickname).first()

        if usuario and usuario.senha == senha:  
            login_user(usuario)
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for('home'))
        else:
            flash("Credenciais incorretas. Tente novamente.", "danger")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    db.create_all()  # Criação das tabelas no banco de dados
    app.run(debug=True)
