"""
app.py — CyberQuest Flask Application Factory
ICT932 – Cybersecurity Testing and Assurance
Team Lead: Prashan Manandhar (CIHE241182)
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# ── Extension instances (imported by other modules) ──────────────────────────
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app():
    """Application factory — creates and configures the Flask app."""
    app = Flask(__name__)

    # ── Configuration ─────────────────────────────────────────────────────────
    app.config['SECRET_KEY'] = 'cyberquest-dev-secret-2026-ict932'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cyberquest.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_LOGIN_ATTEMPTS'] = 5          # brute-force threshold
    app.config['LOCKOUT_MINUTES'] = 15            # lockout window

    # ── Initialise extensions ─────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # ── Register blueprints ───────────────────────────────────────────────────
    from auth import auth_bp
    from game import game_bp
    from admin import admin_bp
    from security import security_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(security_bp)

    # ── Create tables and seed demo data ─────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_demo_accounts()
        _seed_challenges()
        _seed_badges()

    return app


# ── Seed helpers ──────────────────────────────────────────────────────────────

def _seed_demo_accounts():
    """Create demo student and teacher accounts if they don't exist."""
    from models import User

    if not User.query.filter_by(email='student@demo.com').first():
        student = User(
            username='student_demo',
            email='student@demo.com',
            password=bcrypt.generate_password_hash('Test1234!').decode('utf-8'),
            role='student'
        )
        db.session.add(student)

    if not User.query.filter_by(email='teacher@demo.com').first():
        teacher = User(
            username='teacher_demo',
            email='teacher@demo.com',
            password=bcrypt.generate_password_hash('Admin1234!').decode('utf-8'),
            role='teacher'
        )
        db.session.add(teacher)

    db.session.commit()


def _seed_challenges():
    """Seed 15 quiz challenges across three categories."""
    from models import Challenge

    if Challenge.query.count() > 0:
        return  # already seeded

    challenges = [
        # ── Phishing (5) ────────────────────────────────────────────────────
        Challenge(category='phishing', difficulty='easy',
                  question='You receive an email claiming your bank account is suspended and asking you to click a link immediately. What should you do?',
                  option_a='Click the link and enter your credentials',
                  option_b='Forward the email to all your contacts',
                  option_c='Go directly to your bank\'s official website instead',
                  option_d='Reply asking for more information',
                  correct_answer='C',
                  explanation='Always navigate to official websites directly. Phishing emails create urgency to trick you into clicking malicious links.'),

        Challenge(category='phishing', difficulty='medium',
                  question='An email from "paypa1.com" asks you to verify your PayPal account. What is the red flag?',
                  option_a='The email is too short',
                  option_b='The domain uses the number 1 instead of the letter l',
                  option_c='PayPal never sends emails',
                  option_d='The email is in English',
                  correct_answer='B',
                  explanation='Typosquatting replaces letters with similar-looking characters. "paypa1.com" vs "paypal.com" — always check the sender domain carefully.'),

        Challenge(category='phishing', difficulty='medium',
                  question='Which of the following is a common sign of a phishing email?',
                  option_a='Personalised greeting with your full name',
                  option_b='Generic greeting like "Dear Customer" with urgent language',
                  option_c='Email sent from a company you use',
                  option_d='Email with no attachments',
                  correct_answer='B',
                  explanation='Generic greetings combined with urgency ("Act now!") are hallmarks of phishing. Legitimate companies usually personalise their communications.'),

        Challenge(category='phishing', difficulty='hard',
                  question='What is spear phishing?',
                  option_a='A phishing attack targeting fish owners',
                  option_b='A mass phishing email sent to millions of people',
                  option_c='A highly targeted phishing attack customised for a specific individual',
                  option_d='A phishing attack using phone calls',
                  correct_answer='C',
                  explanation='Spear phishing targets specific individuals using personal details (name, job, contacts) to appear more convincing than generic phishing.'),

        Challenge(category='phishing', difficulty='hard',
                  question='A colleague\'s email account sends you a link saying "Check out this important document". The link URL starts with http:// not https://. What should you do?',
                  option_a='Click it — your colleague sent it so it must be safe',
                  option_b='Verify with your colleague through a different channel before clicking',
                  option_c='Download the document immediately',
                  option_d='Forward it to everyone to warn them',
                  correct_answer='B',
                  explanation='Compromised email accounts are used in spear phishing. Always verify unexpected links through a separate communication channel, and prefer https:// links.'),

        # ── Password Security (5) ────────────────────────────────────────────
        Challenge(category='password', difficulty='easy',
                  question='Which of the following is the strongest password?',
                  option_a='password123',
                  option_b='MyDog2024',
                  option_c='Tr0ub4dor&3!xKp',
                  option_d='123456789',
                  correct_answer='C',
                  explanation='Strong passwords use a mix of uppercase, lowercase, numbers, and symbols with no dictionary words. Length and randomness are key.'),

        Challenge(category='password', difficulty='easy',
                  question='What is a password manager?',
                  option_a='A person who manages passwords for your company',
                  option_b='A tool that securely stores and generates unique passwords for each account',
                  option_c='A sticky note where you write your passwords',
                  option_d='A feature that resets your password automatically every day',
                  correct_answer='B',
                  explanation='Password managers generate and store unique strong passwords for each site, so you only need to remember one master password.'),

        Challenge(category='password', difficulty='medium',
                  question='Why should you use a different password for every account?',
                  option_a='It\'s not necessary — reusing passwords is fine',
                  option_b='To prevent credential stuffing attacks if one site is breached',
                  option_c='Because websites require it',
                  option_d='To make it harder for you to remember',
                  correct_answer='B',
                  explanation='If you reuse passwords, a breach on one site gives attackers access to all your other accounts (credential stuffing).'),

        Challenge(category='password', difficulty='medium',
                  question='What is Multi-Factor Authentication (MFA)?',
                  option_a='Using multiple passwords for one account',
                  option_b='A second verification step beyond your password (e.g. a code sent to your phone)',
                  option_c='Having your password reviewed by multiple people',
                  option_d='A long password with multiple words',
                  correct_answer='B',
                  explanation='MFA adds a second factor (something you have or are) making it much harder for attackers to access your account even if they have your password.'),

        Challenge(category='password', difficulty='hard',
                  question='What is a brute-force attack?',
                  option_a='Physically breaking into a server room',
                  option_b='Guessing a password by systematically trying every possible combination',
                  option_c='Sending thousands of phishing emails',
                  option_d='Using social engineering to get someone to reveal their password',
                  correct_answer='B',
                  explanation='Brute-force attacks try all possible character combinations. Long, complex passwords make brute-force attacks computationally infeasible.'),

        # ── Safe Browsing (5) ────────────────────────────────────────────────
        Challenge(category='browsing', difficulty='easy',
                  question='What does the padlock icon in your browser\'s address bar indicate?',
                  option_a='The website is run by a trusted company',
                  option_b='Your connection to the website is encrypted (HTTPS)',
                  option_c='The website has no viruses',
                  option_d='You are anonymous online',
                  correct_answer='B',
                  explanation='The padlock means HTTPS is active and your connection is encrypted. It does NOT guarantee the website itself is safe or legitimate.'),

        Challenge(category='browsing', difficulty='easy',
                  question='You visit a website and a pop-up says "Your computer is infected! Call this number immediately." What should you do?',
                  option_a='Call the number straight away',
                  option_b='Close the browser tab — this is a tech support scam',
                  option_c='Enter your credit card number to pay for virus removal',
                  option_d='Download the software they recommend',
                  correct_answer='B',
                  explanation='This is a classic tech support scam. Legitimate security software never shows pop-ups asking you to call a phone number.'),

        Challenge(category='browsing', difficulty='medium',
                  question='What is a VPN and when is it most useful?',
                  option_a='A virus protection network — use it on every website',
                  option_b='A Virtual Private Network that encrypts your traffic — especially useful on public Wi-Fi',
                  option_c='A way to speed up your internet connection',
                  option_d='A tool to download files faster',
                  correct_answer='B',
                  explanation='VPNs encrypt your internet traffic, protecting you on unsecured public Wi-Fi networks where attackers could intercept your data.'),

        Challenge(category='browsing', difficulty='medium',
                  question='Which action best protects you when using public Wi-Fi?',
                  option_a='Only browse websites starting with http://',
                  option_b='Use a VPN and avoid accessing sensitive accounts',
                  option_c='Share the Wi-Fi password with others so they can verify it\'s safe',
                  option_d='Turn off your firewall to improve speed',
                  correct_answer='B',
                  explanation='Public Wi-Fi is unsecured. A VPN encrypts your traffic and you should avoid banking or sensitive logins until on a trusted network.'),

        Challenge(category='browsing', difficulty='hard',
                  question='What is a drive-by download attack?',
                  option_a='Downloading files from a USB drive',
                  option_b='Malware that automatically downloads when you visit a compromised website — without you clicking anything',
                  option_c='Downloading software while driving',
                  option_d='A legitimate way to update your browser',
                  correct_answer='B',
                  explanation='Drive-by downloads exploit browser or plugin vulnerabilities. Keeping your browser and plugins updated is the best defence.'),
    ]

    db.session.add_all(challenges)
    db.session.commit()


def _seed_badges():
    """Seed badge definitions."""
    from models import Badge

    if Badge.query.count() > 0:
        return

    badges = [
        Badge(name='Phishing Detector',
              description='Correctly answered 3 phishing challenges',
              icon='🎣', requirement=3),
        Badge(name='Password Pro',
              description='Correctly answered 3 password security challenges',
              icon='🔐', requirement=3),
        Badge(name='Safe Surfer',
              description='Correctly answered 3 safe browsing challenges',
              icon='🌐', requirement=3),
        Badge(name='CyberQuest Champion',
              description='Completed all 15 challenges',
              icon='🏆', requirement=15),
        Badge(name='Security Rookie',
              description='Answered your first challenge correctly',
              icon='⭐', requirement=1),
    ]

    db.session.add_all(badges)
    db.session.commit()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
