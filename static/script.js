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
    document.getElementById('leaderboard').style.display = 'none';
    if (game === 'guess') loadGuessGame();
    else if (game === 'snake') loadSnakeGame();
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

// 📊 СТАТИСТИКА
async function loadStats() {
    try {
        const res = await fetch('/stats');
        const data = await res.json();
        document.getElementById('game-container').innerHTML = `
            <div style="padding:30px;text-align:center;max-width:600px;margin:0 auto">
                <h2 style="color:#44ff88;font-size:36px;margin-bottom:30px">📊 Твоя статистика</h2>
                ${!data.user || Object.keys(data.user).length === 0 ? 
                    '<div style="color:#aaa;font-size:24px;padding:40px">Играй и получай статистику! 🎮</div>' : 
                    Object.entries(data.user).map(([game, stats]) => {
                        const gameName = game === 'guess' ? '🎯 Угадайка' : '🐍 Змейка';
                        return `
                            <div style="background:rgba(0,0,0,0.5);margin:20px auto;padding:25px;border-radius:20px;max-width:450px">
                                <h3 style="color:#44ff88;margin:0 0 15px 0;font-size:24px">${gameName}</h3>
                                <div style="font-size:20px;margin:8px 0">🎲 Игр: ${stats.played}</div>
                                <div style="font-size:20px;margin:8px 0">📈 Средний: ${stats.avg} очков</div>
                                <div style="color:#ffaa00;font-size:22px;font-weight:bold;margin:15px 0">🏆 Рекорд: ${stats.best}</div>
                            </div>
                        `;
                    }).join('') + `<div style="margin-top:30px;color:#aaa;font-size:20px">
                        Всего игроков в хабе: ${data.global.players}
                    </div>`
                }
                <button onclick="showGames()" style="font-size:20px;padding:15px 40px;background:#44ff44;color:black;border:none;border-radius:15px;font-weight:bold;margin-top:30px">🏠 К ИГРАМ</button>
            </div>
        `;
        document.getElementById('game-container').style.display = 'block';
    } catch(e) {
        document.getElementById('game-container').innerHTML = '<div style="color:#ff4444">Ошибка загрузки статистики</div>';
    }
}

// ⚙️ НАСТРОЙКИ
function loadSettings() {
    document.getElementById('game-container').innerHTML = `
        <div style="padding:30px;text-align:center;max-width:500px;margin:0 auto">
            <h2 style="color:#667eea;font-size:36px;margin-bottom:30px">⚙️ НАСТРОЙКИ</h2>
            <div style="background:rgba(0,0,0,0.5);padding:25px;border-radius:20px;margin:20px 0">
                <h3 style="color:#667eea;margin:0 0 20px 0">🎮 Игры</h3>
                <label style="display:block;margin:15px 0;font-size:18px">
                    <input type="checkbox" id="hardMode" checked> Сложный режим
                </label>
                <label style="display:block;margin:15px 0;font-size:18px">
                    Скорость: <input type="range" id="speedSlider" min="50" max="300" value="150">
                    <span id="speedValue">150</span>мс
                </label>
            </div>
            <div style="background:rgba(0,0,0,0.5);padding:25px;border-radius:20px;margin:20px 0">
                <h3 style="color:#667eea;margin:0 0 20px 0">🎨 Оформление</h3>
                <select id="themeSelect" style="font-size:18px;padding:10px;border-radius:10px">
                    <option value="dark">🌙 Темная</option>
                    <option value="light">☀️ Светлая</option>
                    <option value="neon">✨ Неон</option>
                </select>
            </div>
            <button onclick="saveSettings()" style="font-size:20px;padding:15px 40px;background:#44ff44;color:black;border:none;border-radius:15px;font-weight:bold">💾 СОХРАНИТЬ</button>
            <button onclick="showGames()" style="font-size:20px;padding:15px 40px;background:#ff6b6b;color:white;border:none;border-radius:15px;font-weight:bold;margin-left:15px">🏠 К ИГРАМ</button>
        </div>
    `;
    document.getElementById('speedSlider').addEventListener('input', function() {
        document.getElementById('speedValue').textContent = this.value;
    });
    document.getElementById('game-container').style.display = 'block';
}

function showGames() {
    document.getElementById('game-container').style.display = 'none';
    document.getElementById('leaderboard').style.display = 'none';
}

// 🎯 УГАДАЙ ЧИСЛО
function loadGuessGame() {
    const canvas = document.getElementById('gameCanvas');
    canvas.style.display = 'none';
    
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
        <div id="leaderboard" class="leaderboard" style="display:block;margin-top:20px">
            <h3 style="color:white;text-align:center;font-size:24px;margin-bottom:15px">🏆 ТОП-10 УГАДАЙКИ</h3>
            <div id="leaders-list" style="max-height:300px;overflow-y:auto;background:rgba(0,0,0,0.5);padding:15px;border-radius:10px"></div>
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
        if (isLoggedIn) {
            saveScore('guess', score);
        }
        showGuessHint(`✅ ПОБЕДА! ${score} очков! 🎉`, '#44ff88');
        input.disabled = true;
        input.style.borderColor = '#44ff88';
        document.getElementById('currentGuess').textContent = num;
    } else if (window.guessAttempts === 0) {
        showGuessHint(`💀 Было: ${window.guessSecret}`, '#ff4444');
        document.getElementById('gameOver').style.display = 'block';
        input.disabled = true;
        input.style.borderColor = '#ff4444';
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

// 🐍 ЗМЕЙКА (полная функция - без изменений)
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
    
    // ... змейка логика (как раньше) ...
    
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

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeAuth();
    if (document.getElementById('auth-modal').style.display === 'flex' && e.key === 'Enter') {
        authUser();
    }
});

// ✅ ПОСЛЕДНЯЯ СТРОКА
checkUserStatus();
