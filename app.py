import os
from flask import Flask, request, jsonify, session, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'aleksin-hub-2026-v4-secure'

# 🔥 RENDER PORT (ВСЕГДА доступен)
port = int(os.environ.get('PORT', 10000))
host = '0.0.0.0'

def init_db():
    conn = sqlite3.connect('games.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, game TEXT, points INTEGER, 
                  difficulty TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

# Все роуты остаются ТЕМИ ЖЕ (login, leaderboard, scores, tournament)
@app.route('/')
def index():
    return render_template_string(HTML_CODE)  # Твой HTML

@app.route('/login', methods=['POST'])
def login(): 
    data = request.json
    conn = sqlite3.connect('games.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (data['username'],))
    if c.fetchone() and c.fetchone()[0] == data['password']:
        session['user'] = data['username']
    conn.close()
    return jsonify({'success': True})

# ... остальные роуты сокращены для ясности ...

# 🔥 ГЛАВНЫЙ RENDER FIX - ЛЮБАЯ команда видит порт!
@app.route('/health')
def health():
    return f"🚀 OK on {host}:{port}"

if __name__ == '__main__':
    init_db()
    print(f"🚀 ALEKSIN GAMES HUB v4.0 listening on {host}:{port}")
    app.run(host=host, port=port, debug=False)
else:
    # 🔥 Render/gunicorn видит ЭТО!
    print(f"🚀 Render detected! Running on {host}:{port}")
    init_db()

# Демо юзер
init_db()
conn = sqlite3.connect('games.db')
conn.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('test', '123456')")
conn.commit()
conn.close()

HTML_CODE = '''[Твой полный HTML-код]'''
