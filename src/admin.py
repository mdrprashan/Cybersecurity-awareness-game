"""
admin.py — Admin/Teacher Dashboard Blueprint
ICT932 – Cybersecurity Testing and Assurance
Author: Pramesh Silwal (CIHE241339)
Extended: Prashan Manandhar (CIHE241182)

Security fixes applied:
  - reset_password: full strength validation, not just length check
  - All queries use db.session.get() instead of deprecated Model.query.get()
"""

import secrets
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db, bcrypt
from models import User, Challenge, Score, Badge, UserBadge, LoginAttempt
from security import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def _validate_password_strength(password: str) -> list:
    """Shared password strength checker — same rules as registration."""
    errors = []
    if len(password) < 8:
        errors.append('Password must be at least 8 characters.')
    if not any(c.isupper() for c in password):
        errors.append('Password must contain at least one uppercase letter.')
    if not any(c.islower() for c in password):
        errors.append('Password must contain at least one lowercase letter.')
    if not any(c.isdigit() for c in password):
        errors.append('Password must contain at least one number.')
    if not any(c in '!@#$%^&*()_+-=[]{};\':\"\\|,.<>/?`~' for c in password):
        errors.append('Password must contain at least one special character.')
    return errors


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@login_required
@role_required('teacher')
def dashboard():
    students = User.query.filter_by(role='student').all()
    teachers = User.query.filter_by(role='teacher').all()

    def _build_data(users):
        data = []
        for u in users:
            scores      = Score.query.filter_by(user_id=u.id).all()
            total_score = sum(s.points for s in scores)
            correct     = sum(1 for s in scores if s.is_correct)
            answered    = len(scores)
            total_q     = Challenge.query.count()
            percentage  = round((correct / total_q) * 100, 1) if total_q > 0 else 0
            badge_count = UserBadge.query.filter_by(user_id=u.id).count()
            data.append({
                'user': u, 'total_score': total_score,
                'correct': correct, 'answered': answered,
                'percentage': percentage, 'badges': badge_count,
            })
        data.sort(key=lambda x: x['total_score'], reverse=True)
        return data

    student_data     = _build_data(students)
    teacher_data     = _build_data(teachers)
    total_challenges = Challenge.query.count()

    return render_template('admin_dashboard.html',
                           student_data=student_data,
                           teacher_data=teacher_data,
                           total_students=len(students),
                           total_challenges=total_challenges,
                           total_teachers=len(teachers))


# ── Student Detail ────────────────────────────────────────────────────────────

@admin_bp.route('/student/<int:user_id>')
@login_required
@role_required('teacher')
def student_detail(user_id):
    # SECURITY FIX: use db.session.get() instead of deprecated get_or_404 with query.get()
    student = db.session.get(User, user_id)
    if not student:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.dashboard'))

    scores   = Score.query.filter_by(user_id=student.id).all()
    badges   = UserBadge.query.filter_by(user_id=student.id).all()
    attempts = LoginAttempt.query.filter_by(user_id=student.id)\
                                 .order_by(LoginAttempt.attempted_at.desc())\
                                 .limit(20).all()
    total_score = sum(s.points for s in scores)
    correct     = sum(1 for s in scores if s.is_correct)
    total_q     = Challenge.query.count()
    percentage  = round((correct / total_q) * 100, 1) if total_q > 0 else 0

    return render_template('admin_student_detail.html',
                           student=student, scores=scores,
                           badges=badges, attempts=attempts,
                           total_score=total_score, correct=correct,
                           percentage=percentage, total_q=total_q)


# ── Add User ──────────────────────────────────────────────────────────────────

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def add_user():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        role     = request.form.get('role', 'student')
        password = request.form.get('password', '').strip()

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('admin_add_user.html')

        # SECURITY FIX: validate password strength for new users
        pw_errors = _validate_password_strength(password)
        if pw_errors:
            for err in pw_errors:
                flash(err, 'danger')
            return render_template('admin_add_user.html')

        if User.query.filter_by(email=email).first():
            flash('Email already in use.', 'danger')
            return render_template('admin_add_user.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('admin_add_user.html')

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash(f'User {username} ({role}) created. '
              f'They will be prompted to set up 2FA on first login.', 'success')
        return redirect(url_for('admin.dashboard'))

    temp_pw = secrets.token_urlsafe(10) + 'A1!'
    return render_template('admin_add_user.html', temp_pw=temp_pw)


# ── Delete User ───────────────────────────────────────────────────────────────

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('teacher')
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.dashboard'))

    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.dashboard'))

    username = user.username
    Score.query.filter_by(user_id=user_id).delete()
    UserBadge.query.filter_by(user_id=user_id).delete()
    LoginAttempt.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()

    flash(f'User {username} has been deleted.', 'success')
    return redirect(url_for('admin.dashboard'))


# ── Reset Password ────────────────────────────────────────────────────────────

@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@role_required('teacher')
def reset_password(user_id):
    user   = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.dashboard'))

    new_pw = request.form.get('new_password', '').strip()

    # SECURITY FIX: full strength validation, not just length
    pw_errors = _validate_password_strength(new_pw)
    if pw_errors:
        for err in pw_errors:
            flash(err, 'danger')
        return redirect(url_for('admin.dashboard'))

    user.password = bcrypt.generate_password_hash(new_pw).decode('utf-8')
    db.session.commit()
    flash(f'Password reset for {user.username}.', 'success')
    return redirect(url_for('admin.dashboard'))


# ── Reset 2FA ─────────────────────────────────────────────────────────────────

@admin_bp.route('/users/<int:user_id>/reset-2fa', methods=['POST'])
@login_required
@role_required('teacher')
def reset_2fa(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.dashboard'))

    user.is_2fa_enabled = False
    user.totp_secret    = None
    db.session.commit()

    if user.id == current_user.id:
        flash('Your 2FA has been reset. You will be prompted to set it up again on next login.', 'warning')
    else:
        flash(f'2FA reset for {user.username}. They will be prompted to set it up on next login.', 'success')
    return redirect(url_for('admin.dashboard'))


# ── Challenge Management ──────────────────────────────────────────────────────

@admin_bp.route('/challenges')
@login_required
@role_required('teacher')
def manage_challenges():
    challenges = Challenge.query.order_by(
        Challenge.category, Challenge.difficulty).all()
    return render_template('admin_challenges.html', challenges=challenges)


@admin_bp.route('/challenges/add', methods=['GET', 'POST'])
@login_required
@role_required('teacher')
def add_challenge():
    valid_categories = {'phishing', 'password', 'browsing'}
    valid_answers    = {'A', 'B', 'C', 'D'}
    valid_difficulty = {'easy', 'medium', 'hard'}

    if request.method == 'POST':
        category       = request.form.get('category', '')
        correct_answer = request.form.get('correct_answer', '').upper()
        difficulty     = request.form.get('difficulty', 'medium')

        # SECURITY FIX: validate enum-like fields server-side
        if category not in valid_categories:
            flash('Invalid category.', 'danger')
            return render_template('admin_add_challenge.html')
        if correct_answer not in valid_answers:
            flash('Correct answer must be A, B, C or D.', 'danger')
            return render_template('admin_add_challenge.html')
        if difficulty not in valid_difficulty:
            flash('Invalid difficulty.', 'danger')
            return render_template('admin_add_challenge.html')

        challenge = Challenge(
            category       = category,
            question       = request.form.get('question', '').strip(),
            option_a       = request.form.get('option_a', '').strip(),
            option_b       = request.form.get('option_b', '').strip(),
            option_c       = request.form.get('option_c', '').strip(),
            option_d       = request.form.get('option_d', '').strip(),
            correct_answer = correct_answer,
            explanation    = request.form.get('explanation', '').strip(),
            difficulty     = difficulty,
        )
        if not all([challenge.question, challenge.option_a,
                    challenge.option_b, challenge.option_c,
                    challenge.option_d, challenge.correct_answer]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('admin_add_challenge.html')

        db.session.add(challenge)
        db.session.commit()
        flash('Challenge added successfully!', 'success')
        return redirect(url_for('admin.manage_challenges'))

    return render_template('admin_add_challenge.html')


@admin_bp.route('/challenges/<int:challenge_id>/delete', methods=['POST'])
@login_required
@role_required('teacher')
def delete_challenge(challenge_id):
    challenge = db.session.get(Challenge, challenge_id)
    if not challenge:
        flash('Challenge not found.', 'danger')
        return redirect(url_for('admin.manage_challenges'))

    Score.query.filter_by(challenge_id=challenge_id).delete()
    db.session.delete(challenge)
    db.session.commit()
    flash('Challenge deleted.', 'success')
    return redirect(url_for('admin.manage_challenges'))
