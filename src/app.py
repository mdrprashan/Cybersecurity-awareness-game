# =============================================================
# app.py — CyberQuest Main Flask Application
# Author: Prashan Manandhar (CIHE241182)
# =============================================================

from flask import Flask, render_template, request, make_response
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from models import db, User

login_manager = LoginManager()
bcrypt        = Bcrypt()
mail          = Mail()


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY']                     = 'cyberquest-dev-secret-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///cyberquest.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Session security settings
    app.config['SESSION_COOKIE_HTTPONLY']  = True   # JS cannot access session cookie
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Prevents CSRF
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_DURATION'] = 2592000  # 30 days in seconds

    # Email config
    app.config['MAIL_SERVER']         = 'smtp.gmail.com'
    app.config['MAIL_PORT']           = 587
    app.config['MAIL_USE_TLS']        = True
    app.config['MAIL_USERNAME']       = 'mdrprashan10@gmail.com'
    app.config['MAIL_PASSWORD']       = 'owhvyaqpkloitslu'
    app.config['MAIL_DEFAULT_SENDER'] = ('CyberQuest', 'mdrprashan10@gmail.com')

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    login_manager.login_view             = 'auth.login'
    login_manager.login_message          = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Register Blueprints ───────────────────────────────
    from auth  import auth_bp
    from game  import game_bp
    from admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(admin_bp)

    # ── Landing page ──────────────────────────────────────
    @app.route('/')
    def index():
        return render_template('index.html')

    # ── Global after_request handler ─────────────────────
    # Adds cache-control headers to ALL responses
    # This prevents the browser from caching protected pages
    # So pressing Back after logout always shows fresh content
    @app.after_request
    def add_security_headers(response):
        # For authenticated users — never cache their pages
        if current_user.is_authenticated:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response.headers['Pragma']        = 'no-cache'
            response.headers['Expires']       = '0'
        # For public pages — allow short caching
        else:
            response.headers['Cache-Control'] = 'no-cache'

        # Security headers for all pages
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options']        = 'SAMEORIGIN'
        return response

    # ── Create tables and seed ────────────────────────────
    with app.app_context():
        db.create_all()
        seed_badges()
        seed_admin_account()

    return app


def seed_badges():
    from models import Badge
    default_badges = [
        {'name': 'Phishing Expert',     'description': 'Completed all Phishing Awareness challenges',  'criteria': 'Answer all 5 phishing questions',       'icon': 'shield-check'},
        {'name': 'Password Pro',        'description': 'Scored 100% on Password Security challenges',  'criteria': 'Get all 5 password questions correct',   'icon': 'lock-fill'},
        {'name': 'Safe Surfer',         'description': 'Completed all Safe Browsing challenges',        'criteria': 'Answer all 5 safe browsing questions',   'icon': 'globe2'},
        {'name': 'CyberQuest Champion', 'description': 'Completed all 15 challenges',                  'criteria': 'Answer all questions in all categories', 'icon': 'trophy-fill'},
        {'name': 'Perfect Score',       'description': 'Achieved 100% correct across all challenges',  'criteria': 'Get every single question correct',      'icon': 'star-fill'},
    ]
    for b in default_badges:
        if not Badge.query.filter_by(name=b['name']).first():
            db.session.add(Badge(**b))
    db.session.commit()


def seed_admin_account():
    if not User.query.filter_by(username='admin').first():
        admin_hash = bcrypt.generate_password_hash('Admin1234!').decode('utf-8')
        db.session.add(User(
            username='admin',
            email='admin@cyberquest.com',
            password_hash=admin_hash,
            role='teacher'
        ))
        db.session.commit()
        print('✅ Default admin account created — username: admin | password: Admin1234!')


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)