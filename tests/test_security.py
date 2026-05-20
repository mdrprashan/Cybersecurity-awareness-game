"""
test_security.py — Security & Brute-Force Detection Tests
ICT932 – Cybersecurity Testing and Assurance
Author: Prashan Manandhar (CIHE241182)
"""

import pytest
from datetime import datetime, timedelta
from app import create_app, db
from models import User, LoginAttempt
from security import log_login_attempt, is_account_locked


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def app():
    test_app = create_app()
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret',
        'MAX_LOGIN_ATTEMPTS': 5,
        'LOCKOUT_MINUTES': 15,
    })
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='module')
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_attempts(app):
    """Wipe login attempts before each test."""
    with app.app_context():
        LoginAttempt.query.delete()
        db.session.commit()


# ── Login Attempt Logging ─────────────────────────────────────────────────────

class TestLoginAttemptLogging:

    def test_log_failed_attempt(self, app):
        """Failed login attempt is recorded in the database."""
        with app.app_context():
            log_login_attempt(email='victim@example.com',
                              ip='1.2.3.4', success=False)
            attempt = LoginAttempt.query.filter_by(
                email='victim@example.com').first()
            assert attempt is not None
            assert attempt.success is False
            assert attempt.ip_address == '1.2.3.4'

    def test_log_successful_attempt(self, app):
        """Successful login attempt is recorded as success=True."""
        with app.app_context():
            log_login_attempt(email='success@example.com',
                              ip='5.6.7.8', success=True)
            attempt = LoginAttempt.query.filter_by(
                email='success@example.com').first()
            assert attempt is not None
            assert attempt.success is True

    def test_multiple_attempts_logged(self, app):
        """Multiple attempts for same email are all stored."""
        with app.app_context():
            for _ in range(3):
                log_login_attempt(email='multi@example.com',
                                  ip='1.1.1.1', success=False)
            count = LoginAttempt.query.filter_by(
                email='multi@example.com').count()
            assert count == 3


# ── Brute-Force Lockout Detection ─────────────────────────────────────────────

class TestBruteForceDetection:

    def test_not_locked_below_threshold(self, app):
        """Account is NOT locked below MAX_LOGIN_ATTEMPTS failures."""
        with app.app_context():
            for _ in range(4):   # threshold is 5
                log_login_attempt(email='safe@example.com',
                                  ip='9.9.9.9', success=False)
            assert is_account_locked('safe@example.com') is False

    def test_locked_at_threshold(self, app):
        """Account IS locked once MAX_LOGIN_ATTEMPTS is reached."""
        with app.app_context():
            for _ in range(5):
                log_login_attempt(email='locked@example.com',
                                  ip='9.9.9.9', success=False)
            assert is_account_locked('locked@example.com') is True

    def test_locked_above_threshold(self, app):
        """Account remains locked above the threshold."""
        with app.app_context():
            for _ in range(7):
                log_login_attempt(email='extra_locked@example.com',
                                  ip='9.9.9.9', success=False)
            assert is_account_locked('extra_locked@example.com') is True

    def test_successful_login_does_not_count_toward_lockout(self, app):
        """Successful attempts are not counted in the failed-attempt total."""
        with app.app_context():
            # 3 failures + 1 success = still under threshold
            for _ in range(3):
                log_login_attempt(email='mixed@example.com',
                                  ip='2.2.2.2', success=False)
            log_login_attempt(email='mixed@example.com',
                              ip='2.2.2.2', success=True)
            assert is_account_locked('mixed@example.com') is False

    def test_old_attempts_outside_window_ignored(self, app):
        """Attempts older than LOCKOUT_MINUTES are not counted."""
        with app.app_context():
            old_time = datetime.utcnow() - timedelta(minutes=20)
            for _ in range(5):
                attempt = LoginAttempt(
                    email='old_attempts@example.com',
                    ip_address='3.3.3.3',
                    success=False,
                    attempted_at=old_time
                )
                db.session.add(attempt)
            db.session.commit()
            # These are all older than 15 minutes — should NOT be locked
            assert is_account_locked('old_attempts@example.com') is False

    def test_unknown_email_not_locked(self, app):
        """An email with no attempts is never locked."""
        with app.app_context():
            assert is_account_locked('nobody@nowhere.com') is False


# ── Security Route Access Control ─────────────────────────────────────────────

class TestSecurityRoutes:

    def test_audit_log_requires_login(self, client):
        """Unauthenticated access to /security/audit-log redirects to login."""
        response = client.get('/security/audit-log', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers.get('Location', '')

    def test_locked_accounts_requires_login(self, client):
        """Unauthenticated access to /security/locked-accounts redirects."""
        response = client.get('/security/locked-accounts', follow_redirects=False)
        assert response.status_code == 302

    def test_student_blocked_from_audit_log(self, client, app):
        """Students cannot access the audit log (teacher-only)."""
        from app import bcrypt
        with app.app_context():
            student = User(
                username='securestudent',
                email='securestudent@test.com',
                password=bcrypt.generate_password_hash('Test1234!').decode('utf-8'),
                role='student'
            )
            db.session.add(student)
            db.session.commit()

        client.post('/login', data={
            'email': 'securestudent@test.com',
            'password': 'Test1234!'
        })
        response = client.get('/security/audit-log', follow_redirects=True)
        # Should be redirected away or shown a 403-equivalent message
        assert b'permission' in response.data or b'Access denied' in response.data or response.status_code in (302, 403)


# ── LoginAttempt Model Tests ──────────────────────────────────────────────────

class TestLoginAttemptModel:

    def test_attempt_has_timestamp(self, app):
        """LoginAttempt records a timestamp automatically."""
        with app.app_context():
            log_login_attempt(email='ts@test.com', ip='1.1.1.1', success=False)
            attempt = LoginAttempt.query.filter_by(email='ts@test.com').first()
            assert attempt.attempted_at is not None
            assert isinstance(attempt.attempted_at, datetime)

    def test_attempt_repr(self, app):
        """LoginAttempt __repr__ works correctly."""
        with app.app_context():
            log_login_attempt(email='repr@test.com', ip='1.1.1.1', success=True)
            attempt = LoginAttempt.query.filter_by(email='repr@test.com').first()
            assert 'repr@test.com' in repr(attempt)
