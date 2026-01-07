import os
from flask import Flask, request, jsonify, session, render_template_string
import sqlite3
from datetime import datetime

# 🔥 ГЛАВНЫЙ FIX ПЕРЕМЕННЫЕ ДО app = Flask()
os.environ['FLASK_RUN_HOST'] = '0.0.0.0'
os.environ['FLASK_RUN_PORT'] = str(os.environ.get('PORT', 10000))

app = Flask(__name__)
app.secret_key = 'aleksin-hub-2026-v4-secure'

print(f"🚀 STARTING on 0.0.0.0:{os.environ.get('PORT', 10000)}")

def init_db():
    conn = sqlite3.connect('games.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, game TEXT, points INTEGER, difficulty TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template_string(HTML_CODE)  # Твой HTML

@app.route('/health')
def health():
    return f"🚀 OK on 0.0.0.0:{os.environ.get('PORT', 10000)}"

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = sqlite3.connect('games.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (data['username'],))
    result = c.fetchone()
    conn.close()
    if result and result[0] == data['password']:
        session['user'] = data['username']
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Неверный логин/пароль'})

# остальные роуты (leaderboard, scores, tournament) как раньше

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
