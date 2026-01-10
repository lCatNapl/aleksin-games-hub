from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import defaultdict
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aleksin-games-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

leaderboards = defaultdict(list)
online_users = set()

@app.route('/')
def index():
    return send_file('index.html')

@socketio.on('score')
def handle_score(data):
    key = f"{data['game']}_{data['username']}"
    leaderboards[data['game']].append({
        'username': data['username'], 
        'score': data['score'],
        'date': datetime.now().isoformat()
    })
    leaderboards[data['game']] = sorted(leaderboards[data['game']], key=lambda x: x['score'], reverse=True)[:10]
    emit('leaderboards', {'data': dict(leaderboards)}, broadcast=True)

@socketio.on('online_status')
def handle_online(data):
    if data['online']:
        online_users.add(data['username'])
    else:
        online_users.discard(data['username'])
    emit('online_users', {'users': list(online_users)}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
