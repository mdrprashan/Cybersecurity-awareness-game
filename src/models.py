"""
models.py — CyberQuest Database Models
ICT932 – Cybersecurity Testing and Assurance
Author: Prashan Manandhar (CIHE241182)

Security fixes applied:
  - load_user uses db.session.get() instead of deprecated User.query.get()
"""

from datetime import datetime
from flask_login import UserMixin
from extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    # SECURITY FIX: db.session.get() is the non-deprecated way in SQLAlchemy 2.x
    return db.session.get(User, int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id             = db.Column(db.Integer,     primary_key=True)
    username       = db.Column(db.String(80),  unique=True, nullable=False)
    email          = db.Column(db.String(120), unique=True, nullable=False)
    password       = db.Column(db.String(200), nullable=False)
    role           = db.Column(db.String(20),  default='student')
    totp_secret    = db.Column(db.String(32),  nullable=True)
    is_2fa_enabled = db.Column(db.Boolean,     default=False)
    created_at     = db.Column(db.DateTime,    default=datetime.utcnow)

    scores         = db.relationship('Score',        backref='user', lazy=True)
    earned_badges  = db.relationship('UserBadge',    backref='user', lazy=True)
    login_attempts = db.relationship('LoginAttempt', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    @property
    def is_teacher(self):
        return self.role == 'teacher'

    @property
    def total_score(self):
        return sum(s.points for s in self.scores)


class Challenge(db.Model):
    __tablename__ = 'challenges'

    id             = db.Column(db.Integer,     primary_key=True)
    category       = db.Column(db.String(50),  nullable=False)
    question       = db.Column(db.Text,        nullable=False)
    option_a       = db.Column(db.String(250), nullable=False)
    option_b       = db.Column(db.String(250), nullable=False)
    option_c       = db.Column(db.String(250), nullable=False)
    option_d       = db.Column(db.String(250), nullable=False)
    correct_answer = db.Column(db.String(1),   nullable=False)
    explanation    = db.Column(db.Text,        nullable=True)
    difficulty     = db.Column(db.String(20),  default='medium')

    scores = db.relationship('Score', backref='challenge', lazy=True)


class Score(db.Model):
    __tablename__ = 'scores'

    id           = db.Column(db.Integer,  primary_key=True)
    user_id      = db.Column(db.Integer,  db.ForeignKey('users.id'),      nullable=False)
    challenge_id = db.Column(db.Integer,  db.ForeignKey('challenges.id'), nullable=False)
    points       = db.Column(db.Integer,  default=0)
    is_correct   = db.Column(db.Boolean,  default=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)


class Badge(db.Model):
    __tablename__ = 'badges'

    id          = db.Column(db.Integer,    primary_key=True)
    name        = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text,       nullable=True)
    icon        = db.Column(db.String(10), nullable=True)
    requirement = db.Column(db.Integer,    default=5)

    earners = db.relationship('UserBadge', backref='badge', lazy=True)


class UserBadge(db.Model):
    __tablename__ = 'user_badges'

    id        = db.Column(db.Integer,  primary_key=True)
    user_id   = db.Column(db.Integer,  db.ForeignKey('users.id'),  nullable=False)
    badge_id  = db.Column(db.Integer,  db.ForeignKey('badges.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)


class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'

    id           = db.Column(db.Integer,     primary_key=True)
    user_id      = db.Column(db.Integer,     db.ForeignKey('users.id'), nullable=True)
    email        = db.Column(db.String(120), nullable=False)
    ip_address   = db.Column(db.String(50),  nullable=True)
    success      = db.Column(db.Boolean,     default=False)
    attempted_at = db.Column(db.DateTime,    default=datetime.utcnow)
