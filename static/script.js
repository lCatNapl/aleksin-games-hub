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
    
    // ✅ ИСПРАВЛЕНО: точно определяем режим
    const modalTitle = document.getElementById('modal-title');
    const mode = modalTitle.dataset.mode || (modalTitle.textContent.includes('РЕГИСТРАЦИЯ') ? 'register' : 'login');
    const endpoint = mode === 'register' ? '/register' : '/login';
    
    console.log(`🔄 ${mode.toUpperCase()}: ${username}`);
    document.getElementById('error').textContent = '';
    
    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await res.json();
        console.log('📡 Ответ:', data);
        
        if (data.success) {
            document.getElementById('status').textContent = `👋 ${data.username}`;
            document.getElementById('logout').style.display = 'inline-block';
            closeAuth();
            isLoggedIn = true;
            checkUserStatus();
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
    if (game === 'guess') loadGuessGame();
    else if (game === 'snake') loadSnakeGame();
    loadLeaderboard(game);
}

async function loadLeaderboard(game) {
    try {
        const res = await fetch(`/top/${game}`, {credentials: 'include'});
        const leaders = await res.json();
        const list = document.getElementById('leaders-list');
        list.innerHTML = leaders.length ? 
            leaders.map((p,i) => `<div class="leader-item"><span>${i+1}. ${p.username}</span><span>${p.score}</span></div>`).join('') : 
            '<div style="text-align:center;color:#aaa;">Пока нет рекордов</div>';
        document.getElementById('leaderboard').style.display = 'block';
    } catch(e) {
        console.error('Leaderboard error:', e);
    }
}

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
        ctx.fillText(`🎯 Угадай: ${guess || '?'} (1-100)`, 20, 60);
        ctx.font = '24px Arial';
        ctx.fillText(`Попыток: ${attempts}`, 20, 110);
        if (attempts === 0) {
            ctx.fillStyle = '#ff4444';
            ctx.font = 'bold 24px Arial';
            ctx.fillText(`Было: ${secret}`, 20, 180);
        }
    }
    
    function checkGuess() {
        const num = parseInt(guess);
        if (isNaN(num) || num < 1 || num > 100) return;
        attempts--;
        if (num === secret) {
            const score = 1000 - (7-attempts)*100;
            if (isLoggedIn) saveScore('guess', score);
            ctx.fillStyle = '#44ff44';
            ctx.fillText('✅ ПОБЕДА!', 20, 160);
        } else if (attempts === 0) {
            ctx.fillStyle = '#ff4444';
            ctx.fillText(`Было: ${secret}`, 20, 180);
        } else if (num < secret) {
            ctx.fillStyle = '#ffaa00';
            ctx.fillText('⬆️ Больше!', 20, 160);
        } else {
            ctx.fillStyle = '#ffaa00';
            ctx.fillText('⬇️ Меньше!', 20, 160);
        }
        guess = ''; draw();
    }
    
    document.addEventListener('keydown', e => {
        if (e.key >= '0' && e.key <= '9' && guess.length < 3) guess += e.key;
        else if (e.key === 'Enter') checkGuess();
        else if (e.key === 'Backspace') guess = guess.slice(0, -1);
        if (currentGame === 'guess') draw();
    });
    draw();
}

function loadSnakeGame() {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    let snake = [{x: 10, y: 10}];
    let dx = 1, dy = 0;
    let food = {x: 15, y: 15};
    let score = 0;
    
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#44ff44';
        snake.forEach(part => ctx.fillRect(part.x*20, part.y*20, 20, 20));
        ctx.fillStyle = '#ff4444';
        ctx.fillRect(food.x*20, food.y*20, 20, 20);
        ctx.fillStyle = 'white';
        ctx.font = 'bold 28px Arial';
        ctx.fillText(`🐍 ${score}`, 20, 40);
    }
    
    document.addEventListener('keydown', e => {
        if (e.key === 'ArrowUp' && dy !== 1) { dx = 0; dy = -1; }
        if (e.key === 'ArrowDown' && dy !== -1) { dx = 0; dy = 1; }
        if (e.key === 'ArrowLeft' && dx !== 1) { dx = -1; dy = 0; }
        if (e.key === 'ArrowRight' && dx !== -1) { dx = 1; dy = 0; }
    });
    
    function gameLoop() {
        const head = {x: snake[0].x + dx, y: snake[0].y + dy};
        if (head.x < 0 || head.x >= 25 || head.y < 0 || head.y >= 20) return;
        snake.unshift(head);
        if (head.x === food.x && head.y === food.y) {
            score++;
            food = {x: Math.floor(Math.random()*25), y: Math.floor(Math.random()*20)};
            if (isLoggedIn) saveScore('snake', score);
        } else snake.pop();
        draw();
        setTimeout(gameLoop, 150);
    }
    gameLoop();
}

async function saveScore(game, score) {
    if (!isLoggedIn) return;
    try {
        await fetch('/save_score', {
            method: 'POST', credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({game, score})
        });
    } catch(e) {}
}

function showAuth(mode) {
    document.getElementById('auth-modal').style.display = 'flex';
    const modalTitle = document.getElementById('modal-title');
    if (mode === 'register') {
        modalTitle.textContent = '📝 РЕГИСТРАЦИЯ';
        modalTitle.dataset.mode = 'register';
    } else {
        modalTitle.textContent = '🔑 ВХОД';
        modalTitle.dataset.mode = 'login';
    }
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

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeAuth();
    if (document.getElementById('auth-modal').style.display === 'flex' && e.key === 'Enter') authUser();
});

checkUserStatus();
// В конец script.js
let touchStartX = 0, touchStartY = 0;
document.addEventListener('touchstart', e => {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
});
document.addEventListener('touchend', e => {
    const deltaX = e.changedTouches[0].clientX - touchStartX;
    const deltaY = e.changedTouches[0].clientY - touchStartY;
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
        if (deltaX > 50) dx = 1, dy = 0;  // Вправо
        if (deltaX < -50) dx = -1, dy = 0; // Влево
    } else {
        if (deltaY > 50) dy = 1, dx = 0;  // Вниз
        if (deltaY < -50) dy = -1, dx = 0; // Вверх
    }
});
