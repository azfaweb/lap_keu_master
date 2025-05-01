from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    projects = db.relationship('Project', backref='user', lazy=True)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(200), nullable=False)
    entity_a = db.Column(db.String(100), nullable=False)
    porsia = db.Column(db.Float, nullable=False)
    entity_b = db.Column(db.String(100), nullable=False)
    porsib = db.Column(db.Float, nullable=False)
    total_lr = db.Column(db.Float, default=0)
    nilai_a = db.Column(db.Float, default=0)
    nilai_b = db.Column(db.Float, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    details = db.relationship('ProjectDetail', backref='project', lazy=True, cascade="all, delete-orphan")

class ProjectDetail(db.Model):
    __tablename__ = 'project_details'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    account_number = db.Column(db.String(100))
    text_item = db.Column(db.String(255))
    total_reporting_period = db.Column(db.Float)