import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, request, jsonify, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'aleksin-hub-2026-secure-key-change-in-prod'

def init_db():
    conn = sqlite3.connect('games.db', check_same_thread=False)
    c = conn.cursor()
    # Пользователи
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # Скоринг
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user TEXT, game TEXT, points INTEGER, 
                  difficulty TEXT, timestamp TEXT,
                  FOREIGN KEY(user) REFERENCES users(username))''')
    # Турнир (ежедневный)
    c.execute('''CREATE TABLE IF NOT EXISTS tournament 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user TEXT, points INTEGER, date TEXT)''')
    conn.commit()
    conn.close()

# ✅ Render PORT binding
port = int(os.environ.get('PORT', 10000))
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=port, debug=False)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)  # Твой HTML целиком

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username, password = data['username'], data['password']
    
    conn = sqlite3.connect('games.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0] == password:  # Простой пароль (для демо)
        session['user'] = username
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '❌ Неверный логин/пароль'})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/api/leaderboard/<game>')
def leaderboard(game):
    if 'user' not in session:
        return jsonify([])
    
    conn = sqlite3.connect('games.db')
    scores = conn.execute(
        "SELECT user, points, difficulty FROM scores WHERE game=? ORDER BY points DESC LIMIT 10",
        (game,)
    ).fetchall()
    conn.close()
    return jsonify([{'user': r[0], 'points': r[1], 'difficulty': r[2]} for r in scores])

@app.route('/api/scores', methods=['POST'])
def save_score():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'})
    
    data = request.json
    conn = sqlite3.connect('games.db')
    conn.execute(
        "INSERT INTO scores (user, game, points, difficulty, timestamp) VALUES (?, ?, ?, ?, ?)",
        (session['user'], data['game'], data['points'], data['difficulty'], 
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    update_tournament(session['user'], data['points'])
    return jsonify({'success': True})

@app.route('/api/tournament')
def tournament():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('games.db')
    scores = conn.execute(
        "SELECT user, SUM(points) as total FROM scores WHERE DATE(timestamp)=? GROUP BY user ORDER BY total DESC LIMIT 100",
        (today,)
    ).fetchall()
    conn.close()
    return jsonify([{'user': r[0], 'points': r[1], 'rank': i+1} for i, r in enumerate(scores)])

def update_tournament(user, points):
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('games.db')
    # Обновляем ежедневный турнир
    conn.execute(
        "INSERT INTO tournament (user, points, date) VALUES (?, ?, ?) ON CONFLICT(user) DO UPDATE SET points=points+?",
        (user, points, today, points)
    )
    conn.commit()
    conn.close()

# Инициализация демо юзера
init_db()
conn = sqlite3.connect('games.db')
conn.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('test', '123456')")
conn.commit()
conn.close()

# ТВОЙ HTML TEMPLATE (вставь сюда весь HTML код из твоего сообщения)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru"> ... Весь твой HTML код целиком ...
</html>
"""
