from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Organization, User

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard_page'))

    if request.method == 'POST':
        user = User.query.filter_by(
            email=request.form.get('email', '').strip().lower(),
            active=True,
        ).first()
        if user and user.check_password(request.form.get('password', '')):
            login_user(user)
            return redirect(url_for('main.dashboard_page'))
        flash('Credenciais inválidas.', 'danger')

    return render_template('login.html')


@bp.route('/cadastro', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard_page'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        organization_name = request.form.get('organization', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirmation = request.form.get('password_confirmation', '')

        if not name or not organization_name or not email or not password:
            flash('Preencha todos os campos.', 'danger')
        elif len(name) > 120 or len(organization_name) > 160 or len(email) > 190:
            flash('Revise o tamanho dos campos informados.', 'danger')
        elif len(password) < 8:
            flash('A senha deve ter pelo menos 8 caracteres.', 'danger')
        elif password != password_confirmation:
            flash('As senhas não conferem.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Já existe uma conta com este e-mail.', 'danger')
        else:
            organization = Organization(name=organization_name)
            user = User(
                organization=organization,
                name=name,
                email=email,
                role='ADMIN',
            )
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError as error:
                db.session.rollback()
                message = str(error.orig).lower()
                if 'user.email' in message or 'user_email_key' in message:
                    flash('Já existe uma conta com este e-mail.', 'danger')
                else:
                    raise
            else:
                login_user(user)
                return redirect(url_for('main.dashboard_page'))

    return render_template('register.html')


@bp.get('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
