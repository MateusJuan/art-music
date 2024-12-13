from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from datetime import timedelta
from supabase import create_client, Client
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
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
        try:
            response = supabase.table('usuarios').select('id', 'email', 'senha', 'nome').eq('email', email).execute()

            if response.data:
                usuario = response.data[0]

                if check_password_hash(usuario['senha'], senha):
                    session['nome'] = usuario['nome']
                    session['usuario_id'] = usuario['id']
                    session['email'] = usuario['email']
                    
                    flash(f"Bem-vindo, {usuario['nome']}!", "success")
                    return redirect(url_for('home'))
                else:
                    flash("Senha incorreta. Tente novamente.", "error")
            else:
                flash("Email não encontrado. Verifique e tente novamente.", "error")
        except Exception as e:
            print("Erro ao realizar login:", str(e))
            flash("Ocorreu um erro ao processar seu login. Tente novamente mais tarde.", "error")

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

@app.route('/partituras')
def partituras():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    try:
        response = supabase.table('partituras').select('*').eq('usuario_id', session['usuario_id']).execute()
        partituras = response.data if response.data else []
    except Exception as e:
        flash(f"Erro ao carregar partituras: {str(e)}", "error")
        partituras = []

    return render_template('partituras.html', partituras=partituras)

'''@app.route('/ver_pdf/<int:id>', methods=['GET'])
def ver_pdf(id):
    try:
        response = supabase.table('partituras').select('pdf_data').eq('id', id).execute()
        partitura = response.data[0] if response.data else None

        if not partitura or not partitura.get('pdf_data'):
            flash("PDF não encontrado.", "error")
            return redirect(url_for('partituras'))

        pdf_data = partitura['pdf_data']
        return Response(
            pdf_data,
            mimetype='application/pdf',
            headers={"Content-Disposition": "inline; filename=partitura.pdf"}
        )
    except Exception as e:
        flash(f"Erro ao buscar o PDF: {str(e)}", "error")
        return redirect(url_for('partituras'))'''


@app.route('/adicionar_partitura', methods=['GET', 'POST'])
def adicionar_partitura():
    if 'usuario_id' not in session:
        flash("Você precisa estar logado para adicionar uma partitura.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        estilo_musical = request.form['estilo_musical']
        
        try:
            quantidade = int(request.form.get('quantidade', 0))
        except ValueError:
            flash("Quantidade deve ser um número válido.", "error")
            return redirect(url_for('adicionar_partitura'))

        try:
            dados_partitura = {
                'nome': nome,
                'descricao': descricao,
                'estilo_musical': estilo_musical,
                'quantidade': quantidade,
                'usuario_id': session['usuario_id'],
            }

            response = supabase.table('partituras').insert([dados_partitura]).execute()

            print("Resposta do Supabase:", response)
            if response.status_code != 201:
                flash(f"Erro ao adicionar partitura: {response.error}", "error")
                return redirect(url_for('adicionar_partitura'))

            flash("Partitura adicionada com sucesso!", "success")
            return redirect(url_for('partituras'))

        except Exception as e:
            flash(f"Erro ao adicionar partitura: {str(e)}", "error")
            return redirect(url_for('adicionar_partitura'))

    return render_template('adicionar_partitura.html')



@app.route('/editar_partitura/<int:id>', methods=['GET', 'POST'])
def editar_partitura(id):
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        estilo_musical = request.form['estilo_musical']
        quantidade = request.form.get('quantidade', 0)

        try:
            supabase.table('partituras').update({
                'nome': nome,
                'descricao': descricao,
                'estilo_musical': estilo_musical,
                'quantidade': quantidade
            }).eq('id', id).execute()
            flash("Partitura atualizada com sucesso!", "success")
            return redirect(url_for('partituras'))
        except Exception as e:
            flash(f"Erro ao atualizar partitura: {str(e)}", "error")
            return redirect(url_for('editar_partitura', id=id))

    try:
        response = supabase.table('partituras').select('*').eq('id', id).execute()
        partitura = response.data[0] if response.data else None
        if not partitura:
            flash("Partitura não encontrada.", "error")
            return redirect(url_for('partituras'))
    except Exception as e:
        flash(f"Erro ao buscar partitura: {str(e)}", "error")
        return redirect(url_for('partituras'))

    return render_template('editar_partitura.html', partitura=partitura)


@app.route('/excluir_partitura/<int:id>', methods=['POST'])
def excluir_partitura(id):
    try:
        supabase.table('partituras').delete().eq('id', id).execute()
        flash("Partitura excluída com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao excluir partitura: {str(e)}", "error")

    return redirect(url_for('partituras'))


@app.route('/cifras')
def cifras():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    try:
        response = supabase.table('cifras').select('*').execute()
        cifras = response.data
        return render_template('cifras.html', cifras=cifras)
    except Exception as e:
        flash(f"Erro ao carregar cifras: {str(e)}", "error")
        return render_template('cifras.html')

@app.route('/adicionar_cifra', methods=['GET', 'POST'])
def adicionar_cifra():
    if request.method == 'POST':
        try:
            titulo = request.form['titulo']
            artista = request.form['artista']
            genero = request.form['genero']
            estilo_musical = request.form['estilo_musical']

            print(f"Dados recebidos: {titulo}, {artista}, {genero}, {estilo_musical}")

            dados_cifra = {
                'titulo': titulo,
                'artista': artista,
                'genero': genero,
                'estilo_musical': estilo_musical
            }

            response = supabase.table('cifras').insert([dados_cifra]).execute()

            if response.status_code == 200:
                flash("Cifra adicionada com sucesso!", "success")
            else:
                flash(f"Erro ao adicionar cifra: {response.error_message}", "error")
                
            return redirect(url_for('cifras'))
        
        except Exception as e:
            flash(f"Erro ao processar os dados: {str(e)}", "error")
            return redirect(url_for('adicionar_cifra'))
    
    return render_template('adicionar_cifra.html')


@app.route('/editar_cifra/<int:id>', methods=['GET', 'POST'])
def editar_cifra(id):
    if request.method == 'POST':
        estilo_musical = request.form['estilo_musical']
        arquivo_url = request.form['arquivo_url']

        try:
            supabase.table('cifras').update({
                'estilo_musical': estilo_musical,
                'arquivo_url': arquivo_url
            }).eq('id', id).execute()
            flash("Cifra atualizada com sucesso!", "success")
            return redirect(url_for('cifras'))
        except Exception as e:
            flash(f"Erro ao atualizar cifra: {str(e)}", "error")
            return redirect(url_for('editar_cifra', id=id))

    try:
        response = supabase.table('cifras').select('*').eq('id', id).execute()
        cifra = response.data[0] if response.data else None
        if not cifra:
            flash("Cifra não encontrada.", "error")
            return redirect(url_for('cifras'))
    except Exception as e:
        flash(f"Erro ao buscar cifra: {str(e)}", "error")
        return redirect(url_for('cifras'))

    return render_template('editar_cifra.html', cifra=cifra)


@app.route('/excluir_cifra/<int:id>', methods=['POST'])
def excluir_cifra(id):
    try:
        supabase.table('cifras').delete().eq('id', id).execute()
        flash("Cifra excluída com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao excluir cifra: {str(e)}", "error")

    return redirect(url_for('cifras'))


@app.route('/tablaturas')
def tablaturas():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('tablaturas.html')

@app.route('/adicionar_tablatura', methods=['GET', 'POST'])
def adicionar_tablatura():
    if request.method == 'POST':
        estilo_musical = request.form['estilo_musical']
        arquivo_url = request.form['arquivo_url']

        dados_tablatura = {
            'estilo_musical': estilo_musical,
            'arquivo_url': arquivo_url
        }

        try:
            supabase.table('tablaturas').insert([dados_tablatura]).execute()
            flash("Tablatura adicionada com sucesso!", "success")
            return redirect(url_for('tablaturas'))
        except Exception as e:
            flash(f"Erro ao adicionar tablatura: {str(e)}", "error")
            return redirect(url_for('adicionar_tablatura'))

    return render_template('adicionar_tablatura.html')

@app.route('/editar_tablatura/<int:id>', methods=['GET', 'POST'])
def editar_tablatura(id):
    if request.method == 'POST':
        estilo_musical = request.form['estilo_musical']
        arquivo_url = request.form['arquivo_url']

        try:
            supabase.table('tablaturas').update({
                'estilo_musical': estilo_musical,
                'arquivo_url': arquivo_url
            }).eq('id', id).execute()
            flash("Tablatura atualizada com sucesso!", "success")
            return redirect(url_for('tablaturas'))
        except Exception as e:
            flash(f"Erro ao atualizar tablatura: {str(e)}", "error")
            return redirect(url_for('editar_tablatura', id=id))

    try:
        response = supabase.table('tablaturas').select('*').eq('id', id).execute()
        tablatura = response.data[0] if response.data else None
        if not tablatura:
            flash("Tablatura não encontrada.", "error")
            return redirect(url_for('tablaturas'))
    except Exception as e:
        flash(f"Erro ao buscar tablatura: {str(e)}", "error")
        return redirect(url_for('tablaturas'))

    return render_template('editar_tablatura.html', tablatura=tablatura)


@app.route('/excluir_tablatura/<int:id>', methods=['POST'])
def excluir_tablatura(id):
    try:
        supabase.table('tablaturas').delete().eq('id', id).execute()
        flash("Tablatura excluída com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao excluir tablatura: {str(e)}", "error")

    return redirect(url_for('tablaturas'))


if __name__ == '__main__':
    app.run(debug=True)


#SOCORRO!😭😭