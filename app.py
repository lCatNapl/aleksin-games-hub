from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'aleksin-games-hub-v4-super-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aleksin_games.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# МОДЕЛЬ ДАННЫХ
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    game = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), default='normal')
    points = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# ✅ ИНИЦИАЛИЗАЦИЯ БАЗЫ
with app.app_context():
    db.create_all()
    # ТЕСТОВЫЕ ДАННЫЕ
    if not User.query.filter_by(username='test').first():
        test_user = User(username='test', password='123456')
        db.session.add(test_user)
        db.session.commit()
        print("✅ Тестовый аккаунт test:123456 создан")

@app.route('/')
def index():
    return render_template('index.html')

# ✅ ЛОГИН/РЕГИСТРАЦИЯ (ПРОВЕРКА)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if user:
        session['username'] = data['username']
        return jsonify({'success': True})
    return jsonify({'success': False}), 401

@app.route('/logout')
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

# ✅ СОХРАНЕНИЕ РЕКОРДОВ
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

# ✅ ГЛОБАЛЬНЫЙ ТОП-10 ПО ИГРАМ
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
        'difficulty': s.difficulty,
        'timestamp': s.timestamp.isoformat()
    } for s in top10])

# ✅ ТУРНИР СЕГОДНЯ (ТОП-100)
@app.route('/api/tournament')
def tournament():
    if 'username' not in session:
        return jsonify({'error': 'Требуется вход'}), 401
    
    today = date.today()
    daily_scores = db.session.query(Score)\
        .filter(db.func.date(Score.timestamp) == today)\
        .order_by(Score.points.desc())\
        .limit(100).all()
    
    return jsonify([{
        'user': s.username,
        'points': s.points,
        'rank': i+1
    } for i, s in enumerate(daily_scores)])

if __name__ == '__main__':
    app.run(debug=True)
