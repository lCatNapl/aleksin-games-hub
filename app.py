from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'aleksin_games_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scores.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    game = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20))
    points = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scores', methods=['POST'])
def save_score():
    if 'username' not in session:
        return jsonify({'error': 'login required'}), 401
    data = request.json
    score = Score(username=session['username'], game=data['game'], 
                  difficulty=data.get('difficulty'), points=data['points'])
    db.session.add(score)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/leaderboard/<game>')
def leaderboard(game):
    if 'username' not in session:
        return jsonify({'error': 'login required'}), 401
    top10 = Score.query.filter_by(game=game).order_by(Score.points.desc()).limit(10).all()
    return jsonify([{'user': s.username, 'points': s.points, 'diff': s.difficulty} for s in top10])

@app.route('/api/tournament')
def tournament():
    if 'username' not in session:
        return jsonify([]), 401
    today = datetime.now().date()
    daily_scores = Score.query.filter(db.func.date(Score.timestamp) == today)\
        .order_by(Score.points.desc()).limit(100).all()
    return jsonify([{'user': s.username, 'points': s.points} for s in daily_scores])
