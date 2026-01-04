let currentGame = ''; 
let isLoggedIn = false; 
let gameData = {score: 0, highscore: 0};
let gameInterval = null; 
let snake = {x:10,y:10,dx:0,dy:0,cells:[],maxCells:4};
let food = {x:15,y:15}; 
let secretNumber = 0; 
let attempts = 0;

async function checkUserStatus() {
    try {
        const res = await fetch('/status', {credentials: 'include'});
        const data = await res.json();
        if (data.logged_in) {
            document.getElementById('status').textContent = `👋 ${data.username}`;
            document.getElementById('logout').style.display = 'inline-block';
            isLoggedIn = true;
        }
    } catch (e) {}
}

async function authUser() {
    console.log('🔥 КНОПКА ЖИВА!');
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('warning-text');
    
    if (!username || !password) {
        errorDiv.textContent = '⚠️ Заполни все поля!';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        const res = await fetch('/' + document.getElementById('modal-title').textContent.toLowerCase(), {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await res.json();
        
        if (data.success) {
            checkUserStatus();
            closeAuth();
            loadLeaderboard();
        } else {
            errorDiv.textContent = data.error || 'Ошибка!';
            errorDiv.style.display = 'block';
        }
    } catch (e) {
        console.error('Auth error:', e);
    }
}

function showAuth(mode) {
    document.getElementById('auth-modal').style.display = 'flex';
    document.getElementById('modal-title').textContent = mode === 'login' ? 'Вход' : 'Регистрация';
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    document.getElementById('warning-text').style.display = 'none';
    console.log('🔧 showAuth вызвана:', mode);
}

function closeAuth() {
    document.getElementById('auth-modal').style.display = 'none';
}

function logout() {
    sessionStorage.clear();
    location.reload();
}

// 🐍 ЗМЕЙКА (полная)
function loadSnakeGame() {
    currentGame = 'snake';
    document.getElementById('game-container').innerHTML = `
        <canvas id="gameCanvas" width="400" height="400"></canvas>
        <div style="text-align:center;font-size:20px">
            <div>Счёт: <span id="snakeScore">0</span> | Рекорд: <span id="snakeHighscore">0</span></div>
            <div>Свайпай 📱 или WASD/Стрелки</div>
        </div>
    `;
    
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    
    canvas.focus();
    
    // СВАЙПЫ БЕЗ ПРОКРУТКИ
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
        
        if (Math.abs(diffX) > Math.abs(diffY)) {
            if (diffX > 0 && snake.dx !== 1) { snake.dx = -1; snake.dy = 0; }
            else if (diffX < 0 && snake.dx !== -1) { snake.dx = 1; snake.dy = 0; }
        } else {
            if (diffY > 0 && snake.dy !== 1) { snake.dx = 0; snake.dy = -1; }
            else if (diffY < 0 && snake.dy !== -1) { snake.dx = 0; snake.dy = 1; }
        }
    }, { passive: false });
    
    document.addEventListener('keydown', (e) => {
        if (currentGame !== 'snake') return;
        switch(e.key) {
            case 'ArrowLeft': if (snake.dx !== 1) { snake.dx = -1; snake.dy = 0; } break;
            case 'ArrowUp': if (snake.dy !== 1) { snake.dx = 0; snake.dy = -1; } break;
            case 'ArrowRight': if (snake.dx !== -1) { snake.dx = 1; snake.dy = 0; } break;
            case 'ArrowDown': if (snake.dy !== -1) { snake.dx = 0; snake.dy = 1; } break;
            case 'a': case 'A': if (snake.dx !== 1) { snake.dx = -1; snake.dy = 0; } break;
            case 'w': case 'W': if (snake.dy !== 1) { snake.dx = 0; snake.dy = -1; } break;
            case 'd': case 'D': if (snake.dx !== -1) { snake.dx = 1; snake.dy = 0; } break;
            case 's': case 'S': if (snake.dy !== -1) { snake.dx = 0; snake.dy = 1; } break;
        }
    });
    
    function updateSnake() {
        snake.x += snake.dx;
        snake.y += snake.dy;
        
        if (snake.x < 0) snake.x = canvas.width / 10 - 1;
        if (snake.y < 0) snake.y = canvas.height / 10 - 1;
        if (snake.x >= canvas.width / 10) snake.x = 0;
        if (snake.y >= canvas.height / 10) snake.y = 0;
        
        snake.cells.unshift({x: snake.x, y: snake.y});
        if (snake.cells.length > snake.maxCells) snake.cells.pop();
        
        if (snake.x === food.x && snake.y === food.y) {
            snake.maxCells++;
            food.x = Math.floor(Math.random() * 39) + 1;
            food.y = Math.floor(Math.random() * 39) + 1;
        }
        
        for (let cell of snake.cells.slice(1)) {
            if (snake.x === cell.x && snake.y === cell.y) {
                gameOver();
                return;
            }
        }
        
        ctx.fillStyle = '#111';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = 'lime';
        snake.cells.forEach((cell, index) => {
            ctx.fillRect(cell.x * 10, cell.y * 10, 10-index*0.2, 10-index*0.2);
        });
        
        ctx.fillStyle = 'red';
        ctx.fillRect(food.x * 10, food.y * 10, 10, 10);
        
        document.getElementById('snakeScore').textContent = snake.cells.length - 4;
        gameData.score = snake.cells.length - 4;
    }
    
    function gameOver() {
        if (gameInterval) clearInterval(gameInterval);
        ctx.fillStyle = 'rgba(255,0,0,0.7)';
        ctx.fillRect(0, 0, 400, 400);
        ctx.fillStyle = 'white';
        ctx.font = '30px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('GAME OVER', 200, 190);
        ctx.fillText(`Счёт: ${gameData.score}`, 200, 230);
        ctx.fillText('Кликни для рестарта', 200, 270);
        saveScore();
    }
    
    canvas.onclick = () => {
        snake = {x:10,y:10,dx:0,dy:0,cells:[],maxCells:4};
        food = {x:Math.floor(Math.random()*38)+1,y:Math.floor(Math.random()*38)+1};
        gameData.score = 0;
        gameInterval = setInterval(updateSnake, 200);
    };
    
    gameInterval = setInterval(updateSnake, 200);
}

// 🎯 УГАДАЙКА 1-10000 БЕЗЛИМИТ (НОВАЯ)
function loadGuessGame() {
    currentGame = 'guess';
    secretNumber = Math.floor(Math.random() * 10000) + 1; // 1-10000
    attempts = 0;
    
    document.getElementById('game-container').innerHTML = `
        <h1 style="text-align:center;margin:20px 0">🎯 Угадай число (1-10000)</h1>
        <div id="game-info" style="text-align:center;font-size:20px;margin:20px 0">
            <span style="color:#44ff44">Ходов: <span id="attempts">0</span></span> 
            <span style="color:#ffaa00">Очки: <span id="score">10000</span></span>
        </div>
        <div style="text-align:center">
            <input type="number" id="guessInput" min="1" max="10000" placeholder="1-10000" 
                   style="padding:15px;font-size:18px;width:280px;border-radius:10px;border:2px solid #444;margin:10px;display:block;margin:10px auto">
            <br>
            <button id="submitGuess" style="padding:15px 40px;font-size:18px;border-radius:10px;background:#44ff44;color:black;cursor:pointer;font-weight:bold">
                Проверить
            </button>
        </div>
        <div id="hint" style="font-size:28px;margin:30px 0;color:#ffaa00;text-align:center;font-weight:bold;min-height:40px"></div>
    `;
    
    document.getElementById('submitGuess').onclick = checkGuess;
    document.getElementById('guessInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') checkGuess();
    });
    document.getElementById('guessInput').focus();
}

function checkGuess() {
    const input = document.getElementById('guessInput');
    const guess = parseInt(input.value);
    attempts++;
    
    if (isNaN(guess) || guess < 1 || guess > 10000) {
        document.getElementById('hint').innerHTML = '❌ Введи число от 1 до 10000!';
        input.value = '';
        input.focus();
        return;
    }
    
    let hint = '';
    if (guess === secretNumber) {
        const score = Math.max(0, 10000 - attempts * 5);
        hint = `✅ <span style="color:#44ff44;font-size:32px">УГДАЛ за ${attempts} ходов!</span><br>Очки: ${score}`;
        gameData.score = score;
        saveScore();
        document.getElementById('hint').innerHTML = hint;
        setTimeout(() => {
            document.getElementById('game-container').innerHTML = `
                <h2 style="text-align:center;color:#44ff44">🎉 ПОЗДРАВЛЯЕМ! 🎉</h2>
                <p style="text-align:center;font-size:24px">Угадал за <strong>${attempts}</strong> ходов!</p>
                <p style="text-align:center;font-size:20px">Очки: <strong>${score}</strong></p>
                <div style="text-align:center;margin:30px">
                    <button onclick="loadGamesMenu()" style="padding:15px 30px;font-size:18px;background:#44ff44;color:black;border:none;border-radius:10px;cursor:pointer">
                        🎮 В главное меню
                    </button>
                </div>
            `;
        }, 3000);
    } else if (guess < secretNumber) {
        const diff = secretNumber - guess;
        if (diff <= 50) hint = '🔥 Очень близко! Больше! 🔥';
        else if (diff <= 200) hint = '➕ Больше!';
        else hint = '📈 Значительно больше!';
    } else {
        const diff = guess - secretNumber;
        if (diff <= 50) hint = '🔥 Очень близко! Меньше! 🔥';
        else if (diff <= 200) hint = '➖ Меньше!';
        else hint = '📉 Значительно меньше!';
    }
    
    document.getElementById('attempts').textContent = attempts;
    document.getElementById('score').textContent = Math.max(0, 10000 - attempts * 5);
    document.getElementById('hint').textContent = hint;
    input.value = '';
    input.focus();
}

function saveScore() {
    if (!isLoggedIn || gameData.score === 0) return;
    
    fetch('/save_score', {
        method: 'POST',
        credentials: 'include',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({score: gameData.score})
    }).catch(e => console.error('Save error:', e));
}

async function loadLeaderboard() {
    try {
        const res = await fetch('/leaderboard');
        const leaders = await res.json();
        const list = document.getElementById('leaderboard-list');
        list.innerHTML = leaders.map((player, i) => 
            `<div class="leader-item">${i+1}. ${player.username} - ${player.score}</div>`
        ).join('');
    } catch (e) {}
}

function loadGamesMenu() {
    document.getElementById('gamesMenu').style.display = 'grid';
    document.getElementById('game-container').innerHTML = '';
}

// ТРОЙНОЙ ФИКС КНОПОК
document.addEventListener('DOMContentLoaded', () => {
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
        submitBtn.onclick = () => { authUser(); return false; };
        submitBtn.onmousedown = () => { authUser(); return false; };
        console.log('🔧 Кнопка авторизации привязана при загрузке!');
    }
    
    checkUserStatus();
    loadLeaderboard();
    setInterval(loadLeaderboard, 30000);
});
