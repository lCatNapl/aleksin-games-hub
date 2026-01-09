from flask import Flask, request, jsonify, session, redirect, send_file
import sqlite3, hashlib, re, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'aleksin-games-2026'

def to_latin(text):
    map_dict = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya','А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'E','Ж':'Zh','З':'Z','И':'I','Й':'Y','К':'K','Л':'L','М':'M','Н':'N','О':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U','Ф':'F','Х':'H','Ц':'C','Ч':'Ch','Ш':'Sh','Щ':'Sch','Ъ':'','Ы':'Y','Ь':'','Э':'E','Ю':'Yu','Я':'Ya'}
    return re.sub(r'[^a-z0-9]', '_', ''.join(map_dict.get(c, c) for c in text).lower())

def init_db():
    conn = sqlite3.connect('scores.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username_orig TEXT UNIQUE, username_lat TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores (username_lat TEXT, game TEXT, difficulty TEXT, score INTEGER, timestamp INTEGER)''')
    conn.commit()
    conn.close()
init_db()

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/ping')
def ping():
    return jsonify({'status': 'ok', 'username': session.get('username_orig', 'guest')})

@app.route('/register', methods=['POST'])
def register():
    username_orig = request.form['username']
    password = hashlib.sha256(request.form['password'].encode()).hexdigest()
    username_lat = to_latin(username_orig)
    
    conn = sqlite3.connect('scores.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username_orig, username_lat, password) VALUES (?, ?, ?)",
                  (username_orig, username_lat, password))
        conn.commit()
        session['username_lat'] = username_lat
        session['username_orig'] = username_orig
        conn.close()
        return redirect('/')
    except:
        conn.close()
        return 'Пользователь существует!', 400

@app.route('/login', methods=['POST'])
def login():
    username_orig = request.form['username']
    password = hashlib.sha256(request.form['password'].encode()).hexdigest()
    username_lat = to_latin(username_orig)
    
    conn = sqlite3.connect('scores.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username_lat=? AND password=?", (username_lat, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['username_lat'] = username_lat
        session['username_orig'] = username_orig
        return redirect('/')
    return 'Ошибка входа!', 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/leaderboard', methods=['POST'])
def leaderboard_save():
    data = request.get_json()
    username_lat = request.headers.get('username', 'guest')
    conn = sqlite3.connect('scores.db')
    c = conn.cursor()
    c.execute("INSERT INTO scores VALUES (?, ?, ?, ?, ?)",
              (username_lat, data['game'], data['diff'], data['score'], int(data['timestamp'])))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/leaderboard/<game>/<difficulty>')
def leaderboard_get(game, difficulty):
    conn = sqlite3.connect('scores.db')
    c = conn.cursor()
    c.execute("SELECT username_orig, score FROM scores s LEFT JOIN users u ON s.username_lat=u.username_lat WHERE game=? AND difficulty=? ORDER BY score DESC LIMIT 10", (game, difficulty))
    scores = [{'name': r[0] or 'guest', 'score': r[1]} for r in c.fetchall()]
    conn.close()
    return jsonify(scores)

if __name__ == '__main__':
    app.run(debug=True)
