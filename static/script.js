let currentGame = '';
let isLoggedIn = false;
let gameData = {score: 0, highscore: 0};
let gameInterval = null;
let snake = {x:10,y:10,dx:0,dy:0,cells:[],maxCells:4};
let food = {x:15,y:15};
let secretNumber = 0;
let attempts = 0;
let maxAttempts = 7;

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

    try {
        const endpoint = document.getElementById('submit-btn').dataset.mode === 'register' ? '/register' : '/login';
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

function loadGuessGame() {
    currentGame = 'guess';
    secretNumber = Math.floor(Math.random() * 100) + 1;
    attempts = 0;
    
    document.querySelector('.container').innerHTML = `
        <h1>🎯 Угадай число</h1>
        <div id="game-info">
            Попытка <span id="attempts">0</span>/7 | Рекорд: <span id="highscore">0</span>
        </div>
        <canvas id="guessCanvas" width="400" height="200" style="cursor:pointer"></canvas>
        <div style="text-align:center;margin:20px">
            <input type="number" id="guessInput" min="1" max="100" placeholder="1-100" style="padding:15px;font-size:20px;border:3px solid #44ff44;border-radius:10px;background:#2a2a2a;color:white;width:200px">
            <br><br>
            <button class="auth-btn" onclick="checkGuess()" style="width:150px;margin:5px">✅ Проверить</button>
            <button class="auth-btn" onclick="clearGuess()" style="width:150px;margin:5px;background:#666">🔄 Очистить</button>
            <br><br>
            <button class="auth-btn" onclick="backToMenu()" style="width:200px">🏠 В меню</button>
        </div>
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
    ctx.fillRect(0, 0, 400, 200);
    
    ctx.fillStyle = '#44ff44';
    ctx.font = '24px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`Загадай число от 1 до 100`, 200, 50);
    ctx.fillText(`Попыток: ${attempts}/${maxAttempts}`, 200, 100);
}

function checkGuess() {
    const guess = parseInt(document.getElementById('guessInput').value);
    if (!guess || guess < 1 || guess > 100) {
        alert('Введи число от 1 до 100');
        return;
    }

    attempts++;
    document.getElementById('attempts').textContent = attempts;
    document.getElementById('guessInput').value = '';

    if (guess === secretNumber) {
        if (attempts < maxAttempts - 2) {
            gameData.highscore = Math.max(gameData.highscore, 8 - attempts);
            document.getElementById('highscore').textContent = gameData.highscore;
            if (isLoggedIn) saveScore('guess');
        }
        alert(`✅ Угадал за ${attempts} попыток! Рекорд: ${gameData.highscore}`);
        loadGuessGame();
    } else if (attempts >= maxAttempts) {
        alert(`💀 Проиграл! Было ${secretNumber}`);
        loadGuessGame();
    } else {
        const hint = guess < secretNumber ? 'Больше!' : 'Меньше!';
        alert(hint);
    }
    updateGuessCanvas();
}

function clearGuess() {
    document.getElementById('guessInput').value = '';
    document.getElementById('guessInput').focus();
}

async function saveScore(game) {
    try {
        await fetch(`/save_score/${game}`, {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({highscore: gameData.highscore})
        });
        loadLeaderboard();
    } catch (e) {}
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('submit-btn').onclick = authUser;
    checkUserStatus();
});
