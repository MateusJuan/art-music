from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    dados = {
        'tipos': ['Todos', 'Gospel/Religioso', 'Rock', 'Pagode', 'Samba', 'Clássica'],
        'conteudos': {
            'gospel': [
                {'banda': 'Vocal Livre', 'qtd': 10},
                {'banda': 'Novo Tom', 'qtd': 15}
            ],
            'rock': [
                {'banda': 'AC/DC', 'qtd': 20},
                {'banda': 'Queen', 'qtd': 18}
            ]
        },
        'nome': 'Usuário Logado' 
    }
    return render_template('index.html', dados=dados)

@app.route('/cifras')
def cifras():
    cifras_por_genero = {
        'Rock': [
            {'banda': 'AC/DC', 'quantidade': 20},
            {'banda': 'Queen', 'quantidade': 18}
        ],
        'Gospel': [
            {'banda': 'Vocal Livre', 'quantidade': 10},
            {'banda': 'Novo Tom', 'quantidade': 15}
        ]
    }
    return render_template('cifras.html', cifras_por_genero=cifras_por_genero)

@app.route('/criarconta')
def criarconta():
    return render_template('criarconta.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/gospel')
def gospel():
    dados = {
        'tipos': ['Todos', 'Gospel/Religioso', 'Rock', 'Pagode', 'Samba', 'Clássica'],
        'conteudos': {
            'gospel': [
                {'banda': 'Vocal Livre', 'qtd': 10},
                {'banda': 'Novo Tom', 'qtd': 15}
            ]
        }
    }
    return render_template('gospel.html', dados=dados)

@app.route('/rock')
def rock():
    dados = {
        'tipos': ['Todos', 'Gospel/Religioso', 'Rock', 'Pagode', 'Samba', 'Clássica'],
        'conteudos': {
            'rock': [
                {'banda': 'AC/DC', 'qtd': 20},
                {'banda': 'Queen', 'qtd': 18}
            ]
        }
    }
    return render_template('rock.html', dados=dados)

if __name__ == '__main__':
    app.run(debug=True)
