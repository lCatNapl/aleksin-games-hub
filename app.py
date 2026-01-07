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
        "SELECT user, SUM(points) as total FROM scores WHERE DATE(timestamp)=? GROUP BY user ORDER BY total DESC LIMIT 100",
        (today,)
    ).fetchall()
    conn.close()
    return jsonify([{'user': r[0], 'points': r[1], 'rank': i+1} for i, r in enumerate(scores)])

# 🔥 Render PORT FIX
port = int(os.environ.get('PORT', 10000))
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=port, debug=False)

# ДЕМО ЮЗЕР
init_db()
conn = sqlite3.connect('games.db')
conn.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('test', '123456')")
conn.commit()
conn.close()

# ✅ ПОЛНЫЙ HTML (весь твой код)
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
            animation: gradientShift 8s ease infinite;
            color: #fff;
            overflow-x: hidden;
            min-height: 100vh;
        }
        @keyframes gradientShift { 0%,100%{background-position:0% 50%;}50%{background-position:100% 50%;} }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header {
            text-align: center; margin-bottom: 30px;
            background: linear-gradient(45deg, #ff00ff, #00ffff, #ffff00);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; font-size: 3em; font-weight: 900; 
            text-shadow: 0 0 30px #ff00ff;
            animation: rgbGlow 2s ease-in-out infinite alternate;
        }
        @keyframes rgbGlow { from{filter:hue-rotate(0deg);}to{filter:hue-rotate(360deg);} }

        .auth-panel, .games-panel { 
            background: rgba(0,0,0,0.8); backdrop-filter: blur(20px); 
            border-radius: 20px; padding: 30px; margin: 20px 0; 
            border: 2px solid; box-shadow: 0 0 50px rgba(0,255,255,0.3);
            animation: float 3s ease-in-out infinite;
        }
        @keyframes float { 0%,100%{transform:translateY(0);}50%{transform:translateY(-10px);} }

        /* ANTI-IPHONE */
        @media only screen and (max-device-width: 812px) and (-webkit-min-device-pixel-ratio: 3) {
            body::before {
                content: "🚫 iPhone заблокирован! Только Android/PC"; 
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: #000; color: #ff4444; font-size: 24px;
                display: flex; align-items: center; justify-content: center; z-index: 9999;
            }
        }

        .login-form { display: flex; flex-direction: column; gap: 15px; max-width: 300px; margin: 0 auto; }
        input { padding: 15px; border: none; border-radius: 10px; background: rgba(255,255,255,0.1);
                color: #fff; font-size: 16px; font-family: inherit; }
        input::placeholder { color: #aaa; }
        button {
            padding: 15px; border: none; border-radius: 10px; 
            background: linear-gradient(45deg, #ff00ff, #00ffff);
            color: #000; font-weight: 700; font-size: 16px; cursor: pointer; 
            transition: all 0.3s; box-shadow: 0 5px 15px rgba(0,255,255,0.4);
        }
        button:hover { transform: scale(1.05); box-shadow: 0 10px 30px rgba(0,255,255,0.6); }
        button:active { transform: scale(0.98); }

        .games-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .game-card {
            background: rgba(0,0,0,0.7); border-radius: 20px; padding: 20px; text-align: center;
            border: 2px solid transparent; cursor: pointer; transition: all 0.3s;
        }
        .game-card:hover { border-color: #00ffff; box-shadow: 0 0 30px #00ffff; transform: translateY(-10px); }
        .game-card h3 { color: #00ffff; margin-bottom: 10px; font-size: 1.5em; }

        .leaderboards, .tournament { 
            background: rgba(0,255,0,0.1); border: 2px solid #00ff00; 
            margin: 20px 0; border-radius: 15px; padding: 20px;
        }
        .leaderboards h2, .tournament h2 { color: #00ff00; text-align: center; margin-bottom: 20px; }
        .leaderboard-list, .tournament-list { max-height: 300px; overflow-y: auto; }
        .leaderboard-list ol, .tournament-list ol { padding-left: 20px; }
        .leaderboard-list li, .tournament-list li {
            padding: 8px; margin: 5px 0; background: rgba(255,255,255,0.1); border-radius: 8px;
            display: flex; justify-content: space-between;
        }
        .rank-1 { border-left: 5px solid #ffd700; } 
        .rank-2 { border-left: 5px solid #c0c0c0; } 
        .rank-3 { border-left: 5px solid #cd7f32; } 
        .prize { color: #ffd700; font-weight: bold; }

        .hidden { display: none !important; }
        .status { text-align: center; font-size: 1.2em; margin: 10px 0; }
        .welcome { color: #00ffff; font-size: 1.5em; }

        #gameCanvas { border: 3px solid #00ffff; border-radius: 10px; background: #000; 
                      display: block; margin: 10px auto; }
        .controls { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin: 10px 0; }
        .control-btn { width: 60px; height: 60px; border-radius: 50%; 
                       background: rgba(0,255,255,0.3); border: none; color: #fff; 
                       font-size: 18px; cursor: pointer; }
        .control-btn:active { background: #00ffff; transform: scale(0.9); }

        @media (max-width: 768px) {
            .header { font-size: 2em; } .container { padding: 10px; }
            .games-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">🚀 ALEKSIN GAMES HUB v4.0</h1>
        
        <div id="authPanel" class="auth-panel">
            <div class="status" id="status">🔐 ВХОД В СИСТЕМУ</div>
            <form class="login-form">
                <input type="text" id="username" placeholder="👤 Логин (test)" value="test">
                <input type="password" id="password" placeholder="🔑 Пароль (123456)">
                <button type="submit">🚀 ВОЙТИ</button>
            </form>
            <div style="text-align:center; margin-top:15px;">
                <small>Демо: test / 123456</small>
            </div>
        </div>

        <div id="mainPanel" class="hidden">
            <div class="status welcome" id="welcome"></div>
            <button onclick="logout()" style="float:right; padding:10px 20px; font-size:14px;">🚪 Выход</button>
            
            <div class="games-grid">
                <div class="game-card" onclick="startSnake('easy')">
                    <h3>🐍 ЗМЕЙКА EASY</h3><p>Классика с touch/WASD</p>
                </div>
                <div class="game-card" onclick="startSnake('medium')">
                    <h3>🐍 ЗМЕЙКА MEDIUM</h3><p>Больше скорость!</p>
                </div>
                <div class="game-card" onclick="startGuess('easy')">
                    <h3>🎯 УГАДАЙКА EASY (1-100)</h3><p>Подсказки + рекорд</p>
                </div>
                <div class="game-card" onclick="startGuess('hard')">
                    <h3>🎯 УГАДАЙКА HARD (1-10000)</h3><p>Для профи!</p>
                </div>
            </div>

            <div id="leaderboards" class="leaderboards hidden"></div>
            <div id="tournament" class="tournament hidden"></div>
        </div>
    </div>

    <canvas id="gameCanvas" width="400" height="400" class="hidden"></canvas>
    <div class="controls hidden" id="controls">
        <button class="control-btn" onclick="changeDirection('up')">↑</button>
        <button class="control-btn" onclick="changeDirection('left')">←</button>
        <button class="control-btn" onclick="changeDirection('right')">→</button>
        <button class="control-btn" onclick="changeDirection('down')">↓</button>
    </div>

    <script>
        let currentUser = null;
        let snakeDir = {x: 0, y: 0};
        let gameActive = false;

        setInterval(() => { if (currentUser) { updateLeaderboards(); updateTournament(); } }, 5000);

        document.querySelector('.login-form').addEventListener('submit', async e => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const response = await fetch('/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            const result = await response.json();
            if (result.success) {
                currentUser = username;
                document.getElementById('status').textContent = `✅ Привет, ${username}!`;
                document.getElementById('welcome').textContent = `🎮 Добро пожаловать, ${username}!`;
                document.getElementById('authPanel').classList.add('hidden');
                document.getElementById('mainPanel').classList.remove('hidden');
                updateLeaderboards();
                updateTournament();
            } else {
                document.getElementById('status').textContent = '❌ ' + (result.error || 'Ошибка входа');
            }
        });

        async function updateLeaderboards() {
            const games = ['snake_easy', 'snake_medium', 'guess_easy', 'guess_hard'];
            let html = '<h2>🏆 ГЛОБАЛЬНЫЕ ТОП-10 (ВСЕ ИГРОКИ)</h2>';
            
            for (let game of games) {
                try {
                    const response = await fetch(`/api/leaderboard/${game}`);
                    const top10 = await response.json();
                    html += `<h3>${game.toUpperCase().replace('_', ' ')}</h3><ol class="leaderboard-list">`;
                    top10.forEach((player, i) => {
                        const rankClass = i < 3 ? `rank-${i+1}` : '';
                        html += `<li class="${rankClass}"><span>#${i+1} ${player.user}</span><span>${player.points} (${player.difficulty})</span></li>`;
                    });
                    html += '</ol>';
                } catch(e) {
                    html += `<p>Загрузка ${game}...</p>`;
                }
            }
            document.getElementById('leaderboards').innerHTML = html;
            document.getElementById('leaderboards').classList.remove('hidden');
        }

        async function updateTournament() {
            try {
                const response = await fetch('/api/tournament');
                const top100 = await response.json();
                let html = '<h2>⚔️ ТУРНИР СЕГОДНЯ (ТОП-100)</h2><ol class="tournament-list">';
                top100.slice(0,100).forEach((player, i) => {
                    const prize = i < 5 ? `<span class="prize">🥇 +${100*(6-(i+1))} очков</span>` : '';
                    html += `<li>${player.rank || i+1}. ${player.user}: ${player.points} ${prize}</li>`;
                });
                html += '</ol>';
                document.getElementById('tournament').innerHTML = html;
                document.getElementById('tournament').classList.remove('hidden');
            } catch(e) {
                document.getElementById('tournament').innerHTML = '<h2>⚔️ Турнир: Загрузка...</h2>';
            }
        }

        async function saveScore(game, points, difficulty = 'normal') {
            await fetch('/api/scores', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({game, points, difficulty})
            });
            updateLeaderboards(); updateTournament();
        }

        async function logout() {
            await fetch('/logout');
            location.reload();
        }

        // ЗМЕЙКА + УГАДАЙКА код (весь твой JavaScript остается тем же)
        function startSnake(difficulty) {
            const canvas = document.getElementById('gameCanvas');
            const ctx = canvas.getContext('2d');
            canvas.classList.remove('hidden');
            document.getElementById('controls').classList.remove('hidden');
            
            let snake = [{x: 10, y: 10}];
            let food = {x: 15, y: 15};
            let score = 0;
            gameActive = true;
            
            function gameLoop() {
                if (!gameActive) return;
                ctx.fillStyle = '#000';
                ctx.fillRect(0, 0, 400, 400);
                ctx.fillStyle = '#00ff00';
                snake.forEach(part => ctx.fillRect(part.x*20, part.y*20, 20, 20));
                ctx.fillStyle = '#ff0000';
                ctx.fillRect(food.x*20, food.y*20, 20, 20);
                
                let head = {x: snake[0].x + snakeDir.x, y: snake[0].y + snakeDir.y};
                
                                if (head.x < 0 || head.x >= 20 || head.y < 0 || head.y >= 20 || 
                    snake.some(s => s.x === head.x && s.y === head.y)) {
                    saveScore(`snake_${difficulty}`, score, difficulty);
                    alert(`Игра окончена! Рекорд: ${score}`);
                    gameActive = false;
                    canvas.classList.add('hidden');
                    document.getElementById('controls').classList.add('hidden');
                    return;
                }
                
                snake.unshift(head);
                if (head.x === food.x && head.y === food.y) {
                    score += 100;
                    food = {x: Math.floor(Math.random()*19), y: Math.floor(Math.random()*19)};
                } else {
                    snake.pop();
                }
                
                setTimeout(gameLoop, difficulty === 'easy' ? 200 : 100);
            }
            gameLoop();
        }

        function changeDirection(dir) {
            const directions = {
                up: {x: 0, y: -1}, down: {x: 0, y: 1},
                left: {x: -1, y: 0}, right: {x: 1, y: 0}
            };
            if ((dir === 'up' && snakeDir.y !== 1) || (dir === 'down' && snakeDir.y !== -1) ||
                (dir === 'left' && snakeDir.x !== 1) || (dir === 'right' && snakeDir.x !== -1)) {
                snakeDir = directions[dir];
            }
        }

        // TOUCH + КЛАВИАТУРА (твой код)
        let touchStartX, touchStartY;
        document.addEventListener('touchstart', e => {
            touchStartX = e.touches[0].clientX; touchStartY = e.touches[0].clientY; e.preventDefault();
        });
        document.addEventListener('touchend', e => {
            if (!touchStartX) return;
            let dx = e.changedTouches[0].clientX - touchStartX;
            let dy = e.changedTouches[0].clientY - touchStartY;
            if (Math.abs(dx) > Math.abs(dy)) {
                changeDirection(dx > 0 ? 'right' : 'left');
            } else {
                changeDirection(dy > 0 ? 'down' : 'up');
            }
            touchStartX = null; e.preventDefault();
        });
        document.addEventListener('keydown', e => {
            if (e.key === 'ArrowUp') changeDirection('up');
            if (e.key === 'ArrowDown') changeDirection('down');
            if (e.key === 'ArrowLeft') changeDirection('left');
            if (e.key === 'ArrowRight') changeDirection('right');
        });

        // УГАДАЙКА
        function startGuess(difficulty) {
            const maxNum = difficulty === 'easy' ? 100 : 10000;
            const target = Math.floor(Math.random() * maxNum) + 1;
            let attempts = 0, min = 1, max = maxNum;
            
            const canvas = document.getElementById('gameCanvas');
            canvas.classList.remove('hidden');
            
            const guessInput = document.createElement('input');
            guessInput.placeholder = 'Введи число';
            guessInput.style.cssText = 'position:fixed;top:10px;left:50%;transform:translateX(-50%);padding:10px;z-index:1000;border-radius:10px;background:rgba(0,255,255,0.2);color:#fff;border:2px solid #00ffff;';
            document.body.appendChild(guessInput);
            
            function checkGuess() {
                const guess = parseInt(guessInput.value);
                if (isNaN(guess)) return;
                attempts++;
                if (guess === target) {
                    const points = maxNum - attempts * 10;
                    saveScore(`guess_${difficulty}`, points, difficulty);
                    alert(`✅ Угадал за ${attempts} попыток! Рекорд: ${points}`);
                    document.body.removeChild(guessInput);
                    canvas.classList.add('hidden');
                } else {
                    if (guess < target) { min = guess; document.getElementById('status').textContent = `⬆️ Больше! ${min}-${max}`; }
                    else { max = guess; document.getElementById('status').textContent = `⬇️ Меньше! ${min}-${max}`; }
                }
                guessInput.value = '';
            }
            
            guessInput.addEventListener('keypress', e => { if (e.key === 'Enter') checkGuess(); });
            document.getElementById('controls').classList.remove('hidden');
            document.querySelector('.control-btn:last-child').textContent = '🎯';
            document.querySelector('.control-btn:last-child').onclick = checkGuess;
        }
    </script>
</body>
</html>'''

# ✅ Render настройки:
# Build Command: pip install -r requirements.txt  
# Start Command: gunicorn app:app
# Language: Python

# requirements.txt:
# Flask==3.0.3
# gunicorn==22.0.0

print("🚀 ALEKSIN GAMES HUB v4.0 ✅ Render-ready!")
