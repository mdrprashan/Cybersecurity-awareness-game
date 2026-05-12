# =============================================================
# game.py — Game Module Blueprint
# Author: Raju Kshetri (CIHE240711)
# Week 7: Placeholder routes added so redirects work
# Full implementation coming in Week 8-9
# =============================================================

from flask import Blueprint, render_template
from flask_login import login_required

game_bp = Blueprint('game', __name__)


@game_bp.route('/challenges')
@login_required
def challenges():
    """Challenge categories page — full implementation by Raju (Week 8)."""
    return render_template('coming_soon.html',
                           title='Challenges',
                           message='Game module coming soon — Raju is working on it!')


@game_bp.route('/progress')
@login_required
def progress():
    """Student progress page — full implementation by Raju (Week 9)."""
    return render_template('coming_soon.html',
                           title='My Progress',
                           message='Progress tracking coming soon!')