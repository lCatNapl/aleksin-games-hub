from flask import Flask, render_template, request, session, redirect, url_for
import random
import json
import os

app = Flask(__name__)
app.secret_key = 'perfect_aleksin_site_2026_tula'

LEADERS_FILE = "leaders.json"

def load_leaders():
    if os.path.exists(LEADERS_FILE):
        with open(LEADERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_leaders(leaders):
    with open(LEADERS_FILE, "w", encoding="utf-8") as f:
        json.dump(leaders, f, ensure_ascii=False, indent=2)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/guess")
def guess_start():
    session['secret'] = random.randint(1, 100)
    session['attempts'] = 0
    session['player_name'] = request.args.get('name', 'Гость')
    return render_template("guess.html")

@app.route("/guess_check", methods=["POST"])
def guess_check():
    if 'secret' not in session: return redirect(url_for('guess_start'))
    guess = int(request.form['num'])
    secret = session['secret']
    session['attempts'] += 1
    if guess < secret: message = f"❄️ Мало! ({session['attempts']} попытка)"
    elif guess > secret: message = f"🔥 Много! ({session['attempts']} попытка)"
    else:
        leaders = load_leaders()
        leaders.append({'name': session['player_name'], 'attempts': session['attempts']})
        leaders.sort(key=lambda x: x['attempts'])
        save_leaders(leaders[:10])
        message = f"🎉 ПОБЕДА! {session['attempts']} попыток! Рекорд: {leaders[0]['attempts']}"
        session.pop('secret', None)
    return render_template("guess.html", message=message, name=session['player_name'], attempts=session['attempts'])

@app.route("/leaders")
def leaders():
    return render_template("leaders.html", leaders=load_leaders())

@app.route("/snake_game")
def snake_game():
    return render_template("snake_game.html")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
