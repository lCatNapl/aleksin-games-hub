// 🎮 Игровой Хаб Назар — ВЕСЬ JavaScript
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
    } catch(e) {
        console.error('Status check:', e);
    }
}

async function authUser() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const isRegister = document.getElementById('modal-title').textContent.includes('Регистрация');
    const endpoint = isRegister ? '/register' : '/login';
    
    document.getElementById('error').textContent = '';
    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            credentials: 'include',
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
        console.error(e);
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
    
    if (game === 'guess') {
        loadGuessGame();
    } else if (game === 'snake') {
        loadSnakeGame();
    }
    loadLeaderboard(game);
}

async function loadLeaderboard(game) {
    try {
        const res = await fetch(`/top/${game}`, {credentials: 'include'});
        const leaders = await res.json();
        const list = document.getElementById('leaders-list');
        
        if (leaders.length === 0) {
            list.innerHTML = '<div style="text-align:center;color:#aaa;">Пока нет рекордов</div>';
        } else {
            list.innerHTML = leaders.map((player, i) => 
                `<div class="leader-item">
                    <span>${i+1}. ${player.username}</span>
                    <span>${player.score}</span>
                </div>`
            ).join('');
        }
        document.getElementById('leaderboard').style.display = 'block';
    } catch(e) {
        console.error('Leaderboard error:', e);
        document.getElementById('leaders-list').innerHTML = '<div>Ошибка загрузки топа</div>';
    }
}

// 🎯 ИГРА "УГАДАЙ ЧИСЛО"
function loadGuessGame() {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    let secret = Math.floor(Math.random() * 100) + 1;
    let attempts = 7;
    let guess = '';
    
    canvas.onclick = () => {}; // Очистка старой игры
    
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'white';
        ctx.font = 'bold 28px Arial';
        ctx.fillText(`🎯 Угадай число: ${guess || '?'} (1-100)`, 20, 60);
        ctx.font = '24px Arial';
        ctx.fillText(`Попыток: ${attempts}`, 20, 110);
        
        if (attempts === 0) {
            ctx.fillStyle = '#ff4444';
            ctx.font = 'bold 24px Arial';
            ctx.fillText(`Число было: ${secret}`, 20, 180);
            ctx.fillStyle = 'white';
            ctx.font = '20px Arial';
            ctx.fillText('F5 — новая игра', 20, 220);
        }
    }
    
    function checkGuess() {
        const num = parseInt(guess);
        if (isNaN(num) || num < 1 || num > 100) {
            alert('Введи число от 1 до 100');
            return;
        }
        
        attempts--;
        if (num === secret) {
            const score = 1000 - (7 - attempts) * 100;
            saveScore('guess', score);
            ctx.fillStyle = '#44ff44';
            ctx.font = 'bold 28px Arial';
            ctx.fillText('✅ ПОБЕДА!', 20, 160);
            ctx.font = '24px Arial';
            ctx.fillText(`Твой рекорд: ${score}`, 20, 200);
        } else if (attempts === 0) {
            ctx.fillStyle = '#ff4444';
            ctx.font = 'bold 28px Arial';
            ctx.fillText(`Число было: ${secret}`, 20, 180);
        } else if (num < secret) {
            ctx.fillStyle = '#ffaa00';
            ctx.fillText('⬆️ Больше!', 20, 160);
        } else {
            ctx.fillStyle = '#ffaa00';
            ctx.fillText('⬇️ Меньше!', 20, 160);
        }
        guess = '';
        draw();
    }
    
    // Цифры 0-9, Enter, Backspace
    function handleKey(e) {
        if (e.key >= '0' && e.key <= '9' && guess.length < 3) {
            guess += e.key;
            draw();
        } else if (e.key === 'Enter') {
            checkGuess();
        } else if (e.key === 'Backspace') {
            guess = guess.slice(0, -1);
            draw();
        }
    }
    
    document.removeEventListener('keydown', handleKey);
    document.addEventListener('keydown', handleKey);
    draw();
}

// 🐍 ИГРА "ЗМЕЙКА"
function loadSnakeGame() {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    let snake = [{x: 10, y: 10}];
    let dx = 1, dy = 0;
    let food = {x: Math.floor(Math.random() * 25), y: Math.floor(Math.random() * 20)};
    let score = 0;
    
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Змейка
        ctx.fillStyle = '#44ff44';
        snake.forEach((part, i) => {
            ctx.fillRect(part.x * 20, part.y * 20, 20 - (i > 0 ? 2 : 0), 20 - (i > 0 ? 2 : 0));
        });
        
        // Еда
        ctx.fillStyle = '#ff4444';
        ctx.fillRect(food.x * 20 + 4, food.y * 20 + 4, 12, 12);
        
        // Счёт
        ctx.fillStyle = 'white';
        ctx.font = 'bold 28px Arial';
        ctx.fillText(`🐍 Очки: ${score}`, 20, 40);
    }
    
    function gameLoop() {
        const head = {x: snake[0].x + dx, y: snake[0].y + dy};
        
        // Столкновение со стеной
        if (head.x < 0 || head.x >= 25 || head.y < 0 || head.y >= 20) {
            ctx.fillStyle = '#ff4444';
            ctx.font = 'bold 32px Arial';
            ctx.fillText('ИГРА ОКОНЧЕНА', 80, 200);
            return;
        }
        
        snake.unshift(head);
        
        // Еда съедена
        if (head.x === food.x && head.y === food.y) {
            score++;
            food = {x: Math.floor(Math.random() * 25), y: Math.floor(Math.random() * 20)};
            if (isLoggedIn) saveScore('snake', score);
        } else {
            snake.pop();
        }
        
        // Самоедение
        for (let i = 1; i < snake.length; i++) {
            if (head.x === snake[i].x && head.y === snake[i].y) {
                ctx.fillStyle = '#ff4444';
                ctx.font = 'bold 32px Arial';
                ctx.fillText('ИГРА ОКОНЧЕНА', 80, 200);
                return;
            }
        }
        
        draw();
        setTimeout(gameLoop, 150);
    }
    
    // Управление стрелками
    function handleSnakeKey(e) {
        if (e.key === 'ArrowUp' && dy !== 1) { dx = 0; dy = -1; }
        if (e.key === 'ArrowDown' && dy !== -1) { dx = 0; dy = 1; }
        if (e.key === 'ArrowLeft' && dx !== 1) { dx = -1; dy = 0; }
        if (e.key === 'ArrowRight' && dx !== -1) { dx = 1; dy = 0; }
    }
    
    document.removeEventListener('keydown', handleSnakeKey);
    document.addEventListener('keydown', handleSnakeKey);
    gameLoop();
}

async function saveScore(game, score) {
    if (!isLoggedIn) {
        alert('🔐 Войди для сохранения рекордов!');
        return;
    }
    try {
        await fetch('/save_score', {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({game, score})
        });
    } catch(e) {
        console.error('Save score failed:', e);
    }
}

function showAuth(mode) {
    document.getElementById('auth-modal').style.display = 'flex';
    document.getElementById('modal-title').textContent = 
        mode === 'register' ? '📝 РЕГИСТРАЦИЯ' : '🔑 ВХОД';
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    document.getElementById('error').textContent = '';
    document.getElementById('username').focus();
}

function closeAuth() {
    document.getElementById('auth-modal').style.display = 'none';
}

async function testAPI() {
    try {
        const res = await fetch('/test', {credentials: 'include'});
        console.log('🧪 API тест:', await res.json());
    } catch(e) {
        console.error('API тест failed:', e);
    }
}

// Горячие клавиши
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeAuth();
    if (document.getElementById('auth-modal').style.display === 'flex' && e.key === 'Enter') {
        authUser();
    }
});

// Запуск при загрузке
checkUserStatus();
