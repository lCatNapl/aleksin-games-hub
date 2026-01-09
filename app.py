from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
from datetime import datetime
from transliterate import translit  # pip install transliterate

app = Flask(__name__)
app.secret_key = 'aleksin-games-super-secret-2026'

# Инициализация БД
def init_db():
    conn = sqlite3.connect('aleksin_games.db')
    c = conn.cursor()
    
    # Пользователи
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username_orig TEXT UNIQUE,
        username_lat TEXT UNIQUE,
        password TEXT
    )''')
    
    # Скоринг
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username_lat TEXT,
        game TEXT,
        difficulty TEXT,
        score INTEGER,
        timestamp INTEGER
    )''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username_orig = request.form['username']
    password = hashlib.sha256(request.form['password'].encode()).hexdigest()
    
    try:
        username_lat = translit(username_orig, 'ru', reversed=True)
    except:
        username_lat = username_orig.encode('ascii', 'ignore').decode('ascii').lower()
    
    conn = sqlite3.connect('aleksin_games.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username_orig, username_lat, password) VALUES (?, ?, ?)",
              (username_orig, username_lat, password))
    conn.commit()
    conn.close()
    
    session['username_lat'] = username_lat
    session['username_orig'] = username_orig
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username_orig = request.form['username']
    password = hashlib.sha256(request.form['password'].encode()).hexdigest()
    
    try:
        username_lat = translit(username_orig, 'ru', reversed=True)
    except:
        username_lat = username_orig.encode('ascii', 'ignore').decode('ascii').lower()
    
    conn = sqlite3.connect('aleksin_games.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username_lat=? AND password=?", (username_lat, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['username_lat'] = username_lat
        session['username_orig'] = username_orig
        return redirect(url_for('index'))
    return 'Ошибка входа!'

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ✅ ФИКС ЛИДЕРБОРДОВ - работает с кириллицей!
@app.route('/leaderboard', methods=['POST'])
def leaderboard_save():
    data = request.get_json()
    username_lat = request.headers.get('username', 'guest')
    
    conn = sqlite3.connect('aleksin_games.db')
    c = conn.cursor()
    c.execute("INSERT INTO scores (username_lat, game, difficulty, score, timestamp) VALUES (?, ?, ?, ?, ?)",
              (username_lat, data['game'], data['diff'], data['score'], int(data['timestamp'])))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'ok'})

@app.route('/leaderboard/<game>/<difficulty>')
def leaderboard_get(game, difficulty):
    conn = sqlite3.connect('aleksin_games.db')
    c = conn.cursor()
    c.execute("""SELECT u.username_orig, s.score 
                 FROM scores s 
                 JOIN users u ON s.username_lat = u.username_lat 
                 WHERE s.game=? AND s.difficulty=? 
                 ORDER BY s.score DESC, s.timestamp ASC 
                 LIMIT 10""", (game, difficulty))
    scores = [{'name': row[0] or 'guest', 'score': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(scores)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
