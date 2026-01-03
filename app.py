from flask import Flask, render_template, request, jsonify, session, send_from_directory
import os
import sqlite3
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = 'aleksin-games-hub-2026-super-secret-key!!!'  # ✅ КРИТИЧНО!

# База данных
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, highscore INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/status')
def status():
    if 'username' in session:
        return jsonify({'logged_in': True, 'username': session['username']})
    return jsonify({'logged_in': False})

@app.route('/auth', methods=['POST'])
def auth():
    data = request.json
    username = data['username'].lower()
    password = hashlib.sha256(data['password'].encode()).hexdigest()
    mode = data['mode']
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    if mode == 'register':
        try:
            c.execute("INSERT INTO users (username, password, highscore) VALUES (?, ?, 0)", 
                     (username, password))
            conn.commit()
            session['username'] = username
            conn.close()
            return jsonify({'success': True})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'success': False, 'message': '❌ Имя уже занято!'})
    
    else:  # login
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': '❌ Неверный логин/пароль'})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT username, highscore FROM users ORDER BY highscore DESC")
    leaders = [{'username': row[0], 'highscore': row[1]} for row in c.fetchall()]
    conn.close()
    return jsonify(leaders)

@app.route('/save-score', methods=['POST'])
def save_score():
    if 'username' not in session:
        return jsonify({'success': False})
    
    data = request.json
    username = session['username']
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET highscore=? WHERE username=?", (data['highscore'], username))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
