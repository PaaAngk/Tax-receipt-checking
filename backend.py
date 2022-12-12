from flask import Flask

app = Flask(__name__)
import database as db

@app.route("/")
def hello_world():
    users = db.get_document_search('ggWP', 'type1', '10-12-2022')
    return str(users)