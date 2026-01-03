let currentGame = '';
let isLoggedIn = false;
let gameKeyHandler = null; // ✅ Фикс: одна игра за раз

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
        document.getElementByListener('error').textContent = 'Сервер недоступен';
    }
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

async function loadGame(game) {
    currentGame = game;
    document.getElementById('game-container').style.display = 'block';
    
    // ✅ Останавливаем старую игру
    if (gameKeyHandler) {
        document.removeEventListener('keydown', gameKeyHandler);
        gameKeyHandler = null;
    }
    
    if (game === 'guess') loadGuessGame();
    else if (game === 'snake') loadSnakeGame();
    loadLeaderboard(game);
}

async function loadLeaderboard(game) {
    try {
        const res = await fetch(`/top/${game}`);
        const leaders = await res.json();
        const list = document.getElementById('leaders-list');
        list.innerHTML = leaders.length ? 
            leaders.map((p,i) => `<div class="leader-item"><span>${i+1}. ${p.username}</span><span>${p.score}</span></div>`).join('') : 
            '<div style="text-align:center;color:#aaa;">Пока нет рекордов</div>';
        document.getElementById('leaderboard').style.display = 'block';
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
        loadLeaderboard(game); // ✅ Обновляем топ
    } catch(e) {}
}

// 🎯 УГАДАЙ ЧИСЛО (ПРАВИЛЬНО!)
function loadGuessGame() {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    let secret = Math.floor(Math.random() * 100) + 1;
    let attempts = 7;
    let guess = '';
    
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'white';
        ctx.font = 'bold 28px Arial';
        ctx.fillText(`🎯 ${guess || '?'} (1-100)`, 20, 60);
        ctx.font = '24px Arial';
        ctx.fillText(`Попыток: ${attempts}`, 20, 110);
        
        if (attempts === 0) {
            ctx.fillStyle = '#ff4444';
            ctx.font = 'bold 24px Arial';
            ctx.fillText(`Было: ${secret}`, 20, 180);
            ctx.fillStyle = 'white';
            ctx.font = '18px Arial';
            ctx.fillText('F5 — новая игра', 20, 220);
        }
    }
    
    function checkGuess() {
        const num = parseInt(guess);
        if (isNaN(num) || num < 1 || num > 100) {
            alert('Число 1-100!');
            return;
        }
        attempts--;
        if (num === secret) {
            const score = Math.max(100, 1000 - (7-attempts)*100);
            saveScore('guess', score);
            ctx.fillStyle = '#44ff44';
            ctx.font = 'bold 32px Arial';
            ctx.fillText('✅ ПОБЕДА!', 120, 160);
            ctx.font = '24px Arial';
            ctx.fillStyle = 'white';
            ctx.fillText(`Рекорд: ${score}`, 140, 200);
        } else if (attempts === 0) {
            ctx.fillStyle = '#ff4444';
            ctx.font = 'bold 28px Arial';
            ctx.fillText(`Было: ${secret}`, 120, 180);
        } else if (num < secret) {
            ctx.fillStyle = '#ffaa00';
            ctx.fillText('⬆️ БОЛЬШЕ', 140, 160);
        } else {
            ctx.fillStyle = '#ffaa00';
            ctx.fillText('⬇️ МЕНЬШЕ', 140, 160);
        }
        guess = '';
        draw();
    }
    
    // ✅ УНИКАЛЬНЫЙ обработчик только для этой игры
    gameKeyHandler = (e) => {
        if (e.key >= '0' && e.key <= '9' && guess.length < 3) {
            guess += e.key;
            draw();
            e.preventDefault();
        } else if (e.key === 'Enter' && currentGame === 'guess') {
            checkGuess();
            e.preventDefault();
        } else if (e.key === 'Backspace') {
            guess = guess.slice(0, -1);
            draw();
            e.preventDefault();
        }
    };
    
    document.addEventListener('keydown', gameKeyHandler);
    canvas.focus();
    draw();
}

// 🐍 ЗМЕЙКА (ПРАВИЛЬНО!)
function loadSnakeGame() {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    let snake = [{x: 10, y: 10}];
    let dx = 1, dy = 0;
    let food = {x: 15, y: 15};
    let score = 0;
    let gameRunning = true;
    
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (!gameRunning) {
            ctx.fillStyle = '#ff4444';
            ctx.font = 'bold 36px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('ИГРА ОКОНЧЕНА', 250, 200);
            ctx.textAlign = 'left';
            return;
        }
        
        // Змейка
        ctx.fillStyle = '#44ff44';
        snake.forEach((part, i) => {
            ctx.fillRect(part.x*20+1, part.y*20+1, 18, 18);
        });
        
        // Еда
        ctx.fillStyle = '#ff4444';
        ctx.beginPath();
        ctx.arc(food.x*20+10, food.y*20+10, 8, 0, Math.PI*2);
        ctx.fill();
        
        // Счёт
        ctx.fillStyle = 'white';
        ctx.font = 'bold 32px Arial';
        ctx.fillText(`🐍 ${score}`, 20, 40);
    }
    
    function gameLoop() {
        if (!gameRunning) return;
        
        const head = {x: snake[0].x + dx, y: snake[0].y + dy};
        
        // Стены
        if (head.x < 0 || head.x >= 25 || head.y < 0 || head.y >= 20) {
            gameRunning = false;
            if (isLoggedIn) saveScore('snake', score);
            draw();
            return;
        }
        
        // Самоедение
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
                x: Math.floor(Math.random() * 24),
                y: Math.floor(Math.random() * 19)
            };
        } else {
            snake.pop();
        }
        
        draw();
        setTimeout(gameLoop, 150);
    }
    
    // ✅ УНИКАЛЬНЫЙ обработчик только для змейки
    gameKeyHandler = (e) => {
        if (!gameRunning) return;
        if (e.key === 'ArrowUp' && dy !== 1) { dx = 0; dy = -1; e.preventDefault(); }
        if (e.key === 'ArrowDown' && dy !== -1) { dx = 0; dy = 1; e.preventDefault(); }
        if (e.key === 'ArrowLeft' && dx !== 1) { dx = -1; dy = 0; e.preventDefault(); }
        if (e.key === 'ArrowRight' && dx !== -1) { dx = 1; dy = 0; e.preventDefault(); }
    };
    
    // 📱 СВАЙПЫ ДЛЯ ТЕЛЕФОНА
    let touchStartX = 0, touchStartY = 0;
    canvas.addEventListener('touchstart', e => {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    });
    canvas.addEventListener('touchend', e => {
        if (!gameRunning) return;
        const deltaX = e.changedTouches[0].clientX - touchStartX;
        const deltaY = e.changedTouches[0].clientY - touchStartY;
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 30) {
            if (deltaX > 0 && dx !== -1) { dx = 1; dy = 0; }
            if (deltaX < 0 && dx !== 1) { dx = -1; dy = 0; }
        } else if (Math.abs(deltaY) > 30) {
            if (deltaY > 0 && dy !== -1) { dx = 0; dy = 1; }
            if (deltaY < 0 && dy !== 1) { dx = 0; dy = -1; }
        }
    });
    
    document.addEventListener('keydown', gameKeyHandler);
    canvas.focus();
    gameLoop();
}

async function logout() {
    await fetch('/logout', {method: 'POST', credentials: 'include'});
    document.getElementById('status').textContent = '👋 Гость';
    document.getElementById('logout').style.display = 'none';
    isLoggedIn = false;
    if (gameKeyHandler) {
        document.removeEventListener('keydown', gameKeyHandler);
        gameKeyHandler = null;
    }
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

checkUserStatus();
