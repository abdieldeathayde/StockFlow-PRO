from flask import Blueprint,render_template
from flask_login import login_required,current_user
from app.services import dashboard
bp=Blueprint('main',__name__)
@bp.get('/')
@login_required
def dashboard_page(): return render_template('dashboard.html',data=dashboard(current_user.organization_id))
