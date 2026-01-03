let currentGame = '';
let isLoggedIn = false;
let gameData = { score: 0, highscore: 0 };

async function checkUserStatus() {
    try {
        const res = await fetch('/status', {credentials: 'include'});
        const data = await res.json();
        if (data.logged_in) {
            document.getElementById('status').textContent = `👋 ${data.username}`;
            document.querySelector('.auth-buttons').style.display = 'none';
            document.getElementById('logout').style.display = 'inline-block';
            isLoggedIn = true;
            loadLeaderboard();
        }
    } catch (e) {
        console.log('👋 Гость');
    }
}

async function authUser() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const mode = document.getElementById('modal-title').dataset.mode;
    const errorDiv = document.getElementById('error');
    
    if (username.length < 3) {
        errorDiv.textContent = '❌ Имя слишком короткое (минимум 3 символа)';
        return;
    }
    if (password.length < 6) {
        errorDiv.textContent = '❌ Пароль слишком короткий (минимум 6 символов)';
        return;
    }
    
    try {
        const res = await fetch('/auth', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({username, password, mode})
        });
        const data = await res.json();
        if (data.success) {
            closeAuth();
            checkUserStatus();
            loadLeaderboard();
        } else {
            errorDiv.textContent = data.message || '❌ Ошибка авторизации';
        }
    } catch (e) {
        errorDiv.textContent = '❌ Ошибка сети';
    }
}

async function logout() {
    await fetch('/logout', {credentials: 'include'});
    isLoggedIn = false;
    document.getElementById('status').textContent = '👋 Гость';
    document.querySelector('.auth-buttons').style.display = 'flex';
    document.getElementById('logout').style.display = 'none';
    document.getElementById('leaders-list').innerHTML = '';
    document.getElementById('leaderboard').style.display = 'none';
}

function showAuth(mode) {
    console.log('🔧 showAuth вызвана:', mode); // ✅ ОТЛАДКА
    
    document.getElementById('auth-modal').style.display = 'flex';
    const modalTitle = document.getElementById('modal-title');
    modalTitle.textContent = mode === 'register' ? '📝 РЕГИСТРАЦИЯ' : '🔑 ВХОД';
    modalTitle.dataset.mode = mode;
    
    // ✅ ПРЕДУПРЕЖДЕНИЕ — ГАРАНТИРОВАННО РАБОТАЕТ
    const warning = document.getElementById('warning-text');
    console.log('🔧 Warning найден:', warning); // ✅ ОТЛАДКА
    
    if (warning) {
        warning.style.display = (mode === 'register') ? 'block' : 'none';
        console.log('🔧 Warning видимость:', warning.style.display); // ✅ ОТЛАДКА
    } else {
        console.error('❌ #warning-text НЕ НАЙДЕН!');
    }
    
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    document.getElementById('error').textContent = '';
    document.getElementById('username').focus();
}

function closeAuth() {
    document.getElementById('auth-modal').style.display = 'none';
}

async function loadLeaderboard() {
    try {
        const res = await fetch('/leaderboard', {credentials: 'include'});
        const data = await res.json();
        const list = document.getElementById('leaders-list');
        list.innerHTML = '';
        
        data.slice(0, 10).forEach((player, i) => {
            const div = document.createElement('div');
            div.className = 'leader-item';
            div.innerHTML = `<span style="color:#44ff44">${i+1}. ${player.username}</span><span style="color:#ffaa00">${player.highscore}</span>`;
            list.appendChild(div);
        });
        document.getElementById('leaderboard').style.display = 'block';
    } catch (e) {
        console.log('Лидерборд недоступен');
    }
}

function loadGame(game) {
    currentGame = game;
    document.querySelector('.games-grid').style.display = 'none';
    document.getElementById('game-container').style.display = 'block';
    document.getElementById('leaderboard').style.display = 'none';
    
    if (game === 'guess') loadGuessNumber();
    else if (game === 'snake') loadSnake();
}

function backToMenu() {
    document.querySelector('.games-grid').style.display = 'grid';
    document.getElementById('game-container').style.display = 'none';
    document.getElementById('gameCanvas').style.display = 'none';
    currentGame = '';
}

function loadGuessNumber() {
    document.getElementById('gameCanvas').style.display = 'none';
    document.getElementById('game-container').innerHTML = `
        <div style="text-align:center;padding:40px;background:linear-gradient(145deg, rgba(0,50,0,0.95), rgba(0,30,0,0.95));border-radius:25px;border:3px solid #44ff44;box-shadow:0 0 40px rgba(68,255,68,0.5)">
            <h2 style="color:#44ff44;font-size:28px;margin:0 0 20px 0;text-shadow:0 0 15px #44ff44">🎯 УГАДАЙ ЧИСЛО (1-100)</h2>
            <p style="color:#ccc;font-size:18px">Твоя лучшая попытка: <strong id="best-guess" style="color:#ffaa00">${gameData.highscore || 0}</strong></p>
            <input type="number" id="guess-input" min="1" max="100" style="padding:20px;font-size:22px;width:250px;border-radius:15px;border:3px solid #44ff44;background:#000;color:#44ff44;margin:25px 0">
            <br>
            <button onclick="checkGuess()" style="padding:20px 40px;font-size:22px;background:linear-gradient(45deg, #44ff44, #00ff88);color:black;border:none;border-radius:15px;cursor:pointer;font-weight:bold;box-shadow:0 8px 25px rgba(68,255,68,0.5)">✅ УГАДАТЬ</button>
            <br><br>
            <p id="guess-feedback" style="font-size:22px;color:#ffaa00;font-weight:bold;margin:20px 0"></p>
            <button onclick="backToMenu()" style="padding:15px 30px;background:#ff4444;color:white;border:none;border-radius:15px;cursor:pointer;font-size:18px;font-weight:bold">🔙 В МЕНЮ</button>
        </div>
    `;
    document.getElementById('guess-input').focus();
}

function checkGuess() {
    const guess = parseInt(document.getElementById('guess-input').value);
    const feedback = document.getElementById('guess-feedback');
    
    if (isNaN(guess) || guess < 1 || guess > 100) {
        feedback.textContent = '❌ Число от 1 до 100!';
        return;
    }
    
    const target = Math.floor(Math.random() * 100) + 1;
    let message = '';
    
    if (guess === target) {
        message = `🎉 УГАДАЛ! Было ${target}`;
        if (guess < gameData.highscore || gameData.highscore === 0) {
            gameData.highscore = guess;
            saveScore();
        }
    } else if (guess < target) {
        message = `📈 Загаданное число БОЛЬШЕ`;
    } else {
        message = `📉 Загаданное число МЕНЬШЕ`;
    }
    
    feedback.textContent = message;
}

function loadSnake() {
    const canvas = document.getElementById('gameCanvas');
    canvas.style.display = 'block';
    const ctx = canvas.getContext('2d');
    const grid = 20;
    let snake = [{x: 10, y: 10}];
    let food = {x: 15, y: 15};
    let dx = 0, dy = 0;
    let score = 0;
    
    function draw() {
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#44ff44';
        snake.forEach(part => ctx.fillRect(part.x * grid, part.y * grid, grid - 2, grid - 2));
        ctx.fillStyle = '#ff4444';
        ctx.fillRect(food.x * grid, food.y * grid, grid - 2, grid - 2);
        ctx.fillStyle = '#44ff44';
        ctx.font = '24px Arial';
        ctx.fillText(`Очки: ${score}`, 20, 30);
    }
    
    function update() {
        const head = {x: snake[0].x + dx, y: snake[0].y + dy};
        if (head.x < 0 || head.x >= 25 || head.y < 0 || head.y >= 20) {
            gameOver(score);
            return;
        }
        for (let part of snake) {
            if (head.x === part.x && head.y === part.y) {
                gameOver(score);
                return;
            }
        }
        snake.unshift(head);
        if (head.x === food.x && head.y === food.y) {
            score++;
            food = {x: Math.floor(Math.random() * 25), y: Math.floor(Math.random() * 20)};
        } else {
            snake.pop();
        }
        draw();
    }
    
    function gameOver(finalScore) {
        if (finalScore > gameData.highscore) {
            gameData.highscore = finalScore;
            saveScore();
        }
        alert(`🐍 Игра окончена! Очки: ${finalScore}`);
        backToMenu();
    }
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowUp' && dy !== 1) { dx = 0; dy = -1; }
        if (e.key === 'ArrowDown' && dy !== -1) { dx = 0; dy = 1; }
        if (e.key === 'ArrowLeft' && dx !== 1) { dx = -1; dy = 0; }
        if (e.key === 'ArrowRight' && dx !== -1) { dx = 1; dy = 0; }
    });
    
    draw();
    setInterval(update, 150);
}

async function saveScore() {
    if (!isLoggedIn) return;
    try {
        await fetch('/save-score', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({highscore: gameData.highscore})
        });
        loadLeaderboard();
    } catch (e) {}
}

// ✅ СТАРТ
checkUserStatus();
