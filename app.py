from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aleksin-hub-super-secret-2026')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = False
CORS(app)  # Для фронта

def get_db():
    conn = sqlite3.connect('gamehub.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        game TEXT,
        score INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256((password + 'aleksin2026').encode()).hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username'].strip()
    password = hash_password(data['password'])
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return jsonify({'success': True, 'message': 'Зарегистрирован!'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Имя занято'}), 409
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username'].strip()
    password = hash_password(data['password'])
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        session['user_id'] = user['id']
        session['username'] = username
        return jsonify({'success': True, 'username': username})
    return jsonify({'success': False, 'message': 'Неверно'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/status')
def status():
    if 'username' in session:
        return jsonify({'logged': True, 'username': session['username']})
    return jsonify({'logged': False})

@app.route('/top/<game>')
def top(game):
    conn = get_db()
    leaders = conn.execute("""
        SELECT u.username, MAX(s.score) as score 
        FROM scores s JOIN users u ON s.user_id=u.id 
        WHERE s.game=? GROUP BY u.id ORDER BY score DESC LIMIT 10
    """, (game,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in leaders])

@app.route('/save_score', methods=['POST'])
def save_score():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO scores (user_id, game, score) VALUES (?, ?, ?)",
              (session['user_id'], data['game'], data['score']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/test')
def test():
    return jsonify({'status': 'API жив!', 'session': bool(session)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
