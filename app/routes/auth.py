from flask import Blueprint,render_template,request,redirect,url_for,flash
from flask_login import login_user,logout_user,current_user
from app.models import User
bp=Blueprint('auth',__name__)
@bp.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('main.dashboard'))
    if request.method=='POST':
        u=User.query.filter_by(email=request.form.get('email','').strip().lower(),active=True).first()
        if u and u.check_password(request.form.get('password','')): login_user(u); return redirect(url_for('main.dashboard'))
        flash('Credenciais inválidas.','danger')
    return render_template('login.html')
@bp.get('/logout')
def logout(): logout_user(); return redirect(url_for('auth.login'))
