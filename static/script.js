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
    console.log('🚀 authUser() вызвана!');
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error'); 
    errorDiv.textContent = '';
    
    if (!username || !password) { 
        errorDiv.textContent = 'Заполни все поля'; 
        console.log('❌ Поля пустые');
        return; 
    }
    
    console.log(`🔐 Отправка ${username} на /login`);
    try {
        const mode = document.getElementById('submit-btn').dataset.mode || 'login';
        const endpoint = mode === 'register' ? '/register' : '/login';
        
        const res = await fetch(endpoint, {
            method: 'POST', credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await res.json();
        console.log('📡 Ответ сервера:', data);
        
        if (data.success) { 
            closeAuth(); 
            checkUserStatus(); 
            console.log('✅ АВТОРИЗАЦИЯ УСПЕШНА!');
        } else {
            errorDiv.textContent = data.error || 'Ошибка авторизации';
            console.log('❌ Ошибка:', data.error);
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
    document.getElementById('warning-text').style.display = mode === 'register' ? 'block' : 'none';
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
            ${snakeData.length ? snakeData.map((p, i) => `<div class="leader-item"><span>#${i+1} ${p.username}</span><span>${p.score}</span></div>`).join('') : '<div style="color:#666;text-align:center">Пока пусто</div>'}
        `;
        document.getElementById('guess-leaderboard').innerHTML = `
            <h4>🎯 Угадайка</h4>
            ${guessData.length ? guessData.map((p, i) => `<div class="leader-item"><span>#${i+1} ${p.username}</span><span>${p.score}</span></div>`).join('') : '<div style="color:#666;text-align:center">Пока пусто</div>'}
        `;
    } catch (e) {
        console.error('Leaderboard failed:', e);
        document.getElementById('snake-leaderboard').innerHTML = '<div style="color:#ff4444">Ошибка загрузки</div>';
        document.getElementById('guess-leaderboard').innerHTML = '<div style="color:#ff4444">Ошибка загрузки</div>';
    }
}

function backToMenu() {
    if (gameInterval) { 
        clearInterval(gameInterval); 
        gameInterval = null; 
    }
    location.reload();
}

// 🐍 ЗМЕЙКА С ФИКСОМ СВАЙПОВ
function loadSnakeGame() {
    currentGame = 'snake';
    document.querySelector('.container').innerHTML = `
        <h1>🐍 Змейка</h1>
        <div id="game-info">Счёт: <span id="score">0</span> | Рекорд: <span id="highscore">0</span></div>
        <canvas id="gameCanvas" width="400" height="400" style="border:2px solid #44ff44;border-radius:10px;background:#111;touch-action:none;display:block;margin:20px auto;"></canvas>
        <div style="text-align:center;margin:20px">
            <p>📱 Свайпы | 💻 Стрелки</p>
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
        e.preventDefault(); 
        touchStartX = e.touches[0].clientX; 
        touchStartY = e.touches[0].clientY;
    }, { passive: false });
    
    canvas.addEventListener('touchend', (e) => {
        e.preventDefault();
        const touchEndX = e.changedTouches[0].clientX;
        const touchEndY = e.changedTouches[0].clientY;
        const diffX = touchStartX - touchEndX;
        const diffY = touchStartY - touchEndY;
        
        if (Math.abs(diffX) > 30 || Math.abs(diffY) > 30) {
            if (Math.abs(diffX) > Math.abs(diffY)) {
                if (diffX > 0 && snake.dx === 0) { snake.dx = -1; snake.dy = 0; }
                else if (diffX < 0 && snake.dx === 0) { snake.dx = 1; snake.dy = 0; }
            } else {
                if (diffY > 0 && snake.dy === 0) { snake.dx = 0; snake.dy = -1; }
                else if (diffY < 0 && snake.dy === 0) { snake.dx = 0; snake.dy = 1; }
            }
        }
    }, { passive: false });

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
        
        ctx.fillStyle = '#000'; ctx.fillRect(0, 0, 400, 400);
        ctx.fillStyle = '#ff4444'; ctx.fillRect(food.x*10, food.y*10, 10, 10);
        ctx.fillStyle = '#44ff44'; 
        for (let cell of snake.cells) ctx.fillRect(cell.x*10, cell.y*10, 10, 10);
        ctx.fillStyle = '#00ff88'; 
        ctx.fillRect(snake.x*10, snake.y*10, 10, 10);
    }

    function gameOver() {
        clearInterval(gameInterval);
        if (isLoggedIn) saveScore('snake');
        if (gameData.score > gameData.highscore) {
            gameData.highscore = gameData.score;
            document.getElementById('highscore').textContent = gameData.highscore;
        }
        ctx.fillStyle = 'rgba(255,0,0,0.7)'; ctx.fillRect(0, 0, 400, 400);
        ctx.fillStyle = 'white'; ctx.font = '30px Arial'; ctx.textAlign = 'center';
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
            <span style="color:#44ff44">Ходов: <span id="attempts">0</span></span> 
            <span style="color:#ffaa00">Рекорд: <span id="highscore">0</span></span>
        </div>
        <div style="text-align:center;margin:20px 0">
            <input type="number" id="guessInput" min="1" max="1000" placeholder="1-1000" 
                   style="padding:15px;font-size:18px;width:200px;border-radius:10px;border:2px solid #444">
            <br><br>
            <canvas id="guessCanvas" width="400" height="50" 
                    style="border:2px solid #44ff44;border-radius:10px;cursor:pointer;margin:20px 0;background:#222"></canvas>
            <div id="hint" style="text-align:center;color:#ffaa00;font-size:18px;margin:10px;font-weight:bold"></div>
        </div>
        <button class="auth-btn" onclick="backToMenu()" style="width:200px">🏠 В меню</button>
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
    const progress = Math.min(attempts / maxAttempts, 1);
    
    ctx.fillStyle = '#222'; ctx.fillRect(0, 0, 400, 50);
    ctx.fillStyle = '#44ff44'; ctx.fillRect(0, 0, 400 * (1-progress), 50);
    ctx.fillStyle = '#ff4444'; ctx.fillRect(400 * (1-progress), 0, 400 * progress, 50);
    ctx.fillStyle = 'white'; ctx.font = '20px Arial'; ctx.textAlign = 'center';
    ctx.fillText(`Ход ${attempts}/${maxAttempts}`, 200, 30);
}

async function checkGuess() {
    if (attempts >= maxAttempts) {
        document.getElementById('hint').innerHTML = '<span style="color:#ff4444">⏰ Время вышло!</span>';
        if (isLoggedIn) saveScore('guess');
        return;
    }
    
    const guess = parseInt(document.getElementById('guessInput').value);
    attempts++;
    document.getElementById('attempts').textContent = attempts;
    document.getElementById('guessInput').value = '';
    updateGuessCanvas();
    
    let hint = '';
    if (guess === secretNumber) {
        const score = Math.max(0, 1000 - attempts * 30);
        hint = `<span style="color:#44ff44">🎉 УГАДАЛ за ${attempts} ходов! ${score} очков</span>`;
        if (isLoggedIn) saveScore('guess');
    } else if (attempts >= maxAttempts) {
        hint = `<span style="color:#ff4444">⏰ Не угадано: ${secretNumber}</span>`;
        if (isLoggedIn) saveScore('guess');
    } else if (guess < secretNumber) {
        const diff = secretNumber - guess;
        hint = diff <= 10 ? '🔥 Больше! (очень близко)' : '📈 Больше!';
    } else {
        const diff = guess - secretNumber;
        hint = diff <= 10 ? '🔥 Меньше! (очень близко)' : '📉 Меньше!';
    }
    document.getElementById('hint').innerHTML = hint;
}

async function saveScore(gameType) {
    if (!isLoggedIn) return;
    
    const score = gameType === 'snake' ? gameData.score : Math.max(0, 1000 - attempts * 30);
    console.log(`💾 Сохранение ${gameType}: ${score}`);
    
    try {
        const res = await fetch('/save', {
            method: 'POST', credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({game: gameType, score})
        });
        const data = await res.json();
        console.log('✅', gameType, 'сохранено:', data);
        
        if (data.highscore_updated) {
            gameData.highscore = data.highscore;
            document.getElementById('highscore')?.textContent = gameData.highscore;
        }
        loadLeaderboard();
        loadTournament();
    } catch (e) { 
        console.error('Save failed:', e); 
    }
}

async function loadTournament() {
    try {
        const res = await fetch('/tournament', {credentials: 'include'});
        const data = await res.json();
        
        if (data.active && !document.getElementById('tournament-container')) {
            document.body.insertAdjacentHTML('beforeend', `
                <div id="tournament-container" style="position:fixed;top:10px;right:10px;background:#1a1a1a;padding:15px;border-radius:15px;border:2px solid #ffaa00;max-width:300px;z-index:1000">
                    <div id="tournament-title" style="font-size:20px;color:#ffaa00;margin-bottom:10px"></div>
                    <div id="tournament-leaderboard" style="max-height:150px;overflow-y:auto;font-size:14px"></div>
                    <div style="color:#666;font-size:12px;margin-top:10px">🥇1-е: +1000 | 🥈2-е: +500 | 🥉3-е: +250</div>
                </div>
            `);
        }
        
        if (data.active) {
            const timeLeft = Math.max(0, data.ends_at - Date.now());
            const hours = Math.floor(timeLeft / 3600000);
            const minutes = Math.floor((timeLeft % 3600000) / 60000);
            
            document.getElementById('tournament-title').textContent = `🏆 Турнир (${hours}ч ${minutes}м)`;
            document.getElementById('tournament-leaderboard').innerHTML = 
                data.leaderboard.slice(0, 3).map((p, i) => 
                    `<div class="leader-item"><span>#${i+1} ${p.username}</span><span>${p.score}</span></div>`
                ).join('') + 
                (data.my_position ? `<div style="color:#44ff44">👤 Ты: #${data.my_position} ${data.my_score}</div>` : '');
        }
    } catch (e) { 
        console.error('Tournament load failed:', e); 
    }
}

// 🚨 ЭКСТРЕННЫЙ ТРОЙНОЙ ФИКС КНОПОК ДЛЯ RENDER
document.addEventListener('click', function(e) {
    if (e.target.id === 'submit-btn' || e.target.classList.contains('btn-primary')) {
        e.preventDefault(); e.stopPropagation();
        console.log('🚨 КНОПКА НАЙДЕНА ПО CLICK!');
        authUser();
    }
});

document.addEventListener('pointerdown', function(e) {
    if (e.target.id === 'submit-btn') {
        e.preventDefault(); e.stopPropagation();
        console.log('🚨 КНОПКА НАЙДЕНА ПО POINTERDOWN!');
        authUser();
    }
});

// ГАРАНТИЯ - каждые 2 сек проверяем привязку
setInterval(() => {
    const btn = document.getElementById('submit-btn');
    if (btn && !btn.onclick) {
        btn.onclick = () => { authUser(); return false; };
        console.log('🔧 КНОПКА ПЕРЕПРИВЯЗАНА!');
    }
}, 2000);

// ✅ ПОЛНАЯ ИНИЦИАЛИЗАЦИЯ
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎮 Aleksin Games Hub полностью загружен!');
    
    // CSS ФИКС ТОПА
    const style = document.createElement('style');
    style.textContent = `
        .leader-item { 
            display: flex !important; justify-content: space-between !important; 
            padding: 15px !important; margin: 10px 0 !important; 
            background: #2a2a2a !important; border-radius: 10px !important;
            font-size: 16px !important; min-height: 20px !important; 
        }
    `;
    document.head.appendChild(style);
    
    // ФИКС КНОПОК
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
        submitBtn.onclick = () => { authUser(); return false; };
        console.log('🔧 Кнопка авторизации привязана при загрузке!');
    }
    
    checkUserStatus();
    setInterval(loadTournament, 30000);
    loadTournament();
});
