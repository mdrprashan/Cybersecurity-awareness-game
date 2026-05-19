from extensions import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    category = db.Column(db.String(100))
    question = db.Column(db.String(500))

    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))

    correct_answer = db.Column(db.String(1))

    difficulty = db.Column(db.String(20))
    points = db.Column(db.Integer)


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)
    challenge_id = db.Column(db.Integer)

    selected_answer = db.Column(db.String(1))

    is_correct = db.Column(db.Boolean)

    points = db.Column(db.Integer)


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    icon = db.Column(db.String(20))


class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)
    badge_id = db.Column(db.Integer)