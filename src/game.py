"""
game.py — Game Blueprint
ICT932 – Cybersecurity Testing and Assurance
Author: Raju Kshetri (CIHE240711)
Fixed integration: Prashan Manandhar (CIHE241182)

Security fixes applied:
  - selected_answer validated as A/B/C/D before processing
  - db.session.get() used instead of deprecated get_or_404
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Challenge, Score, Badge, UserBadge

game_bp = Blueprint("game", __name__)

POINTS_MAP     = {'easy': 10, 'medium': 20, 'hard': 30}
VALID_ANSWERS  = {'A', 'B', 'C', 'D'}

CATEGORIES = [
    {'key': 'phishing', 'label': 'Phishing Awareness', 'icon': '🎣',
     'description': 'Learn to spot phishing emails and social engineering attacks.'},
    {'key': 'password', 'label': 'Password Security',  'icon': '🔐',
     'description': 'Master the art of strong passwords and authentication.'},
    {'key': 'browsing', 'label': 'Safe Browsing',      'icon': '🌐',
     'description': 'Stay safe online — VPNs, HTTPS, and browser threats.'},
]


@game_bp.route("/challenges")
@login_required
def challenges():
    category_data = []
    for cat in CATEGORIES:
        total     = Challenge.query.filter_by(category=cat['key']).count()
        completed = Score.query.filter_by(
            user_id=current_user.id,
            is_correct=True
        ).join(Challenge).filter(Challenge.category == cat['key']).count()
        category_data.append({**cat, 'total': total, 'completed': completed})

    total_score = sum(s.points for s in Score.query.filter_by(user_id=current_user.id).all())
    badges      = UserBadge.query.filter_by(user_id=current_user.id).all()

    return render_template("challenges.html",
                           categories=category_data,
                           total_score=total_score,
                           badges=badges)


@game_bp.route("/challenge/<category>")
@login_required
def challenge_category(category):
    # SECURITY FIX: validate category against known values
    valid_keys = {c['key'] for c in CATEGORIES}
    if category not in valid_keys:
        flash('Unknown challenge category.', 'danger')
        return redirect(url_for('game.challenges'))

    questions    = Challenge.query.filter_by(category=category).all()
    answered_ids = [
        score.challenge_id
        for score in Score.query.filter_by(user_id=current_user.id).all()
    ]
    cat_info = next(c for c in CATEGORIES if c['key'] == category)

    return render_template("question.html",
                           questions=questions,
                           answered_ids=answered_ids,
                           category=category,
                           cat_info=cat_info)


@game_bp.route("/question/<int:challenge_id>")
@login_required
def question(challenge_id):
    challenge = db.session.get(Challenge, challenge_id)
    if not challenge:
        flash('Challenge not found.', 'danger')
        return redirect(url_for('game.challenges'))
    return render_template("single_question.html", challenge=challenge)


@game_bp.route("/answer/<int:challenge_id>", methods=["POST"])
@login_required
def answer(challenge_id):
    challenge = db.session.get(Challenge, challenge_id)
    if not challenge:
        flash('Challenge not found.', 'danger')
        return redirect(url_for('game.challenges'))

    selected_answer = request.form.get("answer", "").upper().strip()

    # SECURITY FIX: reject anything that isn't A/B/C/D
    if selected_answer not in VALID_ANSWERS:
        flash('Invalid answer submitted.', 'danger')
        return redirect(url_for('game.challenge_category', category=challenge.category))

    # Prevent re-answering
    existing = Score.query.filter_by(
        user_id=current_user.id, challenge_id=challenge_id).first()
    if existing:
        flash('You have already answered this question.', 'info')
        return redirect(url_for('game.challenge_category', category=challenge.category))

    is_correct = selected_answer == challenge.correct_answer.upper()
    points     = POINTS_MAP.get(challenge.difficulty, 10) if is_correct else 0

    score = Score(
        user_id=current_user.id,
        challenge_id=challenge.id,
        is_correct=is_correct,
        points=points
    )
    db.session.add(score)
    db.session.commit()

    if is_correct:
        flash(f'✅ Correct! +{points} points. {challenge.explanation}', 'success')
    else:
        correct_text = getattr(challenge, f'option_{challenge.correct_answer.lower()}')
        flash(f'❌ Incorrect. Correct answer: {challenge.correct_answer} — {correct_text}. '
              f'{challenge.explanation}', 'danger')

    _check_and_award_badges(current_user.id)
    return redirect(url_for('game.challenge_category', category=challenge.category))


@game_bp.route("/result")
@login_required
def result():
    scores          = Score.query.filter_by(user_id=current_user.id).all()
    total_score     = sum(s.points for s in scores)
    total_questions = Challenge.query.count()
    answered        = len(scores)
    correct         = sum(1 for s in scores if s.is_correct)
    percentage      = round((correct / total_questions) * 100, 1) if total_questions > 0 else 0
    badges          = UserBadge.query.filter_by(user_id=current_user.id).all()

    return render_template("result.html",
                           total_score=total_score,
                           percentage=percentage,
                           answered=answered,
                           correct=correct,
                           total_questions=total_questions,
                           badges=badges)


@game_bp.route("/progress")
@login_required
def progress():
    scores          = Score.query.filter_by(user_id=current_user.id).all()
    total_score     = sum(s.points for s in scores)
    total_questions = Challenge.query.count()
    answered        = len(scores)
    correct         = sum(1 for s in scores if s.is_correct)
    percentage      = round((correct / total_questions) * 100, 1) if total_questions > 0 else 0
    recent_activity = scores[-5:]
    badges          = UserBadge.query.filter_by(user_id=current_user.id).all()

    return render_template("progress.html",
                           total_score=total_score,
                           percentage=percentage,
                           answered=answered,
                           correct=correct,
                           recent_activity=recent_activity,
                           badges=badges)


def _check_and_award_badges(user_id):
    scores         = Score.query.filter_by(user_id=user_id).all()
    total_answered = len(scores)
    total_correct  = sum(1 for s in scores if s.is_correct)

    def _award(name, icon):
        badge = Badge.query.filter_by(name=name).first()
        if not badge:
            badge = Badge(name=name, icon=icon)
            db.session.add(badge)
            db.session.commit()
        if not UserBadge.query.filter_by(user_id=user_id, badge_id=badge.id).first():
            db.session.add(UserBadge(user_id=user_id, badge_id=badge.id))
            db.session.commit()
            flash(f'🏅 Badge unlocked: {icon} {name}!', 'success')

    if total_answered >= 1:  _award('Security Rookie', '⭐')
    if total_correct  >= 3:  _award('Phishing Detector', '🎣')
    if total_correct  >= 3:  _award('Password Pro', '🔐')
    if total_correct  >= 3:  _award('Safe Surfer', '🌐')
    if total_answered >= 15: _award('CyberQuest Champion', '🏆')
