from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models import User

auth = Blueprint("auth", __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user:
            print("🔍 User ditemukan:", user.username)
            if check_password_hash(user.password, password):
                login_user(user)
                print("✅ Login berhasil:", user.username)
                return redirect(url_for('dashboard'))
            else:
                print("❌ Password salah")

        else:
            print("❌ User tidak ditemukan")

        flash('Username atau password salah.')
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
