"""
test_game.py — Game Module Unit Tests
CyberQuest ICT932 – Cybersecurity Testing and Assurance
Author: Raju Kshetri (CIHE240711)

Tests cover:
  - Challenge category pages
  - Answer submission (correct and incorrect)
  - Answer validation (only A/B/C/D accepted)
  - Re-answer prevention
  - Scoring calculation (easy/medium/hard)
  - Progress and result pages
  - Badge awarding
"""

import pytest
from conftest import login, logout


# ════════════════════════════════════════════════════════════════════
# HELPER — Log in as student and bypass 2FA setup
# ════════════════════════════════════════════════════════════════════

def login_student_skip_2fa(client, app):
    """Log in and skip 2FA setup to access game routes."""
    with app.app_context():
        login(client, 'pytest_student@test.com', 'Test1234!')
    client.get('/2fa/skip', follow_redirects=True)


# ════════════════════════════════════════════════════════════════════
# CHALLENGE PAGES
# ════════════════════════════════════════════════════════════════════

class TestChallengePages:

    def test_challenges_page_requires_login(self, client):
        """GET /challenges without login redirects to login."""
        response = client.get('/challenges', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_challenges_page_loads_for_student(self, client, app):
        """Logged-in student can access /challenges."""
        login_student_skip_2fa(client, app)
        response = client.get('/challenges')
        assert response.status_code == 200
        assert b'Challenge' in response.data or b'Phishing' in response.data
        logout(client)

    def test_phishing_category_loads(self, client, app):
        """GET /challenge/phishing loads challenge questions."""
        login_student_skip_2fa(client, app)
        response = client.get('/challenge/phishing')
        assert response.status_code == 200
        logout(client)

    def test_password_category_loads(self, client, app):
        """GET /challenge/password loads challenge questions."""
        login_student_skip_2fa(client, app)
        response = client.get('/challenge/password')
        assert response.status_code == 200
        logout(client)

    def test_browsing_category_loads(self, client, app):
        """GET /challenge/browsing loads challenge questions."""
        login_student_skip_2fa(client, app)
        response = client.get('/challenge/browsing')
        assert response.status_code == 200
        logout(client)

    def test_invalid_category_redirects(self, client, app):
        """GET /challenge/invalid redirects back to challenges."""
        login_student_skip_2fa(client, app)
        response = client.get('/challenge/hacking', follow_redirects=True)
        assert response.status_code == 200
        assert b'Unknown' in response.data or b'Challenge' in response.data
        logout(client)


# ════════════════════════════════════════════════════════════════════
# ANSWER SUBMISSION
# ════════════════════════════════════════════════════════════════════

class TestAnswerSubmission:

    def _get_first_challenge(self, app, category='phishing'):
        """Helper to get first challenge ID for a category."""
        from models import Challenge
        with app.app_context():
            ch = Challenge.query.filter_by(category=category).first()
            return ch.id if ch else None

    def test_correct_answer_awards_points(self, client, app, db):
        """Submitting the correct answer awards points."""
        login_student_skip_2fa(client, app)
        with app.app_context():
            from models import Challenge, Score, User
            challenge = Challenge.query.filter_by(category='phishing').first()
            user = User.query.filter_by(email='pytest_student@test.com').first()
            if challenge and user:
                # Clear existing score for this challenge
                Score.query.filter_by(
                    user_id=user.id, challenge_id=challenge.id).delete()
                db.session.commit()
                ch_id     = challenge.id
                correct   = challenge.correct_answer
                user_id   = user.id

        if challenge:
            client.post(f'/answer/{ch_id}', data={'answer': correct},
                        follow_redirects=True)
            with app.app_context():
                from models import Score
                score = Score.query.filter_by(
                    user_id=user_id, challenge_id=ch_id).first()
                assert score is not None
                assert score.is_correct is True
                assert score.points > 0
        logout(client)

    def test_wrong_answer_scores_zero(self, client, app, db):
        """Submitting an incorrect answer scores 0 points."""
        login_student_skip_2fa(client, app)
        with app.app_context():
            from models import Challenge, Score, User
            challenge = Challenge.query.filter_by(category='password').first()
            user      = User.query.filter_by(email='pytest_student@test.com').first()
            if challenge and user:
                Score.query.filter_by(
                    user_id=user.id, challenge_id=challenge.id).delete()
                db.session.commit()
                ch_id   = challenge.id
                correct = challenge.correct_answer
                wrong   = next(a for a in ['A', 'B', 'C', 'D'] if a != correct)
                user_id = user.id

        if challenge:
            client.post(f'/answer/{ch_id}', data={'answer': wrong},
                        follow_redirects=True)
            with app.app_context():
                from models import Score
                score = Score.query.filter_by(
                    user_id=user_id, challenge_id=ch_id).first()
                assert score is not None
                assert score.is_correct is False
                assert score.points == 0
        logout(client)

    def test_invalid_answer_rejected(self, client, app, db):
        """Submitting 'X' or other invalid values is rejected."""
        login_student_skip_2fa(client, app)
        with app.app_context():
            from models import Challenge, Score, User
            challenge = Challenge.query.filter_by(category='browsing').first()
            user      = User.query.filter_by(email='pytest_student@test.com').first()
            if challenge and user:
                Score.query.filter_by(
                    user_id=user.id, challenge_id=challenge.id).delete()
                db.session.commit()
                ch_id   = challenge.id
                user_id = user.id

        if challenge:
            response = client.post(f'/answer/{ch_id}', data={'answer': 'X'},
                                   follow_redirects=True)
            # Should show invalid answer message, not record a score
            with app.app_context():
                from models import Score
                score = Score.query.filter_by(
                    user_id=user_id, challenge_id=ch_id).first()
                assert score is None or b'Invalid' in response.data
        logout(client)

    def test_empty_answer_rejected(self, client, app, db):
        """Submitting no answer is rejected."""
        login_student_skip_2fa(client, app)
        with app.app_context():
            from models import Challenge, Score, User
            challenge = Challenge.query.filter_by(category='phishing').order_by(
                Challenge.id.desc()).first()
            user = User.query.filter_by(email='pytest_student@test.com').first()
            if challenge and user:
                Score.query.filter_by(
                    user_id=user.id, challenge_id=challenge.id).delete()
                db.session.commit()
                ch_id   = challenge.id
                user_id = user.id

        if challenge:
            response = client.post(f'/answer/{ch_id}', data={'answer': ''},
                                   follow_redirects=True)
            with app.app_context():
                from models import Score
                score = Score.query.filter_by(
                    user_id=user_id, challenge_id=ch_id).first()
                assert score is None or b'Invalid' in response.data or b'select' in response.data.lower()
        logout(client)

    def test_re_answer_prevented(self, client, app, db):
        """Answering the same question twice is prevented."""
        login_student_skip_2fa(client, app)
        with app.app_context():
            from models import Challenge, Score, User
            challenge = Challenge.query.filter_by(difficulty='easy').first()
            user      = User.query.filter_by(email='pytest_student@test.com').first()
            if challenge and user:
                Score.query.filter_by(
                    user_id=user.id, challenge_id=challenge.id).delete()
                db.session.commit()
                ch_id   = challenge.id
                correct = challenge.correct_answer
                user_id = user.id

        if challenge:
            # First answer
            client.post(f'/answer/{ch_id}', data={'answer': correct})
            # Second answer (should be blocked)
            response = client.post(f'/answer/{ch_id}', data={'answer': correct},
                                   follow_redirects=True)
            assert b'already answered' in response.data
            # Should still only have 1 score record
            with app.app_context():
                from models import Score
                count = Score.query.filter_by(
                    user_id=user_id, challenge_id=ch_id).count()
                assert count == 1
        logout(client)


# ════════════════════════════════════════════════════════════════════
# SCORING SYSTEM
# ════════════════════════════════════════════════════════════════════

class TestScoringSystem:

    def test_easy_question_worth_10_points(self, app):
        """Easy challenges are worth 10 points."""
        with app.app_context():
            from game import POINTS_MAP
            assert POINTS_MAP['easy'] == 10

    def test_medium_question_worth_20_points(self, app):
        """Medium challenges are worth 20 points."""
        with app.app_context():
            from game import POINTS_MAP
            assert POINTS_MAP['medium'] == 20

    def test_hard_question_worth_30_points(self, app):
        """Hard challenges are worth 30 points."""
        with app.app_context():
            from game import POINTS_MAP
            assert POINTS_MAP['hard'] == 30

    def test_correct_answer_validation(self, app):
        """Only A, B, C, D are valid answer choices."""
        with app.app_context():
            from game import VALID_ANSWERS
            assert VALID_ANSWERS == {'A', 'B', 'C', 'D'}
            assert 'X' not in VALID_ANSWERS
            assert 'E' not in VALID_ANSWERS
            assert '' not in VALID_ANSWERS


# ════════════════════════════════════════════════════════════════════
# PROGRESS & RESULT PAGES
# ════════════════════════════════════════════════════════════════════

class TestProgressAndResults:

    def test_progress_page_loads(self, client, app):
        """Logged-in student can access /progress."""
        login_student_skip_2fa(client, app)
        response = client.get('/progress')
        assert response.status_code == 200
        assert b'Progress' in response.data
        logout(client)

    def test_result_page_loads(self, client, app):
        """Logged-in student can access /result."""
        login_student_skip_2fa(client, app)
        response = client.get('/result')
        assert response.status_code == 200
        logout(client)

    def test_progress_requires_login(self, client):
        """GET /progress without login redirects."""
        response = client.get('/progress', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_result_requires_login(self, client):
        """GET /result without login redirects."""
        response = client.get('/result', follow_redirects=False)
        assert response.status_code in (302, 308)


# ════════════════════════════════════════════════════════════════════
# DATABASE: CHALLENGE SEEDING
# ════════════════════════════════════════════════════════════════════

class TestChallengeData:

    def test_15_challenges_seeded(self, app):
        """Database should have exactly 15 challenges."""
        with app.app_context():
            from models import Challenge
            count = Challenge.query.count()
            assert count == 15

    def test_5_phishing_challenges(self, app):
        """There should be 5 phishing challenges."""
        with app.app_context():
            from models import Challenge
            count = Challenge.query.filter_by(category='phishing').count()
            assert count == 5

    def test_5_password_challenges(self, app):
        """There should be 5 password challenges."""
        with app.app_context():
            from models import Challenge
            count = Challenge.query.filter_by(category='password').count()
            assert count == 5

    def test_5_browsing_challenges(self, app):
        """There should be 5 safe browsing challenges."""
        with app.app_context():
            from models import Challenge
            count = Challenge.query.filter_by(category='browsing').count()
            assert count == 5

    def test_all_challenges_have_correct_answer(self, app):
        """Every challenge has a correct_answer of A, B, C, or D."""
        with app.app_context():
            from models import Challenge
            challenges = Challenge.query.all()
            for ch in challenges:
                assert ch.correct_answer in ('A', 'B', 'C', 'D'), \
                    f"Challenge {ch.id} has invalid answer: {ch.correct_answer}"

    def test_all_difficulties_present(self, app):
        """Challenges include easy, medium, and hard difficulties."""
        with app.app_context():
            from models import Challenge
            difficulties = {ch.difficulty for ch in Challenge.query.all()}
            assert 'easy' in difficulties
            assert 'medium' in difficulties
            assert 'hard' in difficulties

    def test_badges_seeded(self, app):
        """At least 5 badges should be seeded."""
        with app.app_context():
            from models import Badge
            count = Badge.query.count()
            assert count >= 5
