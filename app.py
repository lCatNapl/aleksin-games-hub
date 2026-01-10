from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return send_file('index.html')

@app.route('/save_score', methods=['POST'])
def save_score():
    return jsonify({'ok': True})

@app.route('/top10/<path:path>')
def top10(path):
    return jsonify([])

@app.route('/user_scores/<path:path>')
def user_scores(path):
    return jsonify({'totalScore': 0})

@app.route('/status')
def status():
    return jsonify({'logged_in': False})

@app.route('/register', methods=['POST'])
def register():
    return jsonify({'ok': True})

@app.route('/login', methods=['POST'])
def login():
    return jsonify({'ok': True})

@app.errorhandler(404)
@app.errorhandler(500)
def errors(e):
    return send_file('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
