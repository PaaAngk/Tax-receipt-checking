from flask import Flask, request, jsonify, send_from_directory 
import os
app = Flask(__name__)
import database as db

@app.route("/")
def hello_world():
    users = db.get_document_search('ggWP', 'type1', '10-12-2022')
    return str(users)

@app.route('/get-document', methods=['POST'])
def documents():
    data = request.get_json()
    search = db.get_document_search(data["doc_number"], data["doc_type"], data["doc_date"])
    return jsonify(search)

@app.route('/upload-document/<name>')
def download_file(name):
    return send_from_directory(os.getcwd()+"/tempDir/", name)

