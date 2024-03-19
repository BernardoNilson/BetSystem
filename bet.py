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
        if not bet:
            bet = " ".join(map(str, draw_five_numbers()))
        
        warning = verify_fields(name, cpf, bet)
        if warning:
            return render_template('home.html', message=message, warning=warning)
        
        # Se tudo estiver certo, salva no banco de dados
        bet = Bet(register=get_register(), name=name, cpf=cpf, bet=bet)
        bet.save()

        message = "Aposta registrada com sucesso!"
        return render_template('home.html', message=message)

    return render_template('bet.html')

# Listar todas as apostas


@app.route('/list')
def list():
    bets_list = Bet.select().order_by(Bet.register)
    return render_template('list.html', list=bets_list)

# Finalizar apostas e iniciar apuração dos resultados


@app.route('/end')
def end():
    bets_list = []
    # Seleciona todas as linhas do nosso BD com as colunas de nome e aposta
    bets = Bet.select(Bet.name, Bet.bet)
    # Para cada linha, adicione as apostas transformadas para lista de inteiros  
    for bet in bets:
        bets_list.append([int(num) for num in bet.bet.split()])
    print(bets_list)
    
    # Lista de números sorteados 
    drawn_numbers = draw_five_numbers()

    # Quantas rodadas de sorteio foram realizadas
    rounds = 0
    # Limite de rodadas
    max_rounds = 25

    # Quantidade de apostas vencedoras
    winning_bets = 0

    # Lista de apostas vencedoras ou mensagem de que não houve vencedores 
    winners_list = []

    # Lista de todos os números apostados, considerando todas as apostas, ordenada do número mais escolhido ao menos escolhido. Ao lado de cada número deverá haver a quantidade de apostas que contêm aquele número, como  no  exemplo  a  seguir:
    # ...
    
    # Enquanto não tiver nenhum ganhador e não tiver atingido o limite de rounds
    while not winners_list and rounds < max_rounds:
        winners_list = verify_winner(drawn_numbers, bets_list)
        rounds += 1
        add_draw_number(drawn_numbers)
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
    if (len(drawn_numbers) >= 30):
        raise NotImplementedError

    num = random.randint(1, 50)
    while num in drawn_numbers:
        num = random.randint(1, 50)
    drawn_numbers.append(num)

def verify_fields(name, cpf, bet):
  """Verifica se o nome, CPF e aposta são válidos."""

  warning = None

  # Validação do nome (mínimo 3 caracteres)
  if len(name) < 3:
    warning = "Nome precisa ter, no mínimo, 3 caracteres!"
    return warning

  # Validação do CPF (apenas números e 11 dígitos)
  if not cpf.isdigit() or len(cpf) != 11:
    warning = "CPF inválido! Digite apenas números e com 11 dígitos."
    return warning

  # Validação da aposta (5 números entre 1 e 50, sem repetições)
  try:
    bet_numbers = [int(num) for num in bet.split()]
    if len(bet_numbers) != 5 or min(bet_numbers) < 1 or max(bet_numbers) > 50 or len(set(bet_numbers)) != 5:
        raise ValueError
  except ValueError:
    warning = "Aposta inválida! Digite 5 números diferentes entre 1 e 50 separados por espaços."

  return warning

def verify_winner(drawn, bets):
    '''
    A função verifica se todos os números da lista 'drawn' estão na lista de apostas.
    A função espera uma lista de 'bets' com listas internas
    '''
    
    winners = []
    for list in bets:
        count = 0
        for num in list:
            if num in drawn: count += 1
        if count >= 5: winners.append(list)

    return winners

register = 999
def get_register():
  """Retorna o registro disponível e incrementa o valor global."""
  # Declara que register é uma variável global
  global register  
  register += 1
  return register

# Executando a aplicação
if __name__ == '__main__':
    drop_table()
    create_table()
    app.run(debug=True)
