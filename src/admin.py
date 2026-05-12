# =============================================================
# admin.py — Admin Dashboard Blueprint
# Author: Pramesh Silwal (CIHE241339)
# Week 7: Placeholder routes added so redirects work
# Full implementation coming in Week 8-9
# =============================================================

from flask import Blueprint, render_template
from flask_login import login_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/dashboard')
@login_required
def dashboard():
    """Teacher dashboard — full implementation by Pramesh (Week 8)."""
    return render_template('coming_soon.html',
                           title='Teacher Dashboard',
                           message='Admin dashboard coming soon — Pramesh is working on it!')