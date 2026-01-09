from flask import Flask, request, jsonify, session, redirect, send_file
import sqlite3, hashlib, re, json
from datetime import datetime, timedelta
import time

app = Flask(__name__)
app.secret_key = 'aleksin-games-v6-super-secret'

def to_latin(text):
    map_dict = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya','А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'E','Ж':'Zh','З':'Z','И':'I','Й':'Y','К':'K','Л':'L','М':'M','Н':'N','О':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U','Ф':'F','Х':'H','Ц':'C','Ч':'Ch','Ш':'Sh','Щ':'Sch','Ъ':'','Ы':'Y','Ь':'','Э':'E','Ю':'Yu','Я':'Ya'}
    return re.sub(r'[^a-z0-9]', '_', ''.join(map_dict.get(c, c) for c in text).lower())

def init_db():
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    
    # Пользователи
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username_orig TEXT PRIMARY KEY, username_lat TEXT UNIQUE, password TEXT,
        total_score INTEGER DEFAULT 0, games_played INTEGER DEFAULT 0,
        achievements TEXT DEFAULT '[]', tournament_score INTEGER DEFAULT 0
    )''')
    
    # Результаты игр (макс для топ-10)
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY, username_lat TEXT, game TEXT, difficulty TEXT,
        score INTEGER, attempts INTEGER DEFAULT 1, timestamp INTEGER
    )''')
    
    # Турниры (заканчиваются в 00:00 МСК)
    c.execute('''CREATE TABLE IF NOT EXISTS tournaments (
        id INTEGER PRIMARY KEY, game TEXT, difficulty TEXT, active INTEGER DEFAULT 1,
        start_time INTEGER, end_time INTEGER
    )''')
    
    # Турнирные скоринги
    c.execute('''CREATE TABLE IF NOT EXISTS tournament_scores (
        tournament_id INTEGER, username_lat TEXT, score INTEGER,
        PRIMARY KEY (tournament_id, username_lat)
    )''')
    
    # Создать активный турнир если нет
    c.execute("SELECT COUNT(*) FROM tournaments WHERE active=1")
    if c.fetchone()[0] == 0:
        now = int(time.time())
        end_time = int((datetime.now().replace(hour=0,minute=0,second=0,microsecond=0) + timedelta(days=1)).timestamp() + 3*3600)  # МСК
        c.execute("INSERT INTO tournaments (game, difficulty, start_time, end_time, active) VALUES (?, ?, ?, ?, 1)",
                 ('snake', 'easy', now, end_time))
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/ping')
def ping():
    return jsonify({'status': 'ok', 'user': session.get('username_orig', 'guest')})

@app.route('/api/profile/<username_lat>')
def profile(username_lat):
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username_lat=?", (username_lat,))
    user = c.fetchone()
    scores = c.execute("SELECT game, difficulty, MAX(score) as best FROM scores WHERE username_lat=? GROUP BY game, difficulty", (username_lat,)).fetchall()
    conn.close()
    return jsonify({'user': user, 'best_scores': scores})

@app.route('/api/top10/<game>/<difficulty>')
def top10(game, difficulty):
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    c.execute("""SELECT u.username_orig, MAX(s.score) as best_score
                 FROM scores s JOIN users u ON s.username_lat=u.username_lat 
                 WHERE s.game=? AND s.difficulty=? GROUP BY s.username_lat ORDER BY best_score DESC LIMIT 10""", (game, difficulty))
    top = [{'name': r[0], 'score': r[1]} for r in c.fetchall()]
    conn.close()
    return jsonify(top)

@app.route('/api/tournaments')
def tournaments():
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tournaments WHERE active=1")
    tourney = c.fetchone()
    if tourney:
        end_time = tourney[5]
        time_left = max(0, end_time - int(time.time()))
        hours = time_left // 3600
        mins = (time_left % 3600) // 60
        c.execute("SELECT u.username_orig, ts.score FROM tournament_scores ts JOIN users u ON ts.username_lat=u.username_lat WHERE ts.tournament_id=? ORDER BY ts.score DESC LIMIT 10", (tourney[0],))
        standings = [{'name': r[0], 'score': r[1]} for r in c.fetchall()]
        conn.close()
        return jsonify({'active': True, 'game': tourney[2], 'diff': tourney[3], 'time_left': f"{hours:02d}:{mins:02d}", 'standings': standings})
    conn.close()
    return jsonify({'active': False})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username_orig, password = data['username'], hashlib.sha256(data['password'].encode()).hexdigest()
    username_lat = to_latin(username_orig)
    
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username_orig, username_lat, password) VALUES (?, ?, ?)", (username_orig, username_lat, password))
        conn.commit()
        session['username_lat'] = username_lat
        session['username_orig'] = username_orig
        conn.close()
        return jsonify({'success': True})
    except:
        conn.close()
        return jsonify({'success': False, 'error': 'Пользователь существует'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username_orig = data['username']
    password = hashlib.sha256(data['password'].encode()).hexdigest()
    username_lat = to_latin(username_orig)
    
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username_lat=? AND password=?", (username_lat, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['username_lat'] = username_lat
        session['username_orig'] = username_orig
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Неверный логин/пароль'})

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/save_score', methods=['POST'])
def save_score():
    data = request.get_json()
    username_lat = request.headers.get('username', session.get('username_lat', 'guest'))
    
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    
    # Сохранить результат
    c.execute("INSERT INTO scores (username_lat, game, difficulty, score, attempts, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
             (username_lat, data['game'], data['diff'], data['score'], data.get('attempts', 1), int(data['timestamp'])))
    
    # Турнир
    c.execute("SELECT id FROM tournaments WHERE active=1 AND game=? AND difficulty=?", (data['game'], data['diff']))
    tourney = c.fetchone()
    if tourney and username_lat != 'guest':
        c.execute("INSERT OR REPLACE INTO tournament_scores VALUES (?, ?, COALESCE((SELECT score FROM tournament_scores WHERE tournament_id=? AND username_lat=?), 0) + ?)",
                 (tourney[0], username_lat, tourney[0], username_lat, data['score']))
    
    # Обновить статистику
    c.execute("UPDATE users SET total_score=total_score+?, games_played=games_played+1 WHERE username_lat=?", (data['score'], username_lat))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
