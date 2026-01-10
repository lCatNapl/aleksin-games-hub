from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ✅ ГЛАВНЫЙ РОУТ - ОТСУТСТВОВАЛ!
@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')

# ✅ ВСЕ AJAX РОУТЫ
@app.route('/save_score', methods=['POST'])
def save_score():
    return jsonify({'ok': True})

@app.route('/top10/<game>/<diff>')
@app.route('/top10/<game>/<diff>/')
def top10(game, diff):
    return jsonify([])

@app.route('/user_scores/<username>')
def user_scores(username):
    return jsonify({
        'bestSnakeEasy': 0, 'bestSnakeMedium': 0, 'bestSnakeHard': 0,
        'bestGuess1000': 0, 'bestGuess10000': 0, 'bestGuess100000': 0,
        'totalScore': 0
    })

@app.route('/status')
def status():
    return jsonify({'logged_in': False})

@app.route('/register', methods=['POST'])
def register():
    return jsonify({'ok': True})

@app.route('/login', methods=['POST'])
def login():
    return jsonify({'ok': True})

# ✅ 404 ОБРАБОТЧИК
@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
