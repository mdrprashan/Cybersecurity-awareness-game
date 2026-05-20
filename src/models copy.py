from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# =========================================================
# USER MODEL
# =========================================================
class User(UserMixin, db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), default='student')

    totp_secret = db.Column(db.String(32))

    login_attempts = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================================================
# CHALLENGE MODEL
# =========================================================
class Challenge(db.Model):

    __tablename__ = 'challenges'

    id = db.Column(db.Integer, primary_key=True)

    category = db.Column(db.String(50), nullable=False)

    question = db.Column(db.Text, nullable=False)

    option_a = db.Column(db.String(255), nullable=False)

    option_b = db.Column(db.String(255), nullable=False)

    option_c = db.Column(db.String(255), nullable=False)

    option_d = db.Column(db.String(255), nullable=False)

    correct_answer = db.Column(db.String(1), nullable=False)

    difficulty = db.Column(db.String(20))

    points = db.Column(db.Integer, default=10)


# =========================================================
# SCORE MODEL
# =========================================================
class Score(db.Model):

    __tablename__ = 'scores'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'))

    is_correct = db.Column(db.Boolean, default=False)

    answered_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================================================
# BADGE MODEL
# =========================================================
class Badge(db.Model):

    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    description = db.Column(db.String(255))


# =========================================================
# USER BADGE MODEL
# =========================================================
class UserBadge(db.Model):

    __tablename__ = 'user_badges'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'))

    earned_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================================================
# LOGIN ATTEMPT MODEL
# =========================================================
class LoginAttempt(db.Model):

    __tablename__ = 'login_attempts'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    success = db.Column(db.Boolean)

    ip_address = db.Column(db.String(100))

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)