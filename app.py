from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scores.db'
db = SQLAlchemy(app)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    game = db.Column(db.String(20), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    score = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

@app.route('/save_score', methods=['POST'])
def save_score():
    data = request.json
    score = Score(username=data['username'], game=data['game'], difficulty=data['difficulty'], score=data['score'])
    old = Score.query.filter_by(username=data['username'], game=data['game'], difficulty=data['difficulty']).first()
    if old:
        if data['score'] > old.score:
            old.score = data['score']
    else:
        db.session.add(score)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/top10/<game>/<difficulty>')
def top10(game, difficulty):
    tops = Score.query.filter_by(game=game, difficulty=difficulty).order_by(Score.score.desc()).limit(10).all()
    return jsonify([{'username': s.username, 'score': s.score} for s in tops])

@app.route('/user_scores/<username>')
def user_scores(username):
    scores = Score.query.filter_by(username=username).all()
    return jsonify({f"{s.game}_{s.difficulty}": s.score for s in scores})

if __name__ == '__main__':
    app.run(debug=True)
