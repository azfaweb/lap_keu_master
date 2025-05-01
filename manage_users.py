from models import db, User
from werkzeug.security import generate_password_hash
from app import app

def create_user(username, password, role='user'):
    with app.app_context():
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"⚠️ Username '{username}' sudah ada!")
            return

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        print(f"✅ User '{username}' dengan role '{role}' berhasil dibuat.")

if __name__ == '__main__':
    print('--- Tambah User Baru ---')
    username = input('Masukkan Username: ')
    password = input('Masukkan Password: ')
    role = input('Role (admin/user) [default: user]: ') or 'user'

    create_user(username, password, role)