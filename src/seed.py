from src.app import create_app
from src.models import db, Challenge

app = create_app()

with app.app_context():

    # Delete old data first
    Challenge.query.delete()

    # Question 1
    q1 = Challenge(
        category='Web Security',
        question='What does SQL stand for?',
        option_a='Structured Query Language',
        option_b='Simple Query Language',
        option_c='System Query Logic',
        option_d='Secure Question Login',
        correct_answer='A',
        difficulty='Easy',
        points=10
    )

    # Question 2
    q2 = Challenge(
        category='Networking',
        question='Which protocol is used for secure websites?',
        option_a='HTTP',
        option_b='FTP',
        option_c='SSH',
        option_d='HTTPS',
        correct_answer='D',
        difficulty='Easy',
        points=10
    )

    db.session.add(q1)
    db.session.add(q2)

    db.session.commit()

    print("Questions inserted successfully!")