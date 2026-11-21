from io import BytesIO

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from openpyxl import Workbook

from app.models import Product
from app import db
from app.product_import import ProductImportError, import_products_xlsx
from app.services import BusinessError, audit, product_save

bp=Blueprint('products',__name__)
def data():
 d=dict(sku=request.form.get('sku',''),barcode=request.form.get('barcode',''),name=request.form.get('name',''),location=request.form.get('location',''),ncm=request.form.get('ncm',''),description=request.form.get('description',''),category=request.form.get('category',''),cost_price=float(request.form.get('cost_price') or 0),sale_price=float(request.form.get('sale_price') or 0),quantity=int(request.form.get('quantity') or 0),minimum_quantity=int(request.form.get('minimum_quantity') or 0)); return d
@bp.get('/')
@login_required
def index():
 q=request.args.get('q','').strip(); query=Product.query.filter_by(organization_id=current_user.organization_id,active=True)
 if q: query=query.filter(Product.name.ilike(f'%{q}%')|Product.sku.ilike(f'%{q}%')|Product.barcode.ilike(f'%{q}%')|Product.location.ilike(f'%{q}%')|Product.ncm.ilike(f'%{q}%'))
 return render_template('products.html',products=query.order_by(Product.name).all(),q=q)

@bp.post('/import')
@login_required
def import_xlsx():
 if current_user.role=='VIEWER': return 'Forbidden',403
 upload=request.files.get('file')
 if not upload or not upload.filename:
  flash('Selecione um arquivo .xlsx para importar.','danger')
 elif not upload.filename.lower().endswith('.xlsx'):
  flash('O arquivo deve ter extensão .xlsx.','danger')
 else:
  try:
   imported,skipped_duplicates,skipped_incomplete,skipped_invalid=import_products_xlsx(current_user.organization_id,current_user.id,upload.stream)
  except ProductImportError as e:
   flash(str(e),'danger')
  else:
   flash(f'{imported} peça(s) importada(s); {skipped_duplicates} duplicada(s), {skipped_incomplete} incompleta(s) e {skipped_invalid} inválida(s) ignorada(s).','success')
 return redirect(url_for('products.index'))

@bp.get('/import/template')
@login_required
def import_template():
 workbook=Workbook()
 worksheet=workbook.active
 worksheet.title='Peças'
 worksheet.append(['Nome da Peça','Locação','Quantidade','Preço Unitário','NCM'])
 stream=BytesIO()
 workbook.save(stream)
 stream.seek(0)
 return send_file(
  stream,
  as_attachment=True,
  download_name='modelo_importacao_pecas.xlsx',
  mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
 )

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
