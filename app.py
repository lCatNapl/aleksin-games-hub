from flask import Flask, request, jsonify, session
import sqlite3, json, datetime

app = Flask(__name__)
app.secret_key = 'aleksin-hub-2026'

def init_db():
    conn = sqlite3.connect('games.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY, user TEXT, game TEXT, points INTEGER, difficulty TEXT, timestamp TEXT)''')
    conn.commit(); conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = sqlite3.connect('games.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (data['username'], data['password']))
    if c.fetchone():
        session['user'] = data['username']
        conn.close(); return jsonify({'success': True})
    conn.close(); return jsonify({'success': False, 'error': 'Неверный логин/пароль'})

@app.route('/api/leaderboard/<game>')
def leaderboard(game):
    conn = sqlite3.connect('games.db')
    scores = conn.execute(f"SELECT user, points, difficulty FROM scores WHERE game='{game}' ORDER BY points DESC LIMIT 10").fetchall()
    conn.close(); return jsonify([{'user': u[0], 'points': u[1], 'difficulty': u[2]} for u in scores])

@app.route('/api/scores', methods=['POST'])
def save_score():
    if 'user' not in session: return jsonify({'success': False})
    data = request.json
    conn = sqlite3.connect('games.db')
    conn.execute("INSERT INTO scores (user, game, points, difficulty, timestamp) VALUES (?, ?, ?, ?, ?)",
                (session['user'], data['game'], data['points'], data['difficulty'], datetime.datetime.now().isoformat()))
    conn.commit(); conn.close(); return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    # Создадим демо юзера
    conn = sqlite3.connect('games.db')
    conn.execute("INSERT OR IGNORE INTO users VALUES ('test', '123456')")
    conn.commit(); conn.close()
    app.run(debug=True)
