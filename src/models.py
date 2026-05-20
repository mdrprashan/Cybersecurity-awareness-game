"""
models.py — CyberQuest Database Models
ICT932 – Cybersecurity Testing and Assurance
Author: Prashan Manandhar (CIHE241182)
"""

from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """Student and teacher accounts."""
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80),  unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password     = db.Column(db.String(200), nullable=False)
    role         = db.Column(db.String(20),  default='student')   # 'student' | 'teacher'
    totp_secret  = db.Column(db.String(32),  nullable=True)
    is_2fa_enabled = db.Column(db.Boolean,   default=False)
    created_at   = db.Column(db.DateTime,    default=datetime.utcnow)

    # Relationships
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
    """Quiz questions across three categories."""
    __tablename__ = 'challenges'

    id             = db.Column(db.Integer, primary_key=True)
    category       = db.Column(db.String(50),  nullable=False)   # phishing | password | browsing
    question       = db.Column(db.Text,         nullable=False)
    option_a       = db.Column(db.String(250),  nullable=False)
    option_b       = db.Column(db.String(250),  nullable=False)
    option_c       = db.Column(db.String(250),  nullable=False)
    option_d       = db.Column(db.String(250),  nullable=False)
    correct_answer = db.Column(db.String(1),    nullable=False)   # A | B | C | D
    explanation    = db.Column(db.Text,         nullable=True)
    difficulty     = db.Column(db.String(20),   default='medium') # easy | medium | hard

    scores = db.relationship('Score', backref='challenge', lazy=True)

    def __repr__(self):
        return f'<Challenge {self.id} [{self.category}]>'


class Score(db.Model):
    """Records each challenge attempt and points awarded."""
    __tablename__ = 'scores'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'),       nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'),  nullable=False)
    points       = db.Column(db.Integer, default=0)
    is_correct   = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Score user={self.user_id} challenge={self.challenge_id} pts={self.points}>'


class Badge(db.Model):
    """Badge definitions — awarded based on achievements."""
    __tablename__ = 'badges'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(80),  nullable=False)
    description = db.Column(db.Text,        nullable=True)
    icon        = db.Column(db.String(10),  nullable=True)
    requirement = db.Column(db.Integer,     default=5)  # correct answers needed

    earners = db.relationship('UserBadge', backref='badge', lazy=True)

    def __repr__(self):
        return f'<Badge {self.name}>'


class UserBadge(db.Model):
    """Junction table — which users have earned which badges."""
    __tablename__ = 'user_badges'

    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'),   nullable=False)
    badge_id  = db.Column(db.Integer, db.ForeignKey('badges.id'),  nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserBadge user={self.user_id} badge={self.badge_id}>'


class LoginAttempt(db.Model):
    """Audit log for all login attempts — supports brute-force detection."""
    __tablename__ = 'login_attempts'

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    email        = db.Column(db.String(120), nullable=False)
    ip_address   = db.Column(db.String(50),  nullable=True)
    success      = db.Column(db.Boolean,     default=False)
    attempted_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def __repr__(self):
        status = 'OK' if self.success else 'FAIL'
        return f'<LoginAttempt {self.email} [{status}] @ {self.attempted_at}>'
