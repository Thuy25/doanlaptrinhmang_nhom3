from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import SessionLocal
from models import User

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        db = SessionLocal()

        if db.query(User).filter_by(username=data['username']).first():
            flash("Username đã tồn tại")
            return render_template('register.html')

        hashed_password = generate_password_hash(data['password'])

        user = User(
            Name=data['name'],
            hash_pass=hashed_password,
            email=data['email'],
            phone=data['phone'],
            username=data['username'],
            birthday=data['birthday'],
            country=data['country'],
            sex=bool(int(data['sex']))
        )

        db.add(user)
        db.commit()
        db.close()

        flash("Đăng ký thành công")
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        db = SessionLocal()
        user = db.query(User).filter_by(username=data['username']).first()

        if user and check_password_hash(user.hash_pass, data['password']):
            session['user_id'] = user.ID
            session['username'] = user.username
            flash("Đăng nhập thành công!")
            return redirect(url_for('dashboard'))  # chuyển sang dashboard
        else:
            flash("Sai username hoặc password")
        db.close()
    return render_template('login.html')
