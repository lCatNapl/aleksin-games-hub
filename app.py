import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, session, render_template_string

app = Flask(__name__)
app.secret_key = 'aleksin-hub-2026-v4-secure'

def init_db():
    conn = sqlite3.connect('games.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user TEXT, game TEXT, points INTEGER, 
                  difficulty TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tournament 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user TEXT, points INTEGER, date TEXT,
                  PRIMARY KEY(user, date))''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template_string(HTML_CODE)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username, password = data['username'], data['password']
    
    conn = sqlite3.connect('games.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0] == password:
        session['user'] = username
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '❌ Неверный логин/пароль'})

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True})

@app.route('/api/leaderboard/<game>')
def leaderboard(game):
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
    return jsonify({'success': True})

@app.route('/api/tournament')
def tournament():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('games.db')
    scores = conn.execute(
        "SELECT user, SUM(points) as total FROM scores WHERE DATE(timestamp)=? AND user IN (SELECT username FROM users) GROUP BY user ORDER BY total DESC LIMIT 100",
        (today,)
    ).fetchall()
    conn.close()
    return jsonify([{'user': r[0], 'points': r[1], 'rank': i+1} for i, r in enumerate(scores)])

# 🎯 Render PORT FIX (главное!)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Инициализация БД + демо юзер
init_db()
conn = sqlite3.connect('games.db')
conn.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('test', '123456')")
conn.commit()
conn.close()

# ТВОЙ HTML (весь код из твоего сообщения)
HTML_CODE = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 ALEKSIN GAMES HUB v4.0 | ГЛОБАЛЬНЫЕ ЛИДЕРБОРДЫ</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Orbitron', monospace;
            background: linear-gradient(-45deg, #0f0f23, #1a0033, #330066, #000);
            background-size: 400% 400%;
            animation: gradientShift
