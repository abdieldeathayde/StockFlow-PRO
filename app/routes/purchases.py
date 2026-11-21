from flask import Blueprint,render_template,request,redirect,url_for,flash
from flask_login import login_required,current_user
from app.models import Purchase,Supplier,Product
from app.services import purchase_create,purchase_receive,BusinessError
bp=Blueprint('purchases',__name__)
@bp.get('/')
@login_required
def index(): return render_template('purchases.html',purchases=Purchase.query.filter_by(organization_id=current_user.organization_id).order_by(Purchase.created_at.desc()).all())
@bp.route('/new',methods=['GET','POST'])
@login_required
def new():
 ss=Supplier.query.filter_by(organization_id=current_user.organization_id,active=True).all(); ps=Product.query.filter_by(organization_id=current_user.organization_id,active=True).all()
 if current_user.role=='VIEWER': return 'Forbidden',403
 if request.method=='POST':
  try: purchase_create(current_user.organization_id,int(request.form['supplier_id']),int(request.form['product_id']),int(request.form['quantity']),float(request.form['cost']),request.form.get('notes',''),current_user.id); flash('Pedido criado.','success'); return redirect(url_for('purchases.index'))
  except (ValueError,BusinessError) as e: flash(str(e),'danger')
 return render_template('purchase_form.html',suppliers=ss,products=ps)
@bp.post('/<int:poid>/receive')
@login_required
def receive(poid):
 if current_user.role=='VIEWER': return 'Forbidden',403
 try: purchase_receive(current_user.organization_id,poid,current_user.id); flash('Compra recebida; estoque atualizado.','success')
 except BusinessError as e: flash(str(e),'danger')
 return redirect(url_for('purchases.index'))
