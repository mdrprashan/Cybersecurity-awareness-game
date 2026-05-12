# =============================================================
# conftest.py — Shared Pytest Fixtures
# Author: Prashan Manandhar (CIHE241182)
# Description: Sets up a clean in-memory test database and
#              test client for all pytest tests.
# =============================================================

import pytest
import sys
import os

# Add src/ to Python path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture(scope='session')
def app():
    """
    Creates a Flask test app with in-memory SQLite database.
    Session scope = runs once for the entire test suite.
    """
    from app import create_app
    from models import db

    test_app = create_app()

    test_app.config.update({
        'TESTING':                 True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED':        False,
        'MAIL_SUPPRESS_SEND':      True,
        'SECRET_KEY':              'test-secret-key',
        'LOGIN_DISABLED':          False,
    })

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Flask test client — simulates browser requests."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Clean database session per test — rolls back after each."""
    from models import db
    with app.app_context():
        yield db
        db.session.rollback()


@pytest.fixture
def student_user(app, db_session):
    """Creates a test student account in the database."""
    from models import User, db
    from app import bcrypt
    with app.app_context():
        existing = User.query.filter_by(username='test_student').first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        user = User(
            username='test_student',
            email='student@test.com',
            password_hash=bcrypt.generate_password_hash('Test1234!').decode('utf-8'),
            role='student'
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def teacher_user(app, db_session):
    """Creates a test teacher account in the database."""
    from models import User, db
    from app import bcrypt
    with app.app_context():
        existing = User.query.filter_by(username='test_teacher').first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        user = User(
            username='test_teacher',
            email='teacher@test.com',
            password_hash=bcrypt.generate_password_hash('Test1234!').decode('utf-8'),
            role='teacher'
        )
        db.session.add(user)
        db.session.commit()
        return user
