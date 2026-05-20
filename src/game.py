from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Challenge, Score, Badge, UserBadge

current_user_id = 1

game_bp = Blueprint("game", __name__)


@game_bp.route("/challenges")
def challenges():
    categories = ["Phishing Awareness", "Password Security", "Safe Browsing"]
    return render_template("challenges.html", categories=categories)


@game_bp.route("/challenge/<category>")
def challenge_category(category):
    questions = Challenge.query.filter_by(category=category).all()

    answered_ids = [
        score.challenge_id
        for score in Score.query.filter_by(user_id=current_user_id).all()
    ]

    return render_template(
        "question.html",
        questions=questions,
        answered_ids=answered_ids,
        category=category
    )


@game_bp.route("/question/<int:challenge_id>")
def question(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)
    return render_template("question.html", challenge=challenge)


@game_bp.route("/answer/<int:challenge_id>", methods=["POST"])
def answer(challenge_id):
    challenge = Challenge.query.get_or_404(challenge_id)

    selected_answer = request.form.get("answer")

    is_correct = selected_answer == challenge.correct_answer

    points = challenge.points if is_correct else 0

    score = Score(
        user_id=current_user_id,
        challenge_id=challenge.id,
        selected_answer=selected_answer,
        is_correct=is_correct,
        points=points
    )

    db.session.add(score)
    db.session.commit()

    if is_correct:
        flash(f"Correct! You earned {points} points.", "success")
    else:
        flash("Incorrect. Try again.", "danger")

    check_and_award_badges(current_user_id)

    return redirect(url_for("game.result"))


@game_bp.route("/result")
def result():
    scores = Score.query.filter_by(user_id=current_user_id).all()

    total_score = sum(score.points for score in scores)

    total_questions = Challenge.query.count()

    answered = len(scores)

    percentage = 0

    if total_questions > 0:
        percentage = round((answered / total_questions) * 100, 2)

    badges = UserBadge.query.filter_by(user_id=current_user_id).all()

    return render_template(
        "result.html",
        total_score=total_score,
        percentage=percentage,
        badges=badges
    )


@game_bp.route("/progress")
def progress():
    scores = Score.query.filter_by(user_id=current_user_id).all()

    total_score = sum(score.points for score in scores)

    total_questions = Challenge.query.count()

    answered = len(scores)

    percentage = 0

    if total_questions > 0:
        percentage = round((answered / total_questions) * 100, 2)

    recent_activity = scores[-5:]

    badges = UserBadge.query.filter_by(user_id=current_user_id).all()

    return render_template(
        "progress.html",
        total_score=total_score,
        percentage=percentage,
        recent_activity=recent_activity,
        badges=badges
    )


def check_and_award_badges(user_id):

    scores = Score.query.filter_by(user_id=user_id).all()

    total_answered = len(scores)

    total_correct = len([s for s in scores if s.is_correct])

    def award_badge(name, icon):

        existing_badge = Badge.query.filter_by(name=name).first()

        if not existing_badge:

            existing_badge = Badge(name=name, icon=icon)

            db.session.add(existing_badge)

            db.session.commit()

        already_awarded = UserBadge.query.filter_by(
            user_id=user_id,
            badge_id=existing_badge.id
        ).first()

        if not already_awarded:

            user_badge = UserBadge(
                user_id=user_id,
                badge_id=existing_badge.id
            )

            db.session.add(user_badge)

            db.session.commit()

    if total_answered >= 5:
        award_badge("Phishing Expert", "🎣")

    if total_correct >= 5:
        award_badge("Password Pro", "🔐")

    if total_answered >= 10:
        award_badge("Safe Surfer", "🌐")

    if total_answered >= 15:
        award_badge("CyberQuest Champion", "🏆")

    if total_answered >= 15 and total_correct == 15:
        award_badge("Perfect Score", "⭐")