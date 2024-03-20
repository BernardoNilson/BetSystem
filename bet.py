# Importando bibliotecas
from flask import Flask, redirect, render_template, g, request, url_for
from peewee import *
import random
from collections import defaultdict

# Definições
DATABASE = 'bet.db'
DEBUG = True

# Criando a aplicação Flask
app = Flask(__name__, template_folder='source/html',
            static_folder='source/assets')
app.config.from_object(__name__)

# Definindo o banco de dados SQLite
database = SqliteDatabase(DATABASE, pragmas={'foreign_keys': 1})


class BaseModel(Model):
    '''Criação do modelo base da tabela'''
    class Meta:
        database = database


class Bet(BaseModel):
    '''Criação do modelo da tabela de apostas'''
    register = IntegerField(unique=True)
    name = CharField()
    cpf = CharField(11)
    bet = CharField()

def restart_database():
    drop_table()
    create_table()

def create_table():
    '''Criação da tabela do BD'''
    with database:
        database.create_tables([Bet])


def drop_table():
    '''Exclusão da tabela'''
    with database:
        database.drop_tables([Bet])


@app.before_request
def before_request():
    '''Estabelecendo a conexão com o banco de dados'''
    g.db = database
    g.db.connect()


@app.after_request
def after_request(response):
    '''Fechando a conexão com o banco de dados'''
    g.db.close()
    return response


@app.route('/')
def homepage():
    '''Rota principal da aplicação'''
    restart_database()
    return render_template('home.html')


@app.route('/start', methods=['GET', 'POST'])
def start():
    '''Inicio da Fase de Sorteio do programa'''
    message = "A fase de apostas começou. Você deve registrar novas apostas."
    return render_template('home.html', message=message)


@app.route('/start/bet', methods=['GET', 'POST'])
def bet():
    '''Registro de novas apostas'''
    form = request.form
    warning = None
    message = 'Você deve registrar novamente.'

    if request.method == 'POST':
        name = form['name']
        cpf = form['cpf']
        bet = form['bet']
        # Opção 'surpresinha'
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


@app.route('/list')
def list():
    '''Listar todas as apostas'''
    bets_list = Bet.select().order_by(Bet.register)
    return render_template('list.html', list=bets_list)


@app.route('/end')
def end():
    '''Finalizar Fase de Apostas e iniciar Fase de Apuração dos resultados'''
    message = None

    # Seleciona todas as linhas do nosso BD com as colunas de nome e aposta
    bets = Bet.select(Bet.name, Bet.bet)

    bets_list = []
    # Para cada linha, adicione as apostas transformadas para lista de inteiros
    for bet in bets:
        bets_list.append([int(num) for num in bet.bet.split()])

    # Lista de números sorteados
    drawn_numbers = draw_five_numbers()

    # Quantas rodadas de sorteio foram realizadas
    rounds = 0

    # Limite de rodadas
    max_rounds = 25

    # Lista de apostas vencedoras ou mensagem de que não houve vencedores
    winners_list = []

    # Enquanto não tiver nenhum ganhador e não tiver atingido o limite de rounds
    while not winners_list and rounds < max_rounds:
        winners_list = verify_winner(drawn_numbers, bets_list)
        rounds += 1
        if not winners_list:
            add_draw_number(drawn_numbers)

    # Seleciona todos os nomes com base em quem acertou a aposta
    winners_list_str = []
    for list in winners_list:
        winner_str = " ".join(map(str, list))
        winners_list_str.append(winner_str)
    winners_names = Bet.select(Bet.name, Bet.bet).where(
        Bet.bet.in_(winners_list_str))

    # Quantidade de apostas vencedoras
    winners_count = len(winners_list)

    # Lista de todos os números apostados, considerando todas as apostas, ordenada do número mais escolhido ao menos escolhido. Ao lado de cada número deverá haver a quantidade de apostas que contêm aquele número, como  no  exemplo  a  seguir:
    num_frequency = count_numbers_frequency(bets_list)

    # Reinicia o banco de dados
    restart_database()

    if not winners_list:
        message = "Nenhuma aposta foi sorteada. Tente novamente!"

    return render_template('end.html', drawn=drawn_numbers,
                           rounds=rounds, winners_count=winners_count,
                           winners=winners_list, num_frequency=num_frequency, message=message, winners_names=winners_names)


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
    """Recebe uma lista e adiciona mais um número sorteado nessa lista. Só atua sobre listas com tamanho inferior a 30."""

    # Podemos adicionar até 25 novos números sorteados
    if (len(drawn_numbers) >= 30):
        raise NotImplementedError

    num = random.randint(1, 50)
    # Para não repetir nenhum número:
    while num in drawn_numbers:
        num = random.randint(1, 50)
    drawn_numbers.append(num)


def verify_fields(name, cpf, bet):
    """
    Verifica se o nome, CPF e aposta são válidos.\n
    Nome -> precisa ser maior que 3 caracteres\n
    CPF -> precisa ser 11 digitos\n
    Aposta -> Precisa ser 5 números separados por espaço (str)
    """

    warning = None

    # Validação do nome (mínimo 3 caracteres)
    if len(name) < 3 or len(name) > 60:
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
    A função verifica quais apostas da lista de apostas acertaram pelo menos 5 números entre os números sorteados.\n
    A função espera uma lista 'bets', que possui listas de inteiros
    '''

    winners = []
    # Para cada aposta, incrementa o contador se os números da aposta estiverem entre os sorteados
    for list in bets:
        count = 0
        for num in list:
            if num in drawn:
                count += 1
        if count >= 5:
            winners.append(list)

    return winners


def count_numbers_frequency(bets):
    '''
    A função retorna uma tupla ordenada contendo os pares chave/valor
    '''

    # Usei o defaultdict pois traz algumas simplificações e deixa o código mais legível
    counts = defaultdict(int)

    # Para cada lista de apostas dentro da lista, incrementa sua frequência no dicionário
    for bet in bets:
        for num in bet:
            counts[num] += 1

    # Ordena o dicionário por contagem em ordem decrescente
            #  converte chave/valor, use frequência para ordem, configura ordem inversa
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)


# Uso pelo BD
register = 999


def get_register():
    """Retorna o registro disponível para ser usado no BD e incrementa o valor na variável global."""
    global register
    register += 1
    return register


# Executando a aplicação
if __name__ == '__main__':
    restart_database()
    app.run(debug=True)
