from flask import Blueprint,render_template,request,redirect,url_for,flash
from flask_login import login_required,current_user
from app.models import Product
from app import db
from app.services import product_save,BusinessError,audit
bp=Blueprint('products',__name__)
def data():
 d=dict(sku=request.form.get('sku',''),barcode=request.form.get('barcode',''),name=request.form.get('name',''),description=request.form.get('description',''),category=request.form.get('category',''),cost_price=float(request.form.get('cost_price') or 0),sale_price=float(request.form.get('sale_price') or 0),quantity=int(request.form.get('quantity') or 0),minimum_quantity=int(request.form.get('minimum_quantity') or 0)); return d
@bp.get('/')
@login_required
def index():
 q=request.args.get('q','').strip(); query=Product.query.filter_by(organization_id=current_user.organization_id,active=True)
 if q: query=query.filter(Product.name.ilike(f'%{q}%')|Product.sku.ilike(f'%{q}%')|Product.barcode.ilike(f'%{q}%'))
 return render_template('products.html',products=query.order_by(Product.name).all(),q=q)
@bp.route('/new',methods=['GET','POST'])
@login_required
def new():
 if current_user.role=='VIEWER': return 'Forbidden',403
 if request.method=='POST':
  try: product_save(current_user.organization_id,data(),current_user.id); flash('Produto salvo.','success'); return redirect(url_for('products.index'))
  except (ValueError,BusinessError) as e: flash(str(e),'danger')
 return render_template('product_form.html',product=None)
@bp.route('/<int:pid>/edit',methods=['GET','POST'])
@login_required
def edit(pid):
 p=Product.query.filter_by(organization_id=current_user.organization_id,id=pid,active=True).first_or_404()
 if current_user.role=='VIEWER': return 'Forbidden',403
 if request.method=='POST':
  try: product_save(current_user.organization_id,data(),current_user.id,p); flash('Produto atualizado.','success'); return redirect(url_for('products.index'))
  except (ValueError,BusinessError) as e: flash(str(e),'danger')
 return render_template('product_form.html',product=p)
@bp.post('/<int:pid>/deactivate')
@login_required
def deactivate(pid):
 if current_user.role!='ADMIN': return 'Forbidden',403
 p=Product.query.filter_by(organization_id=current_user.organization_id,id=pid).first_or_404(); p.active=False; audit(current_user.organization_id,current_user.id,'DEACTIVATE','Product',p.id); db.session.commit(); flash('Produto desativado.','success'); return redirect(url_for('products.index'))
