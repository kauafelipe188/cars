from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)

# Configuração de banco de dados aprimorada (considere usar variáveis ​​de ambiente)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meubanco.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Chave_secreta'

db = SQLAlchemy(app)

# Criação do modelo
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)
    senha_hash = db.Column(db.String(128), nullable=False)
    informacoes_adicionais = db.relationship('InformacoesAdicionais', backref='usuario', uselist=False)

    def set_senha(self, senha):
        """Define a senha com segurança usando um hash"""
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Usuario {self.id}: {self.nome} ({self.email})>"

# Criação do segundo modelo que será adicionado ao usuário assim que ele realizar o login
class InformacoesAdicionais(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    data_nascimento = db.Column(db.Date)
    rg = db.Column(db.String(20))
    cpf = db.Column(db.String(14))
    endereco = db.Column(db.Text)
    telefone = db.Column(db.String(20))
    # Não fechei ainda estou esperando dar algum erro

@app.route('/logout')
def logout():
    session.pop('usuario_logado', None)  # Remove usuário da sessão
    return redirect(url_for('index'))

@app.route('/excluir_usuario/<int:usuario_id>', methods=['GET', 'POST'])
def excluir_usuario(usuario_id):
    usuario = Usuario.query.get(usuario_id)

    if not usuario:
        flash('Usuário não encontrado.')
        return redirect(url_for('home'))

    if request.method == 'POST':
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuário excluído com sucesso!')
        return redirect(url_for('home'))

    return render_template('confirmar_exclusao.html', usuario=usuario)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/veiculos')
def veiculos():
    return render_template('veiculos.html')

@app.route('/home')
def home():
    if 'usuario_logado' not in session:  # Checando se o usuário está logado
        return redirect(url_for('login'))
    usuarios = Usuario.query.all()
    return render_template('index.html', usuarios=usuarios)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        email = request.form['email']
        senha = request.form['senha']

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.check_senha(senha):
            session['usuario_logado'] = usuario.id 
            return redirect(url_for('index'))
        else:
            flash('Email ou senha inválidos.', 'error')
            return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'GET':
        return render_template('cadastro.html')
    else:
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        # Validação do usuário (opicional:formato do email, tamanho da senha)
        if not nome or not email or not senha:
            flash('Preencha todos os campos.', 'error')
            return redirect(url_for('cadastro'))

        # Cria e salva o usuário
        usuario = Usuario(nome=nome, email=email)
        usuario.set_senha(senha)
        db.session.add(usuario)
        db.session.commit()

        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('login'))  # Se o usuário for cadastrado ele é redirecionado para o login

# Adiciona informações sobre o usuário no banco de dados 
@app.route('/informacoes_adicionais', methods=['GET', 'POST'])
def informacoes_adicionais():
    usuario = Usuario.query.get(session['usuario_logado'])

    if request.method == 'POST':
        data_nascimento = datetime.strptime(request.form.get('data_nascimento'), '%Y-%m-%d').date()
        rg = request.form.get('rg')
        cpf = request.form.get('cpf')
        endereco = request.form.get('endereco')
        telefone = request.form.get('telefone')

        # Verifique se o usuário já possui informações adicionais
        informacoes = usuario.informacoes_adicionais

        if not informacoes:
            informacoes = InformacoesAdicionais(usuario=usuario)

        informacoes.data_nascimento = data_nascimento
        informacoes.rg = rg
        informacoes.cpf = cpf
        informacoes.endereco = endereco
        informacoes.telefone = telefone

        db.session.add(informacoes)
        db.session.commit()
        flash('Informações salvas com sucesso!')
        return redirect(url_for('home'))

    return render_template('adicionar_informacoes.html')

class veiculo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), nullable=False)
    marca = db.Column(db.String(20), nullable=False)
    modelo =db.Column(db.String(20), nullable=False)
    categoria = db.Column(db.String(20), nullable=False)
    cor = db.Column(db.String(20), nullable=False)
    ano = db.Column(db.Date, nullable=False)
    preco_dia = db.Column(db.Float, nullable=False)
    disponibilidade = db.Column(db.String(20), nullable=False)
    placa = db.Column(db.String(20), unique=True, nullable=False)
    imagem = db.Column(db.String(255))

    def __repr__(self):
        return f'<veiculo> {self.nome}'

# Função para cadastrar os veiculos 
@app.route('/cad_veiculo', methods=['GET', 'POST'])
def cadastrar_veiculo():
    if request.method == 'GET':
        return render_template('cad_veiculo.html')
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        categoria = request.form.get('categoria')
        cor = request.form.get('cor')

        try:
            ano = datetime.strptime(request.form.get('ano'), '%Y-%m-%d').date()
        except ValueError:
            flash('Ano inválido. Use o formato AAAA-MM-DD')
            return render_template('cad_veiculo.html')

        preco_dia = request.form.get('preco_dia')
        disponibilidade = request.form.get('disponibilidade')
        placa = request.form.get('placa')
        imagem = request.files['imagem']

        if imagem:
            # Salvando a imagem em um diretório
            imagem_path = os.path.join('static/imagens/uploads', imagem.filename)
            imagem.save(imagem_path)
        
        # Validação (opcional, mas recomendada):
        # Verifique se a placa já existe no banco de dados
        veiculo_existente = veiculo.query.filter_by(placa=placa).first()
        if veiculo_existente:
            flash('Já existe um veículo cadastrado com essa placa.')
            return render_template('cadastrar_veiculo.html')

        novo_veiculo = veiculo(
            nome=nome,
            marca=marca,
            modelo=modelo,
            categoria=categoria,
            cor=cor,
            ano=ano,
            preco_dia=preco_dia,
            disponibilidade=disponibilidade,
            placa=placa,
            imagem=imagem_path
        )

        db.session.add(novo_veiculo)
        db.session.commit()
        flash('Veículo cadastrado com sucesso!')
        return redirect(url_for('index_logged'))  # Redireciona para a página inicial

    return render_template('cadastrar_veiculo.html')

# função para excluir os veiculos
@app.route('/deletar_veiculo/<int:veiculo_id>', methods=['GET', 'POST'])
def deletar_veiculo(veiculo_id):
    veiculo = veiculo.query.get(veiculo_id)
    if not veiculo:
        flash('Veículo não encontrado.')
        return redirect(url_for('listar_veiculos'))  # Redireciona para a lista de veículos

    if request.method == 'GET':
        return render_template('deletar_veiculo.html', veiculo=veiculo)  # Renderiza a confirmação

    if request.method == 'POST':
        db.session.delete(veiculo)
        db.session.commit()
        flash('Veículo deletado com sucesso!')
        return redirect(url_for('veiculos'))  # Redireciona para a lista de veículos

    return render_template('deletar_veiculo.html', veiculo=veiculo)  # Caso ocorra algum erro
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)

