# Importando bibliotecas
from flask import Flask, redirect, render_template, g, request, url_for
from peewee import *
import random

DATABASE = 'bet.db'
DEBUG = True

# Criando a aplicação Flask
app = Flask(__name__, template_folder='source/html',
            static_folder='source/assets')
app.config.from_object(__name__)

# Definindo o banco de dados SQLite
database = SqliteDatabase(DATABASE, pragmas={'foreign_keys': 1})

# Criação do modelo base da tabela


class BaseModel(Model):
    class Meta:
        database = database

# Criação do modelo da tabela de apostas


class Bet(BaseModel):
    register = IntegerField(unique=True)
    name = CharField()
    cpf = CharField(11)
    bet = CharField()

# Criação da tabela


def create_table():
    with database:
        database.create_tables([Bet])

# Exclusão da tabela


def drop_table():
    with database:
        database.drop_tables([Bet])

# Estabelecendo a conexão com o banco de dados


@app.before_request
def before_request():
    g.db = database
    g.db.connect()

# Fechando a conexão com o banco de dados


@app.after_request
def after_request(response):
    g.db.close()
    return response

# Rota principal da aplicação
@app.route('/')
def homepage():
    drop_table()
    create_table()
    return render_template('home.html')

# Inicio do programa


@app.route('/start', methods=['GET', 'POST'])
def start():
    message = "A fase de apostas começou. Você deve registrar novas apostas."
    return render_template('home.html', message=message)

# Registro de novas apostas


@app.route('/start/bet', methods=['GET', 'POST'])
def bet():
    form = request.form
    warning = None
    message = 'Você deve registrar novamente.'

    if request.method == 'POST':
        name = form['name']
        cpf = form['cpf']
        bet = form['bet']

        warning = verify_fields(name, cpf, bet)
        if warning:
            return render_template('home.html', message=message, warning=warning)
        
        # Se tudo estiver certo, salva no banco de dados
        bet = Bet(register=get_register(register), name=name, cpf=cpf, bet=bet)
        bet.save()

        message = "Aposta registrada com sucesso!"
        return render_template('home.html', message=message)

    return render_template('bet.html')

# Listar todas as apostas


@app.route('/list')
def list():

    return render_template('bet.html')

# Finalizar apostas e iniciar apuração dos resultados


@app.route('/end')
def end():
    return render_template('bet.html')

# Premiação dos vencedores


@app.route('/prize')
def prize():
    return render_template('bet.html')


def draw_five_numbers():
    """Sorteia 5 números e retorna uma lista."""
    drawn_numbers = []
    for _ in range(5):
        num = random.randint(1, 50)
        while num in drawn_numbers:
            num = random.randint(1, 50)
        drawn_numbers.append(num)
    return drawn_numbers


def add_draw_number(drawn_numbers):
    """Recebe uma lista e adiciona mais um número sorteado."""

    # Podemos adicionar até 25 novos números sorteados
    if (drawn_numbers.length >= 30):
        raise NotImplementedError

    num = random.randint(1, 50)
    while num in drawn_numbers:
        num = random.randint(1, 50)
    drawn_numbers.append(num)

def verify_fields(name, cpf, bet):
    warning = None

    # Validação do nome
    if len(name) < 3:
        warning = "Nome precisa ter, no mínimo, 3 caracteres!"
    else:
        # Validação do CPF
        if not cpf.isdigit() or len(cpf) != 11:
            warning = "CPF inválido! Digite apenas números e com 11 dígitos."
        else:
            # Validação da aposta
            bet_numbers = [int(x) for x in bet.split()]
            invalid = any(int(x) < 1 or int(x) > 50 for x in bet_numbers)

            print(bet_numbers)
            print(len(bet_numbers) != 5)
            print(invalid)

            if len(bet_numbers) != 5 or invalid:
                warning = "Aposta inválida! Digite 5 números entre 1 e 50 separados por espaços."

    return warning

register = 1000
def get_register(register):
    '''Retorna o registro disponível'''
    register += 1
    return register

# Executando a aplicação
if __name__ == '__main__':
    create_table()
    # drop_table()
    app.run(debug=True)
