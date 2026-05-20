"""
test_auth.py — Authentication Unit Tests
ICT932 – Cybersecurity Testing and Assurance
Author: Prashan Manandhar (CIHE241182)
"""

import pytest
from app import create_app, db, bcrypt
from models import User


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def app():
    """Create a test Flask application with in-memory SQLite database."""
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


@pytest.fixture(scope='module')
def test_user(app):
    """Create a test student user."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password=bcrypt.generate_password_hash('Test1234!').decode('utf-8'),
            role='student'
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture(scope='module')
def test_teacher(app):
    """Create a test teacher user."""
    with app.app_context():
        teacher = User(
            username='testteacher',
            email='teacher@test.com',
            password=bcrypt.generate_password_hash('Teach1234!').decode('utf-8'),
            role='teacher'
        )
        db.session.add(teacher)
        db.session.commit()
        return teacher


# ── Registration Tests ────────────────────────────────────────────────────────

class TestRegistration:

    def test_register_page_loads(self, client):
        """GET /register returns 200."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Create Account' in response.data

    def test_register_new_user(self, client, app):
        """POST /register with valid data creates user and redirects."""
        response = client.post('/register', data={
            'username': 'newstudent',
            'email':    'newstudent@example.com',
            'password': 'Secure99!',
            'confirm_password': 'Secure99!',
            'role': 'student'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Account created' in response.data or b'Sign in' in response.data

        with app.app_context():
            user = User.query.filter_by(email='newstudent@example.com').first()
            assert user is not None
            assert user.role == 'student'

    def test_register_duplicate_email(self, client, test_user, app):
        """Registering with an existing email shows an error."""
        response = client.post('/register', data={
            'username': 'anotheruser',
            'email':    'test@example.com',   # already exists
            'password': 'Test1234!',
            'confirm_password': 'Test1234!',
            'role': 'student'
        }, follow_redirects=True)
        assert b'already exists' in response.data

    def test_register_password_mismatch(self, client):
        """Mismatched passwords are rejected."""
        response = client.post('/register', data={
            'username': 'mismatch',
            'email':    'mismatch@example.com',
            'password': 'Test1234!',
            'confirm_password': 'Different99!',
            'role': 'student'
        }, follow_redirects=True)
        assert b'do not match' in response.data

    def test_register_weak_password(self, client):
        """A weak password (no uppercase/symbol) is rejected."""
        response = client.post('/register', data={
            'username': 'weakpw',
            'email':    'weakpw@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'student'
        }, follow_redirects=True)
        assert b'uppercase' in response.data or b'special' in response.data

    def test_register_missing_fields(self, client):
        """Submitting with empty fields returns an error."""
        response = client.post('/register', data={
            'username': '',
            'email':    '',
            'password': '',
            'confirm_password': '',
            'role': 'student'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'required' in response.data


# ── Login Tests ───────────────────────────────────────────────────────────────

class TestLogin:

    def test_login_page_loads(self, client):
        """GET /login returns 200."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Sign In' in response.data

    def test_login_valid_credentials(self, client, test_user):
        """Login with correct credentials redirects to challenges."""
        response = client.post('/login', data={
            'email':    'test@example.com',
            'password': 'Test1234!'
        }, follow_redirects=True)
        assert response.status_code == 200
        # Should be redirected somewhere (not just login page again)
        assert b'Invalid email or password' not in response.data

    def test_login_wrong_password(self, client):
        """Wrong password shows error."""
        response = client.post('/login', data={
            'email':    'test@example.com',
            'password': 'WrongPassword99!'
        }, follow_redirects=True)
        assert b'Invalid email or password' in response.data

    def test_login_nonexistent_user(self, client):
        """Login with unknown email shows error."""
        response = client.post('/login', data={
            'email':    'nobody@nowhere.com',
            'password': 'Test1234!'
        }, follow_redirects=True)
        assert b'Invalid email or password' in response.data

    def test_login_empty_fields(self, client):
        """Submitting empty login form is handled gracefully."""
        response = client.post('/login', data={
            'email': '', 'password': ''
        }, follow_redirects=True)
        assert response.status_code == 200


# ── Logout Tests ──────────────────────────────────────────────────────────────

class TestLogout:

    def test_logout_redirects_to_login(self, client):
        """Logging out redirects to the login page."""
        # Login first
        client.post('/login', data={
            'email': 'test@example.com', 'password': 'Test1234!'
        })
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Sign In' in response.data or b'logged out' in response.data

    def test_logout_requires_login(self, client):
        """Accessing /logout without being logged in redirects."""
        response = client.get('/logout', follow_redirects=False)
        assert response.status_code in (302, 200)


# ── Password Strength Validation Tests ────────────────────────────────────────

class TestPasswordValidation:

    def test_valid_strong_password(self, app):
        """Strong password passes all checks."""
        from auth import _validate_password_strength
        with app.app_context():
            errors = _validate_password_strength('Tr0ub4dor&3')
            assert errors == []

    def test_short_password_rejected(self, app):
        """Passwords under 8 characters are rejected."""
        from auth import _validate_password_strength
        with app.app_context():
            errors = _validate_password_strength('Ab1!')
            assert any('8 characters' in e for e in errors)

    def test_no_uppercase_rejected(self, app):
        """Password without uppercase is rejected."""
        from auth import _validate_password_strength
        with app.app_context():
            errors = _validate_password_strength('abcdef1!')
            assert any('uppercase' in e for e in errors)

    def test_no_symbol_rejected(self, app):
        """Password without special characters is rejected."""
        from auth import _validate_password_strength
        with app.app_context():
            errors = _validate_password_strength('Abcdef12')
            assert any('special' in e for e in errors)


# ── RBAC Tests ────────────────────────────────────────────────────────────────

class TestRBAC:

    def test_teacher_role_assigned(self, app, test_teacher):
        """Teacher user has correct role."""
        with app.app_context():
            teacher = User.query.filter_by(email='teacher@test.com').first()
            assert teacher is not None
            assert teacher.role == 'teacher'
            assert teacher.is_teacher is True

    def test_student_is_not_teacher(self, app, test_user):
        """Student user does not have teacher privileges."""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            assert user.is_teacher is False
