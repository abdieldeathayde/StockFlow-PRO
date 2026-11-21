from flask import Blueprint,render_template,request,redirect,url_for,flash
from flask_login import login_required,current_user
from app.models import Supplier
from app.services import supplier_create
bp=Blueprint('suppliers',__name__)
@bp.get('/')
@login_required
def index(): return render_template('suppliers.html',suppliers=Supplier.query.filter_by(organization_id=current_user.organization_id,active=True).order_by(Supplier.name).all())
@bp.route('/new',methods=['GET','POST'])
@login_required
def new():
 if current_user.role=='VIEWER': return 'Forbidden',403
 if request.method=='POST':
  name=request.form.get('name','').strip()
  if not name: flash('Nome obrigatório.','danger')
  else: supplier_create(current_user.organization_id,dict(name=name,document=request.form.get('document',''),email=request.form.get('email',''),phone=request.form.get('phone',''),notes=request.form.get('notes','')),current_user.id); flash('Fornecedor cadastrado.','success'); return redirect(url_for('suppliers.index'))
 return render_template('supplier_form.html')
