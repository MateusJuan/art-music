from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Mcmidori3208@localhost/art_music'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def init_db():
    with app.app_context():
        sql = """
        CREATE DATABASE IF NOT EXISTS art_music;
        USE art_music;
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            password VARCHAR(255) NOT NULL
        );
        """
        db.session.execute(text(sql))
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/criarconta')
def criar_conta():
    return render_template('criarconta.html')

if __name__ == '__main__':
    init_db()  
    app.run(debug=True)
