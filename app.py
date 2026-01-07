from flask import Flask, render_template_string
app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string("""
    <!-- ВСТАВЬ СЮДА ПОЛНЫЙ HTML КОД v3.5 из сообщения выше -->
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
