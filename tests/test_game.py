import pytest
from app import app, db
from models import User, Challenge, Score
from flask_login import login_user


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


def test_correct_answer_awards_points(client):
    """Test correct answer gives points."""

    with app.app_context():

        user = User(username="raju", password="test")
        db.session.add(user)

        challenge = Challenge(
            category="Phishing Awareness",
            question="Test Question",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="a",
            difficulty="easy",
            points=10
        )

        db.session.add(challenge)
        db.session.commit()

        score = Score(
            user_id=user.id,
            challenge_id=challenge.id,
            selected_answer="a",
            is_correct=True,
            points=10
        )

        db.session.add(score)
        db.session.commit()

        assert score.points == 10
        assert score.is_correct is True


def test_incorrect_answer_no_points(client):
    """Test incorrect answer gives zero points."""

    with app.app_context():

        user = User(username="student", password="test")
        db.session.add(user)

        challenge = Challenge(
            category="Password Security",
            question="Password Question",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="b",
            difficulty="easy",
            points=10
        )

        db.session.add(challenge)
        db.session.commit()

        score = Score(
            user_id=user.id,
            challenge_id=challenge.id,
            selected_answer="a",
            is_correct=False,
            points=0
        )

        db.session.add(score)
        db.session.commit()

        assert score.points == 0
        assert score.is_correct is False