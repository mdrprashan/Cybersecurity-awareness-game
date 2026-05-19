from app import db
from models import Challenge

questions = [
    # Phishing Awareness
    ("Phishing Awareness", "easy", 10, "Which email is most suspicious?",
     "Email from your teacher", "Email asking you to verify password urgently", "Email from school portal", "Class timetable email", "b"),

    ("Phishing Awareness", "easy", 10, "What should you check before clicking a link?",
     "Colour of the email", "Sender address and URL", "Email length", "Font size", "b"),

    ("Phishing Awareness", "medium", 20, "What is social engineering?",
     "Hacking WiFi", "Tricking people into revealing information", "Installing antivirus", "Updating software", "b"),

    ("Phishing Awareness", "medium", 20, "A message says your account will close in 10 minutes. What should you do?",
     "Click quickly", "Ignore all emails", "Verify through official website", "Forward to friends", "c"),

    ("Phishing Awareness", "hard", 30, "Why are phishing emails dangerous?",
     "They only annoy users", "They can steal login details and personal data", "They improve security", "They block spam", "b"),

    # Password Security
    ("Password Security", "easy", 10, "Which is the strongest password?",
     "password123", "raju123", "Cyber@2024", "T9#xP!7qL@2z", "d"),

    ("Password Security", "easy", 10, "What does MFA mean?",
     "Multi-Factor Authentication", "Main File Access", "Mobile File App", "Manual Firewall Alert", "a"),

    ("Password Security", "medium", 20, "Why should passwords not be reused?",
     "It is hard to remember", "One stolen password can access many accounts", "It slows the computer", "It deletes files", "b"),

    ("Password Security", "medium", 20, "What is credential stuffing?",
     "Using stolen passwords on many websites", "Making strong passwords", "Encrypting files", "Scanning viruses", "a"),

    ("Password Security", "hard", 30, "Why is a password manager useful?",
     "It removes all passwords", "It stores and generates strong unique passwords", "It disables MFA", "It shares passwords online", "b"),

    # Safe Browsing
    ("Safe Browsing", "easy", 10, "What does HTTPS mean?",
     "A safer encrypted website connection", "A gaming website", "A slow website", "A fake link", "a"),

    ("Safe Browsing", "easy", 10, "What should you do when browser shows a security warning?",
     "Ignore it", "Proceed quickly", "Stop and check the website", "Download more files", "c"),

    ("Safe Browsing", "medium", 20, "Why is public WiFi risky?",
     "It is always slow", "Attackers may intercept data", "It uses too much battery", "It blocks websites", "b"),

    ("Safe Browsing", "medium", 20, "What is a malicious download?",
     "A file that may contain malware", "A school document", "A browser update", "A PDF only", "a"),

    ("Safe Browsing", "hard", 30, "Why should users avoid unknown browser extensions?",
     "They use colours", "They may track data or inject malicious code", "They make tabs bigger", "They improve WiFi", "b"),
]

from app import app

with app.app_context():
    for category, difficulty, points, question, a, b, c, d, correct in questions:
        existing = Challenge.query.filter_by(question=question).first()
        if not existing:
            challenge = Challenge(
                category=category,
                difficulty=difficulty,
                points=points,
                question=question,
                option_a=a,
                option_b=b,
                option_c=c,
                option_d=d,
                correct_answer=correct
            )
            db.session.add(challenge)

    db.session.commit()
    print("15 quiz questions added successfully.")