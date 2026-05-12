# =============================================================
# app.py — CyberQuest Main Flask Application
# Author: Prashan Manandhar (CIHE241182)
# Description: Application factory pattern entry point.
#              Initialises all extensions and registers blueprints.
# =============================================================

from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from models import db, User

# Initialise extensions (not yet bound to app)
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app():
    """
    Application factory function.
    Creates and configures the Flask app instance.
    Returns the configured app.
    """
    app = Flask(__name__)

    # ---------------------------------------------------------
    # App Configuration
    # ---------------------------------------------------------
    app.config['SECRET_KEY'] = 'cyberquest-dev-secret-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cyberquest.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ---------------------------------------------------------
    # Initialise Extensions with App
    # ---------------------------------------------------------
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Redirect unauthenticated users to the login page
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # ---------------------------------------------------------
    # User Loader for Flask-Login
    # Tells Flask-Login how to reload user from session
    # ---------------------------------------------------------
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------------------------------------------------------
    # Register Blueprints
    # Each blueprint handles a section of the app
    # ---------------------------------------------------------
    from auth import auth_bp
    from game import game_bp
    from admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(admin_bp)

    # ---------------------------------------------------------
    # Register Main Route (Landing Page)
    # ---------------------------------------------------------
    from flask import render_template

    @app.route('/')
    def index():
        """Landing page — visible to all visitors."""
        return render_template('index.html')

    # ---------------------------------------------------------
    # Create All Database Tables
    # Runs only if tables don't already exist
    # ---------------------------------------------------------
    with app.app_context():
        db.create_all()
        seed_badges(app)

    return app


def seed_badges(app):
    """
    Seeds the default badges into the database if they don't exist.
    Called once on app startup.
    """
    from models import Badge

    default_badges = [
        {
            'name': 'Phishing Expert',
            'description': 'Completed all Phishing Awareness challenges',
            'criteria': 'Answer all 5 phishing questions',
            'icon': 'shield-check'
        },
        {
            'name': 'Password Pro',
            'description': 'Scored 100% on Password Security challenges',
            'criteria': 'Get all 5 password questions correct',
            'icon': 'lock-fill'
        },
        {
            'name': 'Safe Surfer',
            'description': 'Completed all Safe Browsing challenges',
            'criteria': 'Answer all 5 safe browsing questions',
            'icon': 'globe2'
        },
        {
            'name': 'CyberQuest Champion',
            'description': 'Completed all 15 challenges',
            'criteria': 'Answer all questions in all categories',
            'icon': 'trophy-fill'
        },
        {
            'name': 'Perfect Score',
            'description': 'Achieved 100% correct across all challenges',
            'criteria': 'Get every single question correct',
            'icon': 'star-fill'
        },
    ]

    for badge_data in default_badges:
        # Only insert if badge doesn't already exist
        existing = Badge.query.filter_by(name=badge_data['name']).first()
        if not existing:
            badge = Badge(**badge_data)
            db.session.add(badge)

    db.session.commit()


# ---------------------------------------------------------
# Run the App Directly
# ---------------------------------------------------------
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)