let currentGame = '';
let isLoggedIn = false;
let gameData = {score: 0, highscore: 0};
let gameInterval = null;
let snake = {x:10,y:10,dx:0,dy:0,cells:[],maxCells:4};
let food = {x:15,y:15};
let secretNumber = 0;
let attempts = 0;
let maxAttempts = 20;

async function checkUserStatus() {
    try {
        const res = await fetch('/status', {credentials: 'include'});
        const data = await res.json();
        if (data.logged_in) {
            document.getElementById('status').textContent = `👋 ${data.username}`;
            document.getElementById('auth-buttons').style.display = 'none';
            document.getElementById('games-grid').style.display = 'grid';
            document.getElementById('logout-btn').style.display = 'block';
            document.getElementById('leaderboard-container').style.display = 'block';
            isLoggedIn = true;
            loadLeaderboard();
        } else {
            document.getElementById('status').textContent = '👋 Гость';
            document.getElementById('auth-buttons').style.display = 'flex';
            document.getElementById('games-grid').style.display = 'none';
            document.getElementById('logout-btn').style.display = 'none';
            document.getElementById('leaderboard-container').style.display = 'none';
        }
    } catch (e) {
        console.error('Status check failed:', e);
    }
}

async function authUser() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = '';

    if (!username || !password) {
        errorDiv.textContent = 'Заполни все поля';
        return;
    }

    try {
        const mode = document.getElementById('submit-btn').dataset.mode || 'login';
        const endpoint = mode === 'register' ? '/register' : '/login';
        
        const res = await fetch(endpoint, {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await res.json();

        if (data.success) {
            closeAuth();
            checkUserStatus();
        } else {
            errorDiv.textContent = data.error || 'Ошибка авторизации';
        }
    } catch (e) {
        errorDiv.textContent = 'Ошибка сети';
        console.error('Auth failed:', e);
    }
}

function showAuth(mode) {
    document.getElementById('auth-modal').style.display = 'flex';
    document.getElementById('modal-title').textContent = mode === 'register' ? '📝 Регистрация' : '🔑 Вход';
    document.getElementById('submit-btn').textContent = mode === 'register' ? 'Зарегистрироваться' : 'Войти';
    document.getElementById('submit-btn').dataset.mode = mode;
    
    const warning = document.getElementById('warning-text');
    if (mode === 'register') {
        warning.style.display = 'block';
    } else {
        warning.style.display = 'none';
    }
    
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    document.getElementById('error').textContent = '';
    document.getElementById('username').focus();
}

function closeAuth() {
    document.getElementById('auth-modal').style.display = 'none';
}

async function logout() {
    try {
        await fetch('/logout', {credentials: 'include', method: 'POST'});
    } catch (e) {}
    location.reload();
}

async function loadLeaderboard() {
    try {
        const [snakeRes, guessRes] = await Promise.all([
            fetch('/top/snake', {credentials: 'include'}),
            fetch('/top/guess', {credentials: 'include'})
        ]);
        const snakeData = await snakeRes.json();
        const guessData = await guessRes.json();

        document.getElementById('snake-leaderboard').innerHTML = `
            <h4>🐍 Змейка</h4>
            ${snakeData.map((p, i) => `<div class="leader-item"><span>#${i+1} ${p.username}</span><span>${p.score}</span></div>`).join('')}
        `;
        document.getElementById('guess-leaderboard').innerHTML = `
            <h4>🎯 Угадайка</h4>
            ${guessData.map((p, i) => `<div class="leader-item"><span>#${i+1} ${p.username}</span><span>${p.score}</span></div>`).join('')}
        `;
    } catch (e) {
        console.error('Leaderboard load failed:', e);
    }
}

function backToMenu() {
    if (gameInterval) {
        clearInterval(gameInterval);
        gameInterval = null;
    }
    location.reload();
}

// 🐍 ЗМЕЙКА
function loadSnakeGame() {
    currentGame = 'snake';
    document.querySelector('.container').innerHTML = `
        <h1>🐍 Змейка</h1>
        <div id="game-info">Счёт: <span id="score">0</span> | Рекорд: <span id="highscore">0</span></div>
        <canvas id="gameCanvas" width="400" height="400"></canvas>
        <div style="text-align:center;margin:20px">
            <p>📱 Телефон: свайпы | 💻 Компьютер: стрелки</p>
            <button class="auth-btn" onclick="backToMenu()" style="width:200px">🏠 В меню</button>
        </div>
    `;
    
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    snake = {x:10,y:10,dx:0,dy:0,cells:[],maxCells:4};
    food = {x:Math.floor(Math.random()*38)+1,y:Math.floor(Math.random()*38)+1};
    gameData.score = 0;
    gameData.highscore = 0;

    canvas.addEventListener('click', restartSnake);
    
    document.addEventListener('keydown', (e) => {
        if (currentGame !== 'snake') return;
        if (e.key === 'ArrowLeft' && snake.dx === 0) { snake.dx = -1; snake.dy = 0; }
        if (e.key === 'ArrowUp' && snake.dy === 0) { snake.dx = 0; snake.dy = -1; }
        if (e.key === 'ArrowRight' && snake.dx === 0) { snake.dx = 1; snake.dy = 0; }
        if (e.key === 'ArrowDown' && snake.dy === 0) { snake.dx = 0; snake.dy = 1; }
    });

    let touchStartX = 0, touchStartY = 0;
    canvas.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    });
    canvas.addEventListener('touchend', (e) => {
        const touchEndX = e.changedTouches[0].clientX;
        const touchEndY = e.changedTouches[0].clientY;
        const diffX = touchStartX - touchEndX;
        const diffY = touchStartY - touchEndY;
        
        if (Math.abs(diffX) > Math.abs(diffY)) {
            if (diffX > 0 && snake.dx === 0) { snake.dx = -1; snake.dy = 0; }
            else if (diffX < 0 && snake.dx === 0) { snake.dx = 1; snake.dy = 0; }
        } else {
            if (diffY > 0 && snake.dy === 0) { snake.dx = 0; snake.dy = -1; }
            else if (diffY < 0 && snake.dy === 0) { snake.dx = 0; snake.dy = 1; }
        }
    });

    function updateSnake() {
        snake.x += snake.dx;
        snake.y += snake.dy;

        if (snake.x < 0 || snake.x >= 40 || snake.y < 0 || snake.y >= 40) gameOver();
        
        for (let cell of snake.cells) {
            if (snake.x === cell.x && snake.y === cell.y) gameOver();
        }

        snake.cells.unshift({x: snake.x, y: snake.y});

        if (snake.x === food.x && snake.y === food.y) {
            gameData.score++;
            document.getElementById('score').textContent = gameData.score;
            food = {x:Math.floor(Math.random()*38)+1,y:Math.floor(Math.random()*38)+1};
        } else {
            snake.cells.pop();
        }

        if (snake.cells.length > snake.maxCells) snake.maxCells++;

        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, 400, 400);

        ctx.fillStyle = '#ff4444';
        ctx.fillRect(food.x*10, food.y*10, 10, 10);

        ctx.fillStyle = '#44ff44';
        for (let cell of snake.cells) {
            ctx.fillRect(cell.x*10, cell.y*10, 10, 10);
        }

        ctx.fillStyle = '#00ff88';
        ctx.fillRect(snake.x*10, snake.y*10, 10, 10);
    }

    function gameOver() {
        clearInterval(gameInterval);
        if (gameData.score > gameData.highscore) {
            gameData.highscore = gameData.score;
            document.getElementById('highscore').textContent = gameData.highscore;
            if (isLoggedIn) saveScore('snake');
        }
        ctx.fillStyle = 'rgba(255,0,0,0.7)';
        ctx.fillRect(0, 0, 400, 400);
        ctx.fillStyle = 'white';
        ctx.font = '30px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER', 200, 190);
        ctx.fillText(`Счёт: ${gameData.score}`, 200, 230);
        ctx.fillText('Кликни для рестарта', 200, 270);
    }

    function restartSnake() {
        if (gameInterval) clearInterval(gameInterval);
        snake = {x:10,y:10,dx:0,dy:0,cells:[],maxCells:4};
        food = {x:Math.floor(Math.random()*38)+1,y:Math.floor(Math.random()*38)+1};
        gameData.score = 0;
        gameInterval = setInterval(updateSnake, 200);
    }

    gameInterval = setInterval(updateSnake, 200);
}

// 🎯 УГАДАЙКА 1-1000
function loadGuessGame() {
    currentGame = 'guess';
    secretNumber = Math.floor(Math.random() * 1000) + 1;
    attempts = 0;
    
    document.querySelector('.container').innerHTML = `
        <h1>🎯 Угадай число (1-1000)</h1>
        <div id="game-info">
            <span style="color:#44ff44">Ходов: <span id="attempts">0</span></span> | 
            <span style="color:#ffaa00">Рекорд: <span id="highscore">0</span></span>
        </div>
        <canvas id="guessCanvas" width="400" height="250" style="cursor:pointer"></canvas>
        <div style="text-align:center;margin:20px">
            <input type="number" id="guessInput" min="1" max="1000" placeholder="1-1000" 
                   style="padding:15px;font-size:20px;border:3px solid #44ff44;border-radius:10px;background:#2a2a2a;color:white;width:220px">
            <br><br>
            <button class="auth-btn" onclick="checkGuess()" style="width:160px;margin:5px">✅ Проверить</button>
            <button class="auth-btn" onclick="clearGuess()" style="width:160px;margin:5px;background:#666">🔄 Очистить</button>
            <br><br>
            <button class="auth-btn" onclick="backToMenu()" style="width:200px">🏠 В меню</button>
        </div>
        <div id="hint" style="text-align:center;color:#ffaa00;font-size:18px;margin:10px;font-weight:bold"></div>
    `;
    
    gameData.highscore = 0;
    updateGuessCanvas();
    
    document.getElementById('guessInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') checkGuess();
    });
    
    document.getElementById('guessCanvas').addEventListener('click', checkGuess);
}

function updateGuessCanvas() {
    const canvas = document.getElementById('guessCanvas');
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, 400, 250);
    
    ctx.fillStyle = '#44ff44';
    ctx.font = 'bold 26px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('🎯 Угадай число от 1 до 1000', 200, 60);
    ctx.font = 'bold 22px Arial';
    ctx.fillText(`Ходов: ${attempts}`, 200, 110);
    
    const progress = attempts / 20;
    ctx.fillStyle = '#ff4444';
    ctx.fillRect(50, 140, 300 * progress, 20);
    ctx.strokeStyle = '#44ff44';
    ctx.lineWidth = 3;
    ctx.strokeRect(50, 140, 300, 20);
    
    ctx.fillStyle = '#00ff88';
    ctx.font = '20px Arial';
    ctx.fillText(`Прогресс: ${Math.round(progress*100)}%`, 200, 190);
}

function checkGuess() {
    const guess = parseInt(document.getElementById('guessInput').value);
    if (!guess || guess < 1 || guess > 1000) {
        document.getElementById('hint').textContent = '❌ Число от 1 до 1000!';
        document.getElementById('hint').style.color = '#ff4444';
        return;
    }

    attempts++;
    document.getElementById('attempts').textContent = attempts;
    document.getElementById('guessInput').value = '';
    document.getElementById('hint').textContent = '';

    if (guess === secretNumber) {
        const score = Math.max(0, 1000 - attempts * 30);
        if (score > gameData.highscore) {
            gameData.highscore = score;
            document.getElementById('highscore').textContent = gameData.highscore;
            if (isLoggedIn) saveScore('guess');
        }
        document.getElementById('hint').innerHTML = `🎉 Угадал за <strong>${attempts}</strong> ходов! Очки: <strong>${score}</strong>`;
        document.getElementById('hint').style.color = '#44ff44';
        setTimeout(() => loadGuessGame(), 3000);
    } else if (attempts >= 20) {
        document.getElementById('hint').innerHTML = `💀 Проиграл! Было <strong>${secretNumber}</strong>`;
        document.getElementById('hint').style.color = '#ff4444';
        setTimeout(() => loadGuessGame(), 3000);
    } else {
        let hintText = guess < secretNumber ? '📈 Больше!' : '📉 Меньше!';
        const diff = Math.abs(guess - secretNumber);
        if (diff <= 10) hintText += ' (очень близко!)';
        else if (diff <= 50) hintText += ' (ближе)';
        
        document.getElementById('hint').textContent = hintText;
        document.getElementById('hint').style.color = '#ffaa00';
    }
    
    updateGuessCanvas();
}

function clearGuess() {
    document.getElementById('guessInput').value = '';
    document.getElementById('guessInput').focus();
    document.getElementById('hint').textContent = '';
}

// 🏆 ТУРНИР
async function loadTournament() {
    currentGame = 'tournament';
    try {
        const res = await fetch('/tournament');
        const data = await res.json();
        
        document.querySelector('.container').innerHTML = `
            <h1>🏆 АКТИВНЫЙ ТУРНИР</h1>
            <div id="tournament-info" style="text-align:center;color:#ffaa00;font-size:18px;margin:20px">
                <div>🕐 До конца: <span id="countdown">-</span></div>
                <div>ID: <strong>${data.id}</strong></div>
            </div>
            
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:30px;margin:30px 0">
                <div class="leaderboard">
                    <h3>🐍 Змейка</h3>
                    <div id="tournament-snake-top"></div>
                    <div style="margin-top:20px;color:#44ff44;font-size:20px">
                        🎁 <strong>1-е место: 1000 очков</strong><br>
                        🎁 <strong>2-е место: 500 очков</strong><br>
                        🎁 <strong>3-е место: 250 очков</strong>
                    </div>
                </div>
                
                <div class="leaderboard">
                    <h3>🎯 Угадайка</h3>
                    <div id="tournament-guess-top"></div>
                    <div style="margin-top:20px;color:#44ff44;font-size:20px">
                        🎁 <strong>1-е место: 1000 очков</strong><br>
                        🎁 <strong>2-е место: 500 очков</strong><br>
                        🎁 <strong>3-е место: 250 очков</strong>
                    </div>
                </div>
            </div>
            
            <div style="text-align:center">
                <button class="auth-btn" onclick="backToMenu()" style="width:250px;font-size:18px">🏠 В меню</button>
            </div>
        `;
        
        // ✅ ТОП-3
        document.getElementById('tournament-snake-top').innerHTML = 
            data.snake_top.map((p, i) => 
                `<div class="leader-item"><span>🥇${i+1} ${p[0]}</span><span>${p[1]}</span></div>`
            ).join('') || '<div style="text-align:center;color:#666">Никто не играл</div>';
        
        document.getElementById('tournament-guess-top').innerHTML = 
            data.guess_top.map((p, i) => 
                `<div class="leader-item"><span>🥇${i+1} ${p[0]}</span><span>${p[1]}</span></div>`
            ).join('') || '<div style="text-align:center;color:#666">Никто не играл</div>';
        
        // ✅ ТАЙМЕР
        updateCountdown(data.end_time);
        setInterval(() => updateCountdown(data.end_time), 1000);
        
    } catch (e) {
        document.querySelector('.container').innerHTML = `
            <h1>🏆 ТУРНИР</h1>
            <div style="text-align:center;color:#ff4444">Ошибка загрузки турнира</div>
            <button class="auth-btn" onclick="backToMenu()" style="width:250px">🏠 В меню</button>
        `;
    }
}

function updateCountdown(endTimeISO) {
    const endTime = new Date(endTimeISO).getTime();
    const now = new Date().getTime();
    const distance = endTime - now;
    
    if (distance < 0) {
        document.getElementById('countdown').textContent = 'Турнир завершён!';
        return;
    }
    
    const hours = Math.floor(distance / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);
    
    document.getElementById('countdown').textContent = 
        `${hours}ч ${minutes}м ${seconds}с`;
}

// ✅ УЛУЧШЕННЫЙ saveScore (личный + турнир)
async function saveScore(game) {
    if (!isLoggedIn) return;
    
    try {
        // Личная БД
        await fetch(`/save_score/${game}`, {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({highscore: gameData.highscore})
        });
        
        // Турнирная БД
        await fetch(`/save_tournament_score/${game}`, {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({score: gameData.highscore})
        });
        
        loadLeaderboard();
    } catch (e) {
        console.error('Save score failed:', e);
    }
}

// ✅ ИНИЦИАЛИЗАЦИЯ
document.addEventListener('DOMContentLoaded', function() {
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
        submitBtn.onclick = authUser;
        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();
            authUser();
        });
        console.log('✅ Кнопка авторизации привязана!');
    }
    checkUserStatus();
});
