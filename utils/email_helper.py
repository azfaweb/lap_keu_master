from flask_mail import Message
from flask import current_app
from app import mail  # Import mail object dari app.py

def send_upload_notification(user_email, project_name):
    try:
        msg = Message(
            subject="Laporan Baru Diunggah",
            recipients=[user_email],
            body=f"Proyek '{project_name}' berhasil diunggah dan diproses.",
            sender=current_app.config['MAIL_USERNAME']
        )
        mail.send(msg)
        print("✅ Email notifikasi berhasil dikirim ke", user_email)
    except Exception as e:
        print("❌ Gagal kirim email:", e)