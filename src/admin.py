from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, User, Challenge, Score

admin_bp = Blueprint('admin', __name__)


# Teacher Dashboard
@admin_bp.route('/admin/dashboard')
@login_required
def dashboard():

    total_students = User.query.filter_by(role='student').count()

    total_answers = Score.query.count()

    scores = Score.query.all()

    average_score = 0

    if total_answers > 0:
        correct_answers = Score.query.filter_by(is_correct=True).count()
        average_score = round((correct_answers / total_answers) * 100, 2)

    students = User.query.filter_by(role='student').all()

    return render_template(
        'admin_dashboard.html',
        total_students=total_students,
        total_answers=total_answers,
        average_score=average_score,
        students=students
    )


# View all questions
@admin_bp.route('/admin/questions')
@login_required
def questions():

    questions = Challenge.query.all()

    return render_template(
        'manage_questions.html',
        questions=questions
    )


# Add question
@admin_bp.route('/admin/questions/add', methods=['GET', 'POST'])
@login_required
def add_question():

    if request.method == 'POST':

        new_question = Challenge(
            category=request.form['category'],
            question=request.form['question'],
            option_a=request.form['option_a'],
            option_b=request.form['option_b'],
            option_c=request.form['option_c'],
            option_d=request.form['option_d'],
            correct_answer=request.form['correct_answer'],
            difficulty=request.form['difficulty'],
            points=request.form['points']
        )

        db.session.add(new_question)
        db.session.commit()

        flash('Question added successfully!', 'success')

        return redirect(url_for('admin.questions'))

    return render_template('add_question.html')
    # Edit question
@admin_bp.route('/admin/questions/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_question(id):

    question = Challenge.query.get_or_404(id)

    if request.method == 'POST':

        question.category = request.form['category']
        question.question = request.form['question']
        question.option_a = request.form['option_a']
        question.option_b = request.form['option_b']
        question.option_c = request.form['option_c']
        question.option_d = request.form['option_d']
        question.correct_answer = request.form['correct_answer']
        question.difficulty = request.form['difficulty']
        question.points = request.form['points']

        db.session.commit()

        flash('Question updated successfully!', 'success')

        return redirect(url_for('admin.questions'))

    return render_template('edit_question.html', question=question)


# Delete question
@admin_bp.route('/admin/questions/delete/<int:id>', methods=['POST'])
@login_required
def delete_question(id):

    question = Challenge.query.get_or_404(id)

    db.session.delete(question)
    db.session.commit()

    flash('Question deleted successfully!', 'success')

    return redirect(url_for('admin.questions'))