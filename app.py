import os
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from sqlalchemy import func

app = Flask(__name__)
app.secret_key = 'aleksin-games-hub-v4-super-secret-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aleksin_games.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# МОДЕЛИ
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    game = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), default='normal')
    points = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ✅ ИНИЦИАЛИЗАЦИЯ БАЗЫ + ГАРАНТИРОВАННЫЙ ТЕСТ АККАУНТ
with app.app_context():
    db.create_all()
    
    # ПРОВЕРКА + ПРИНУДИТЕЛЬНОЕ СОЗДАНИЕ test:123456
    test_user = User.query.filter_by(username='test').first()
    if not test_user:
        test_user = User(username='test', password='123456')
        db.session.add(test_user)
        db.session.commit()
        print("✅ Test account 'test:123456' CREATED!")
    else:
        print("✅ Test account 'test:123456' EXISTS!")

@app.route('/')
def index():
    return render_template('index.html')

# ✅ ЛОГИН
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if user:
        session['username'] = data['username']
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Неверный логин/пароль'}), 401

# ✅ РЕГИСТРАЦИЯ
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'error': 'Логин занят'}), 400
    
    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    session['username'] = data['username']
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

# ✅ СОХРАНЕНИЕ РЕКОРДА
@app.route('/api/scores', methods=['POST'])
def save_score():
    if 'username' not in session:
        return jsonify({'error': 'Требуется вход'}), 401
    
    data = request.json
    score = Score(
        username=session['username'],
        game=data['game'],
        difficulty=data.get('difficulty', 'normal'),
        points=data['points']
    )
    db.session.add(score)
    db.session.commit()
    return jsonify({'success': True})

# ✅ ГЛОБАЛЬНЫЙ ТОП-10
@app.route('/api/leaderboard/<game>')
def leaderboard(game):
    if 'username' not in session:
        return jsonify({'error': 'Требуется вход'}), 401
    
    top10 = Score.query.filter_by(game=game)\
        .order_by(Score.points.desc())\
        .limit(10).all()
    
    return jsonify([{
        'user': s.username,
        'points': s.points,
        'difficulty': s.difficulty
    } for s in top10])

# ✅ ТУРНИР ТОП-100
@app.route('/api/tournament')
def tournament():
    if 'username' not in session:
        return jsonify({'error': 'Требуется вход'}), 401
    
    today = date.today()
    daily_scores = db.session.query(Score)\
        .filter(func.date(Score.timestamp) == today)\
        .order_by(Score.points.desc())\
        .limit(100).all()
    
    return jsonify([{
        'user': s.username,
        'points': s.points,
        'rank': i+1
    } for i, s in enumerate(daily_scores)])

# ✅ RENDER PORT BINDING
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
