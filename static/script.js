let currentGame = '';
let isLoggedIn = false;

async function checkUserStatus() {
    try {
        const res = await fetch('/status', {credentials: 'include'});
        const data = await res.json();
        if (data.logged_in) {
            document.getElementById('status').textContent = `👋 ${data.username}`;
            document.getElementById('logout').style.display = 'inline-block';
            isLoggedIn = true;
        }
    } catch(e) {}
}

async function authUser() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const modalTitle = document.getElementById('modal-title');
    const mode = modalTitle.dataset.mode || (modalTitle.textContent.includes('РЕГИСТРАЦИЯ') ? 'register' : 'login');
    const endpoint = mode === 'register' ? '/register' : '/login';
    
    document.getElementById('error').textContent = '';
    try {
        const res = await fetch(endpoint, {
            method: 'POST', credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('status').textContent = `👋 ${data.username}`;
            document.getElementById('logout').style.display = 'inline-block';
            closeAuth();
            isLoggedIn = true;
        } else {
            document.getElementById('error').textContent = data.error || 'Ошибка';
        }
    } catch(e) {
        document.getElementById('error').textContent = 'Сервер недоступен';
    }
}

async function logout() {
    await fetch('/logout', {method: 'POST', credentials: 'include'});
    document.getElementById('status').textContent = '👋 Гость';
    document.getElementById('logout').style.display = 'none';
    isLoggedIn = false;
}

async function loadGame(game) {
    currentGame = game;
    document.getElementById('game-container').style.display = 'block';
    if (game === 'guess') loadGuessGame();
    else if (game === 'snake') loadSnakeGame();
    loadLeaderboard(game);
}

async function loadLeaderboard(game) {
    try {
        const res = await fetch(`/top/${game}`);
        const leaders = await res.json();
        const list = document.getElementById('leaders-list');
        if (list) {
            list.innerHTML = leaders.length ? 
                leaders.map((p,i) => `<div class="leader-item"><span>${i+1}. ${p.username}</span><span>${p.score}</span></div>`).join('') : 
                '<div style="text-align:center;color:#aaa;">Пока нет рекордов</div>';
            document.getElementById('leaderboard').style.display = 'block';
        }
    } catch(e) {}
}

async function saveScore(game, score) {
    if (!isLoggedIn) {
        alert('🔐 Войди для рекордов!');
        return;
    }
    try {
        await fetch('/save_score', {
            method: 'POST', credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({game, score})
        });
        loadLeaderboard(game);
    } catch(e) {}
}

// 🎯 УГАДАЙ ЧИСЛО (HTML версия — НЕ ломается)
function loadGuessGame() {
    const canvas = document.getElementById('gameCanvas');
    canvas.style.display = 'none';
    
    // ✅ HTML ИГРА
    document.getElementById('game-container').innerHTML = `
        <div style="padding:30px;text-align:center;font-family:Arial;background:rgba(0,0,0,0.3);border-radius:20px;max-width:500px;margin:0 auto">
            <h2 style="font-size:36px;margin-bottom:20px">🎯 УГАДАЙ ЧИСЛО (1-100)</h2>
            <div id="currentGuess" style="font-size:48px;font-weight:bold;color:#44ff88;margin:30px 0;min-height:60px">?</div>
            <div id="attemptsDisplay" style="font-size:28px;color:#ffaa00;margin:20px 0">Попыток: <span id="attempts">7</span></div>
            <div id="hint" style="font-size:36px;font-weight:bold;margin:40px 0;min-height:70px;line-height:70px"></div>
            
            <div style="margin:30px 0">
                <input id="guessInput" type="number" min="1" max="100" 
                       style="font-size:28px;padding:25px 20px;width:300px;border-radius:20px;border:3px solid #44ff44;background:rgba(255,255,255,0.95);text-align:center;font-weight:bold"
                       placeholder="Введите число">
            </div>
            
            <div style="margin:40px 0">
                <button onclick="checkGuess()" style="font-size:24px;padding:20px 50px;margin:10px;border:none;border-radius:20px;background:#44ff44;color:black;font-weight:bold;min-width:200px;cursor:pointer">✅ ПРОВЕРИТЬ</button>
                <button onclick="clearGuess()" style="font-size:24px;padding:20px 50px;margin:10px;border:none;border-radius:20px;background:#ff6b6b;color:white;font-weight:bold;min-width:200px;cursor:pointer">🗑️ ОЧИСТИТЬ</button>
            </div>
            
            <div id="gameOver" style="font-size:24px;color:#ff4444;margin-top:30px;display:none">F5 — новая игра</div>
        </div>
        <div id="leaderboard" class="leaderboard" style="display:block">
            <h3>🏆 ТОП-10</h3>
            <div id="leaders-list"></div>
        </div>
    `;
    
    window.guessSecret = Math.floor(Math.random() * 100) + 1;
    window.guessAttempts = 7;
    
    document.getElementById('guessInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') checkGuess();
    });
    document.getElementById('guessInput').focus();
    loadLeaderboard('guess');
}

window.checkGuess = function() {
    const input = document.getElementById('guessInput');
    const num = parseInt(input.value);
    
    if (isNaN(num) || num < 1 || num > 100) {
        showGuessHint('❌ Число от 1 до 100!', '#ff4444');
        input.style.borderColor = '#ff4444';
        return;
    }
    
    window.guessAttempts--;
    document.getElementById('attempts').textContent = window.guessAttempts;
    
    if (num === window.guessSecret) {
        const score = Math.max(100, 1000 - (7 - window.guessAttempts) * 100);
        if (isLoggedIn) saveScore('guess', score);
        showGuessHint(`✅ ПОБЕДА! ${score} очков! 🎉`, '#44ff88');
        input.disabled = true;
        input.style.borderColor = '#44ff88';
    } else if (window.guessAttempts === 0) {
        showGuessHint(`💀 Было: ${window.guessSecret}`, '#ff4444');
        document.getElementById('gameOver').style.display = 'block';
        input.disabled = true;
    } else if (num < window.guessSecret) {
        showGuessHint('⬆️ БОЛЬШЕ', '#ffaa00');
    } else {
        showGuessHint('⬇️ МЕНЬШЕ', '#ffaa00');
    }
    input.value = '';
    input.style.borderColor = '#44ff44';
};

window.clearGuess = function() {
    const input = document.getElementById('guessInput');
    input.value = '';
    document.getElementById('hint').innerHTML = '';
    input.style.borderColor = '#44ff44';
};

window.showGuessHint = function(message, color) {
    document.getElementById('hint').innerHTML = `<span style="color:${color}">${message}</span>`;
};

// 🐍 ЗМЕЙКА (canvas версия)
function loadSnakeGame() {
    const canvas = document.getElementById('gameCanvas');
    canvas.width = 500;
    canvas.height = 400;
    canvas.style.display = 'block';
    const ctx = canvas.getContext('2d');
    
    let snake = [{x: 10, y: 10}];
    let dx = 1, dy = 0;
    let food = {x: 15, y: 15};
    let score = 0;
    let gameRunning = true;
    
    const GRID_WIDTH = 25;
    const GRID_HEIGHT = 20;
    const CELL_SIZE = 20;
    
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (!gameRunning) {
            ctx.fillStyle = 'rgba(0,0,0,0.9)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#ff4444';
            ctx.font = 'bold 48px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('GAME OVER', 250, 220);
            ctx.font = 'bold 36px Arial';
            ctx.fillStyle = '#ffffff';
            ctx.fillText(`Счёт: ${score}`, 250, 270);
            ctx.font = '24px Arial';
            ctx.fillStyle = '#44ff44';
            ctx.fillText('Кликни для рестарта', 250, 320);
            ctx.textAlign = 'left';
            return;
        }
        
        snake.forEach((part, i) => {
            ctx.fillStyle = i === 0 ? '#44ff88' : '#44ff44';
            ctx.shadowColor = '#44ff44';
            ctx.shadowBlur = 10;
            ctx.fillRect(part.x*CELL_SIZE+1, part.y*CELL_SIZE+1, CELL_SIZE-2, CELL_SIZE-2);
            ctx.shadowBlur = 0;
        });
        
        ctx.fillStyle = '#ff4444';
        ctx.shadowColor = '#ff4444';
        ctx.shadowBlur = 15;
        ctx.beginPath();
        ctx.arc(food.x*CELL_SIZE+CELL_SIZE/2, food.y*CELL_SIZE+CELL_SIZE/2, CELL_SIZE/2-2, 0, Math.PI*2);
        ctx.fill();
        ctx.shadowBlur = 0;
        
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 36px Arial';
        ctx.fillText(`🐍 ${score}`, 20, 45);
        
        ctx.strokeStyle = '#444444';
        ctx.lineWidth = 4;
        ctx.strokeRect(0, 0, GRID_WIDTH*CELL_SIZE, GRID_HEIGHT*CELL_SIZE);
    }
    
    function gameLoop() {
        if (!gameRunning) return;
        
        const head = {x: snake[0].x + dx, y: snake[0].y + dy};
        
        if (head.x < 0 || head.x >= GRID_WIDTH || head.y < 0 || head.y >= GRID_HEIGHT) {
            gameRunning = false;
            if (isLoggedIn) saveScore('snake', score);
            draw();
            return;
        }
        
        for (let i = 0; i < snake.length; i++) {
            if (head.x === snake[i].x && head.y === snake[i].y) {
                gameRunning = false;
                if (isLoggedIn) saveScore('snake', score);
                draw();
                return;
            }
        }
        
        snake.unshift(head);
        
        if (head.x === food.x && head.y === food.y) {
            score++;
            food = {
                x: Math.floor(Math.random() * (GRID_WIDTH-4)) + 2,
                y: Math.floor(Math.random() * (GRID_HEIGHT-4)) + 2
            };
        } else {
            snake.pop();
        }
        
        draw();
        setTimeout(gameLoop, 130);
    }
    
    document.addEventListener('keydown', e => {
        if (!gameRunning) return;
        if (e.key === 'ArrowUp' && dy !== 1) dx = 0, dy = -1;
        if (e.key === 'ArrowDown' && dy !== -1) dx = 0, dy = 1;
        if (e.key === 'ArrowLeft' && dx !== 1) dx = -1, dy = 0;
        if (e.key === 'ArrowRight' && dx !== -1) dx = 1, dy = 0;
        e.preventDefault();
    });
    
    let touchStartX = 0, touchStartY = 0;
    canvas.addEventListener('touchstart', e => {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    });
    canvas.addEventListener('touchend', e => {
        if (!gameRunning) return;
        const deltaX = e.changedTouches[0].clientX - touchStartX;
        const deltaY = e.changedTouches[0].clientY - touchStartY;
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
            if (deltaX > 0 && dx !== -1) dx = 1, dy = 0;
            if (deltaX < 0 && dx !== 1) dx = -1, dy = 0;
        } else if (Math.abs(deltaY) > 50) {
            if (deltaY > 0 && dy !== -1) dx = 0, dy = 1;
            if (deltaY < 0 && dy !== 1) dx = 0, dy = -1;
        }
    });
    
    canvas.addEventListener('click', () => {
        if (!gameRunning) loadSnakeGame();
    });
    
    gameLoop();
    loadLeaderboard('snake');
}

function showAuth(mode) {
    document.getElementById('auth-modal').style.display = 'flex';
    const modalTitle = document.getElementById('modal-title');
    modalTitle.textContent = mode === 'register' ? '📝 РЕГИСТРАЦИЯ' : '🔑 ВХОД';
    modalTitle.dataset.mode = mode;
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    document.getElementById('error').textContent = '';
    document.getElementById('username').focus();
}

function closeAuth() {
    document.getElementById('auth-modal').style.display = 'none';
}

async function testAPI() {
    const res = await fetch('/test', {credentials: 'include'});
    console.log(await res.json());
}

// Горячие клавиши
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeAuth();
    if (document.getElementById('auth-modal').style.display === 'flex' && e.key === 'Enter') {
        authUser();
    }
});

async function checkUserStatus() {
    try {
        const res = await fetch('/status', {credentials: 'include'});
        const data = await res.json();
        if (data.logged_in) {
            document.getElementById('status').textContent = `👋 ${data.username}`;
            document.getElementById('logout').style.display = 'inline-block';
            isLoggedIn = true;
        }
    } catch(e) {
        // Тихо игнорируем ошибки
    }
}  // ← ✅ ЭТО КОНЕЦ ФУНКЦИИ
