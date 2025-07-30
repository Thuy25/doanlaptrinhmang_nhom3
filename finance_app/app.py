from flask import Flask, session, redirect, url_for, render_template
from auth.routes import auth

app = Flask(__name__)
app.secret_key = 'very_secret_key'  # đổi key thật sự khi chạy thật

app.register_blueprint(auth)

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == "__main__":
    app.run(debug=True)
