"""
conftest.py — Shared pytest fixtures
CyberQuest ICT932 – Cybersecurity Testing and Assurance

Location : Cybersecurity-awareness-game/tests/conftest.py
Run from : Cybersecurity-awareness-game/
Command  : python -m pytest tests/ -v
"""

import os
import sys
import importlib.util
import pytest

# ── Add tests/ dir so 'from conftest import login, logout' works ──────────────
_tests_dir = os.path.dirname(os.path.abspath(__file__))
if _tests_dir not in sys.path:
    sys.path.insert(0, _tests_dir)

# ── Find src/ directory ───────────────────────────────────────────────────────
def _find_src():
    current = _tests_dir
    for _ in range(5):
        candidate = os.path.join(current, 'src')
        if os.path.isdir(candidate):
            return candidate
        current = os.path.dirname(current)
    raise RuntimeError("Cannot find src/ directory")

_src_dir = _find_src()

# ── Force-load src/app.py explicitly by FILE PATH ────────────────────────────
# This bypasses any root-level app.py conflict entirely
def _load_src_module(module_name):
    """Load a module from src/ by explicit path, not by name."""
    path = os.path.join(_src_dir, module_name + '.py')
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod   # register it so relative imports work
    spec.loader.exec_module(mod)
    return mod

# Pre-load all src modules in dependency order so imports resolve correctly
for _mod in ['extensions', 'models', 'security', 'auth', 'game', 'admin', 'app']:
    if _mod not in sys.modules:
        try:
            _load_src_module(_mod)
        except Exception:
            pass   # some may fail until app context is ready — that's OK

# Also add src/ to path for any remaining relative imports inside blueprints
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# ── Set env vars BEFORE create_app() runs ────────────────────────────────────
os.environ['SECRET_KEY']   = 'test-secret-key-for-pytest-only'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['FLASK_ENV']    = 'development'


# ══════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════

@pytest.fixture(scope='session')
def app():
    """Flask test app with in-memory SQLite."""
    from app import create_app
    test_app = create_app()
    test_app.config.update({
        'TESTING':            True,
        'WTF_CSRF_ENABLED':   False,
        'MAX_LOGIN_ATTEMPTS': 5,
        'LOCKOUT_MINUTES':    15,
    })
    yield test_app


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()


@pytest.fixture(scope='session')
def db(app):
    from extensions import db as _db
    return _db


@pytest.fixture(scope='session')
def student_user(app, db):
    from models import User
    from extensions import bcrypt
    with app.app_context():
        user = User.query.filter_by(email='pytest_student@test.com').first()
        if not user:
            user = User(
                username='pytest_student',
                email='pytest_student@test.com',
                password=bcrypt.generate_password_hash('Test1234!').decode('utf-8'),
                role='student'
            )
            db.session.add(user)
            db.session.commit()
        return user


@pytest.fixture(scope='session')
def teacher_user(app, db):
    from models import User
    from extensions import bcrypt
    with app.app_context():
        user = User.query.filter_by(email='pytest_teacher@test.com').first()
        if not user:
            user = User(
                username='pytest_teacher',
                email='pytest_teacher@test.com',
                password=bcrypt.generate_password_hash('Teach1234!').decode('utf-8'),
                role='teacher'
            )
            db.session.add(user)
            db.session.commit()
        return user


# ── Login / Logout helpers ────────────────────────────────────────────────────

def login(client, email, password):
    return client.post('/login', data={
        'email': email, 'password': password
    }, follow_redirects=True)


def logout(client):
    return client.get('/logout', follow_redirects=True)
