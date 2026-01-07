from flask import Flask, render_template, request, jsonify, session
import os

app = Flask(__name__)
app.secret_key = 'aleksin-games-hub-v3-super-secret'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if data['username'] == 'test' and data['password'] == '123456':
        session['username'] = data['username']
        return jsonify({'success': True})
    return jsonify({'success': False}), 401

@app.route('/logout')
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

# FAKE API — localStorage делает фронт
@app.route('/api/scores', methods=['POST'])
def save_score():
    return jsonify({'success': True})

@app.route('/api/leaderboard/<game>')
def leaderboard(game):
    return jsonify([])

@app.route('/api/tournament')
def tournament():
    return jsonify([])

# ✅ RENDER PORT
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
