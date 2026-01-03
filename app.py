from flask import Flask, render_template, request, jsonify, session
import os

app = Flask(__name__)
app.secret_key = 'aleksin-games-hub-2026'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    return jsonify({'logged_in': False})

@app.route('/login', methods=['POST'])
def login():
    return jsonify({'success': True})

@app.route('/register', methods=['POST'])
def register():
    return jsonify({'success': True})

@app.route('/logout', methods=['POST'])
def logout():
    return jsonify({'success': True})

@app.route('/save', methods=['POST'])
def save():
    return jsonify({'success': True})

@app.route('/top/snake')
def top_snake():
    return jsonify([])

@app.route('/top/guess')
def top_guess():
    return jsonify([])

@app.route('/tournament')
def tournament():
    return jsonify({'active': False})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
