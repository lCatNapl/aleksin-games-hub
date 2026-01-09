from flask import Flask, request, jsonify, session
import sqlite3, hashlib, re, json, random, time
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'aleksin-games-v6-super-secret'

def to_latin(text):
    map_dict = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
        'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'E','Ж':'Zh','З':'Z','И':'I','Й':'Y','К':'K','Л':'L','М':'M','Н':'N','О':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U','Ф':'F','Х':'H','Ц':'C','Ч':'Ch','Ш':'Sh','Щ':'Sch','Ъ':'','Ы':'Y','Ь':'','Э':'E','Ю':'Yu','Я':'Ya'
    }
    return re.sub(r'[^a-z0-9]', '_', ''.join(map_dict.get(c, c) for c in text).lower())

def init_db():
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username_orig TEXT PRIMARY KEY, username_lat TEXT UNIQUE, password TEXT,
        total_score INTEGER DEFAULT 0, games_played INTEGER DEFAULT 0,
        tournament_score INTEGER DEFAULT 0, achievements TEXT DEFAULT '[]'
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY, username_lat TEXT, game TEXT, difficulty TEXT,
        score INTEGER, attempts INTEGER DEFAULT 1, timestamp INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tournaments (
        id INTEGER PRIMARY KEY, game TEXT, difficulty TEXT, active INTEGER DEFAULT 1,
        start_time INTEGER, end_time INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tournament_scores (
        tournament_id INTEGER, username_lat TEXT, score INTEGER,
        PRIMARY KEY (tournament_id, username_lat)
    )''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return open('index.html').read()

@app.route('/api/ping')
def ping():
    return jsonify({'status': 'ok', 'user': session.get('username_orig', 'guest')})

@app.route('/api/profile/<username_lat>')
def profile(username_lat):
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username_lat=?", (username_lat,))
    user = c.fetchone()
    
    c.execute("SELECT game||' '||difficulty as game_diff, username_lat, MAX(score) as best FROM scores WHERE username_lat=? GROUP BY game, difficulty ORDER BY best DESC", (username_lat,))
    best_scores = c.fetchall()
    
    c.execute("SELECT COALESCE(SUM(score), 0) FROM tournament_scores ts JOIN tournaments t ON ts.tournament_id=t.id WHERE t.active=1 AND ts.username_lat=?", (username_lat,))
    tournament_score = c.fetchone()[0]
    
    conn.close()
    return jsonify({'user': user, 'best_scores': best_scores, 'tournament': tournament_score})

@app.route('/api/top10/<game>/<difficulty>')
def top10(game, difficulty):
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    c.execute("""
        SELECT u.username_orig, MAX(s.score) as best_score
        FROM scores s JOIN users u ON s.username_lat=u.username_lat 
        WHERE s.game=? AND s.difficulty=? 
        GROUP BY s.username_lat ORDER BY best_score DESC LIMIT 10
    """, (game, difficulty))
    top = [{'name': r[0], 'score': r[1] or 0} for r in c.fetchall()]
    conn.close()
    return jsonify(top)

@app.route('/api/tournaments')
def tournaments():
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    
    # Проверяем активный турнир
    c.execute("SELECT id, end_time FROM tournaments WHERE active=1")
    tourney = c.fetchone()
    
    current_time = int(time.time())
    msk_offset = 3 * 3600  # МСК
    
    # Создаем новый турнир если нужно
    if not tourney or current_time + msk_offset > tourney[1]:
        # Рандомная игра
        games = [('snake', 'easy'), ('snake', 'medium'), ('snake', 'hard'), 
                ('guess', '1000'), ('guess', '10000'), ('guess', '100000')]
        game, diff = random.choice(games)
        
        # Завтра 00:00 МСК
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        end_time = int(tomorrow.timestamp()) + msk_offset
        
        if tourney:
            c.execute("UPDATE tournaments SET active=0 WHERE id=?", (tourney[0],))
        
        c.execute("INSERT INTO tournaments (game, difficulty, start_time, end_time, active) VALUES (?, ?, ?, ?, 1)",
                 (game, diff, current_time, end_time))
        conn.commit()
        tourney_id, end_time, game, diff = 1, end_time, game, diff
    else:
        tourney_id, end_time, game, diff = tourney[0], tourney[1], 'snake', 'easy'
    
    # Время до конца (МСК)
    time_left = max(0, end_time - (current_time + msk_offset))
    hours, remainder = divmod(time_left, 3600)
    mins, secs = divmod(remainder, 60)
    
    c.execute("""
        SELECT u.username_orig, COALESCE(ts.score, 0) as score 
        FROM tournament_scores ts RIGHT JOIN users u ON ts.username_lat=u.username_lat 
        WHERE ts.tournament_id=? 
        ORDER BY ts.score DESC NULLS LAST LIMIT 10
    """, (tourney_id,))
    standings = [{'name': r[0], 'score': r[1]} for r in c.fetchall()]
    
    conn.close()
    return jsonify({
        'active': True, 'game': game, 'diff': diff,
        'time_left': f"{hours:02d}:{mins:02d}:{secs:02d}",
        'end_time': end_time, 'standings': standings
    })

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username_orig = data['username']
    password = hashlib.sha256(data['password'].encode()).hexdigest()
    username_lat = to_latin(username_orig)
    
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username_orig, username_lat, password) VALUES (?, ?, ?)",
                 (username_orig, username_lat, password))
        conn.commit()
        session['username_lat'] = username_lat
        session['username_orig'] = username_orig
        conn.close()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
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

@app.route('/api/save_score', methods=['POST'])
def save_score():
    data = request.get_json()
    username_lat = request.headers.get('username', session.get('username_lat', 'guest'))
    
    if username_lat == 'guest':
        return jsonify({'success': False, 'error': 'Войдите!'})
    
    conn = sqlite3.connect('aleksin_v6.db')
    c = conn.cursor()
    
    timestamp = int(data['timestamp'])
    
    # Сохраняем результат
    c.execute("""
        INSERT INTO scores (username_lat, game, difficulty, score, attempts, timestamp) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username_lat, data['game'], data['diff'], data['score'], data.get('attempts', 1), timestamp))
    
    # Турнир
    c.execute("SELECT id FROM tournaments WHERE active=1 AND game=? AND difficulty=?", 
             (data['game'], data['diff']))
    tourney = c.fetchone()
    if tourney:
        c.execute("""
            INSERT OR REPLACE INTO tournament_scores (tournament_id, username_lat, score)
            VALUES (?, ?, COALESCE((SELECT score FROM tournament_scores WHERE tournament_id=? AND username_lat=?), 0) + ?)
        """, (tourney[0], username_lat, tourney[0], username_lat, data['score']))
    
    # Обновляем статистику
    c.execute("UPDATE users SET total_score=total_score+?, games_played=games_played+1 WHERE username_lat=?", 
             (data['score'], username_lat))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
