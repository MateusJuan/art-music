from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cifras.db'
app.config['SECRET_KEY'] = 'minha_chave_secreta'
db = SQLAlchemy(app)

class Cifra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    genero = db.Column(db.String(50), nullable=False)
    banda = db.Column(db.String(150), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Cifra {self.banda}>"

@app.route('/cifras')
def cifras():
    cifras = Cifra.query.all()

    cifras_por_genero = {}
    for cifra in cifras:
        if cifra.genero not in cifras_por_genero:
            cifras_por_genero[cifra.genero] = []
        cifras_por_genero[cifra.genero].append(cifra)

    return render_template('cifras.html', cifras_por_genero=cifras_por_genero)

@app.route('/adicionar_cifra', methods=['GET', 'POST'])
def adicionar_cifra():
    if request.method == 'POST':
        genero = request.form['genero']
        banda = request.form['banda']
        quantidade = int(request.form['quantidade'])
        
        nova_cifra = Cifra(genero=genero, banda=banda, quantidade=quantidade)
        db.session.add(nova_cifra)
        db.session.commit()

        flash("Cifra adicionada com sucesso!", "success")
        return redirect(url_for('cifras'))

    return render_template('adicionar_cifra.html')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
