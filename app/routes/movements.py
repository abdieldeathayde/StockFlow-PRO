from flask import Blueprint,render_template,request,redirect,url_for,flash
from flask_login import login_required,current_user
from app.models import Product,Movement
from app.services import move,adjust,BusinessError
bp=Blueprint('movements',__name__)
@bp.route('/',methods=['GET','POST'])
@login_required
def index():
 if current_user.role=='VIEWER' and request.method=='POST': return 'Forbidden',403
 if request.method=='POST':
  try: move(current_user.organization_id,int(request.form['product_id']),request.form['kind'],int(request.form['quantity']),request.form.get('note',''),current_user.id); flash('Movimento registrado.','success'); return redirect(url_for('movements.index'))
  except (ValueError,BusinessError) as e: flash(str(e),'danger')
 ps=Product.query.filter_by(organization_id=current_user.organization_id,active=True).order_by(Product.name).all(); ms=Movement.query.filter_by(organization_id=current_user.organization_id).order_by(Movement.created_at.desc()).limit(250).all(); return render_template('movements.html',products=ps,movements=ms)
@bp.post('/adjust')
@login_required
def adjustment():
 if current_user.role!='ADMIN': return 'Forbidden',403
 try: adjust(current_user.organization_id,int(request.form['product_id']),int(request.form['balance']),request.form.get('note',''),current_user.id); flash('Ajuste realizado.','success')
 except (ValueError,BusinessError) as e: flash(str(e),'danger')
 return redirect(url_for('movements.index'))
