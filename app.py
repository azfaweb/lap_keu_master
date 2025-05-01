from models import db, User, Project, ProjectDetail
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from auth import auth
from flask_login import LoginManager
import pandas as pd
import os
import io
import pdfkit
from utils.file_processing import bersihkan_excel
from flask_mail import Mail, Message
import requests
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallbacksecretkey')
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

# Registrasi blueprint auth
app.register_blueprint(auth)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'none'
db.init_app(app)
with app.app_context():
    db.create_all()
    
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # ganti
app.config['MAIL_PASSWORD'] = 'your_app_password'      # ganti

mail = Mail(app)

load_dotenv()

API_KEY = os.getenv("30Vxikyyve18FPPcltK9CEN1Sp5ONRzWeIjZLhL3EN4S1Xj6mbE6CGk6FigDY869")

def send_upload_notification(user_email, project_name):
    msg = Message(
        subject="Laporan Baru Diunggah",
        recipients=[user_email],
        body=f"Proyek '{project_name}' berhasil diunggah dan diproses.",
        sender=app.config['MAIL_USERNAME']
    )
    mail.send(msg)

UPLOAD_FOLDER = 'static/uploads'
EXPORT_FOLDER = 'exported'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Filter untuk menampilkan "-" jika None atau NaN
@app.template_filter('none_to_dash')
def none_to_dash(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return '-'
    return value

# ==============================
# ROUTES
# ==============================

@app.route('/')
def home():
    return redirect(url_for('dashboard')) if current_user.is_authenticated else redirect(url_for('auth.login'))

@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup_project():
    if current_user.role != 'admin':
        flash('Akses hanya untuk Admin.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        project = Project(
            project_name=request.form['project_name'],
            entity_a=request.form['entity_a'],
            porsia=float(request.form['porsia']) / 100,
            entity_b=request.form['entity_b'],
            porsib=float(request.form['porsib']) / 100,
            user_id=current_user.id
        )
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('upload_laporan', project_id=project.id))
    return render_template('setup_project.html')

@app.route('/upload/<int:project_id>', methods=['GET', 'POST'])
@login_required
def upload_laporan(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith(('.xls', '.xlsx')):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            try:
                df = pd.read_excel(filepath)
                df_bersih = bersihkan_excel(df)
                df_bersih['Total of Reporting Period'] = pd.to_numeric(df_bersih['Total of Reporting Period'], errors='coerce').fillna(0)

                # Hitung dan simpan ke project
                total = df_bersih['Total of Reporting Period'].sum()
                project.total_lr = total
                project.nilai_a = total * project.porsia
                project.nilai_b = total * project.porsib
                db.session.commit()

                # Bersihkan detail lama
                ProjectDetail.query.filter_by(project_id=project.id).delete()

                # Simpan semua detail baru
                for _, row in df_bersih.iterrows():
                    detail = ProjectDetail(
                        project_id=project.id,
                        account_number=row.get('Account Number'),
                        text_item=row.get('Text for B/S P&L Item'),
                        total_reporting_period=row.get('Total of Reporting Period')
                    )
                    db.session.add(detail)
                db.session.commit()

                return redirect(url_for('dashboard'))

            except Exception as e:
                return render_template('upload_laporan.html', error=str(e))
        else:
            return render_template('upload_laporan.html', error="Upload file Excel yang valid.")

    return render_template('upload_laporan.html', project=project)

@app.route('/dashboard')
@login_required
def dashboard():
    print("🔐 current_user:", current_user)
    print("🆔 is_authenticated:", current_user.is_authenticated)
    projects = Project.query.all()  # ✅ Semua proyek ditampilkan ke semua user
    return render_template('dashboard.html', projects=projects)

@app.route('/dashboard/view/<int:project_id>')
@login_required
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    details = ProjectDetail.query.filter_by(project_id=project.id).all()
    return render_template('view_project.html', project=project, details=details)

@app.route('/dashboard/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        project.entity_a = request.form['entity_a']
        project.porsia = float(request.form['porsia']) / 100
        project.entity_b = request.form['entity_b']
        project.porsib = float(request.form['porsib']) / 100
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('edit_project.html', project=project)

@app.route('/dashboard/delete/<int:project_id>')
@login_required
def delete_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('dashboard'))

# ==============================
# EXPORT
# ==============================

@app.route('/dashboard/export_excel')
@login_required
def export_projects_excel():
    projects = Project.query.filter_by(user_id=current_user.id).all()

    data = [{
        'Nama Proyek': p.project_name,
        'Entitas A': p.entity_a,
        'Porsi A (%)': p.porsia * 100,
        'Pembagian A (Rp)': p.nilai_a,
        'Entitas B': p.entity_b,
        'Porsi B (%)': p.porsib * 100,
        'Pembagian B (Rp)': p.nilai_b
    } for p in projects]

    df = pd.DataFrame(data)
    output_path = os.path.join(EXPORT_FOLDER, f'proyek_user_{current_user.id}.xlsx')
    df.to_excel(output_path, index=False)

    return send_file(output_path, as_attachment=True)

@app.route('/dashboard/project_excel/<int:project_id>')
@login_required
def export_single_project_excel(project_id):
    project = Project.query.get_or_404(project_id)
    details = ProjectDetail.query.filter_by(project_id=project.id).all()

    data = [{
        'Account Number': d.account_number,
        'Text for B/S P&L Item': d.text_item,
        'Total of Reporting Period': d.total_reporting_period
    } for d in details]

    df = pd.DataFrame(data)
    output_path = os.path.join(EXPORT_FOLDER, f"{project.project_name}.xlsx")
    df.to_excel(output_path, index=False)

    return send_file(output_path, as_attachment=True)


@app.route('/dashboard/project_pdf/<int:project_id>', methods=['POST'])
@login_required
def export_single_project_pdf(project_id):
    project = Project.query.get_or_404(project_id)

    print("👤 current_user.id:", current_user.id)
    print("📁 project.user_id:", project.user_id)
    print("🎯 current_user.role:", current_user.role)

    # Hanya pemilik atau admin
    #if current_user.role != 'admin' and project.user_id != current_user.id:
    #   flash("🚫 Kamu tidak punya akses ke proyek ini.", "danger")
    #    return redirect(url_for('dashboard'))

    details = ProjectDetail.query.filter_by(project_id=project.id).all()
    html_content = render_template('export_pdf_template.html', project=project, details=details)

    api_key = os.getenv("HTML2PDF_API_KEY") or '30Vxikyyve18FPPcltK9CEN1Sp5ONRzWeIjZLhL3EN4S1Xj6mbE6CGk6FigDY869'
    response = requests.post(
        'https://api.html2pdf.app/v1/generate',
        json={'html': html_content, 'apiKey': api_key}
    )

    if response.status_code == 200:
        return send_file(
            io.BytesIO(response.content),
            download_name=f"{project.project_name}.pdf",
            as_attachment=True
        )
    else:
        return f"Gagal generate PDF. Status: {response.status_code}", 500


@app.route('/dashboard/export_pdf')
@login_required
def export_projects_pdf():
    # Admin lihat semua proyek, user hanya miliknya
    if current_user.role == 'admin':
        projects = Project.query.all()
    else:
        projects = Project.query.filter_by(user_id=current_user.id).all()

    html_content = render_template('export_projects_pdf.html', projects=projects)

    api_key = os.getenv("HTML2PDF_API_KEY") or '30Vxikyyve18FPPcltK9CEN1Sp5ONRzWeIjZLhL3EN4S1Xj6mbE6CGk6FigDY869'
    response = requests.post(
        'https://api.html2pdf.app/v1/generate',
        json={
            'html': html_content,
            'apiKey': api_key
        }
    )

    if response.status_code == 200:
        return send_file(
            io.BytesIO(response.content),
            download_name='semua_proyek.pdf',
            as_attachment=True
        )
    else:
        return f"❌ Gagal export PDF semua proyek. Status: {response.status_code}", 500


@app.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Akses hanya untuk Admin.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Cek username apakah sudah ada
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username sudah digunakan.', 'danger')
            return redirect(url_for('add_user'))

        # Simpan user baru
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash(f'User {username} berhasil dibuat.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_user.html')

@app.route('/admin/users')
@login_required
def list_users():
    if current_user.role != 'admin':
        flash('Akses hanya untuk Admin.', 'danger')
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('list_users.html', users=users)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Akses hanya untuk Admin.', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    if user.role == 'admin':
        flash('Tidak bisa menghapus sesama Admin!', 'danger')
        return redirect(url_for('list_users'))

    db.session.delete(user)
    db.session.commit()
    flash('User berhasil dihapus.', 'success')
    return redirect(url_for('list_users'))

with app.app_context():
    db.create_all()

    # Buat user admin dan user default jika belum ada
    if not User.query.first():
        from werkzeug.security import generate_password_hash
        admin = User(username='admin', password=generate_password_hash('admin123'), role='admin')
        user = User(username='user', password=generate_password_hash('user123'), role='user')
        db.session.add_all([admin, user])
        db.session.commit()
        print("✅ Admin & User default berhasil dibuat.")

if __name__ == '__main__':
    app.run(debug=True)