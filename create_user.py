from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    username = "admin"
    password = "admin123"
    role = "admin"

    # Cek apakah user sudah ada
    existing = User.query.filter_by(username=username).first()
    if existing:
        print("⚠️ User sudah ada.")
    else:
        new_user = User(
            username=username,
            password=generate_password_hash(password),
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        print("✅ User berhasil ditambahkan.")