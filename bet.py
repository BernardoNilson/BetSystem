# Importando bibliotecas
from flask import Flask, render_template
# from peewee import SqliteDatabase

# Criando a aplicação Flask
app = Flask(__name__, template_folder='source/html', static_folder='source/assets')
app.config.from_object(__name__)

# Rota principal da aplicação
@app.route('/')
def hello_world():
  return render_template('index.html')


# Executando a aplicação
if __name__ == '__main__':
    app.run(debug=True)