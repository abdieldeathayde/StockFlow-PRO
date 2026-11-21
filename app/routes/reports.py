from flask import Blueprint,render_template,Response
from flask_login import login_required,current_user
from app.models import Product,Movement
import csv,io
bp=Blueprint('reports',__name__)
@bp.get('/')
@login_required
def index():
 ps=Product.query.filter_by(organization_id=current_user.organization_id,active=True).order_by(Product.name).all(); ms=Movement.query.filter_by(organization_id=current_user.organization_id).order_by(Movement.created_at.desc()).limit(500).all(); return render_template('reports.html',products=ps,movements=ms)
@bp.get('/csv')
@login_required
def csv_export():
 ps=Product.query.filter_by(organization_id=current_user.organization_id,active=True).all(); out=io.StringIO(); w=csv.writer(out,delimiter=';'); w.writerow(['SKU','Barcode','Produto','Categoria','Quantidade','Mínimo','Custo','Venda','Valor estoque'])
 for p in ps: w.writerow([p.sku,p.barcode or '',p.name,p.category,p.quantity,p.minimum_quantity,p.cost_price,p.sale_price,p.stock_value])
 return Response('\ufeff'+out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=stockflow.csv'})
@bp.get('/xlsx')
@login_required
def xlsx_export():
 from openpyxl import Workbook
 import io
 ps=Product.query.filter_by(organization_id=current_user.organization_id,active=True).all(); wb=Workbook(); ws=wb.active; ws.title='Estoque'; ws.append(['SKU','Barcode','Produto','Categoria','Qtd','Mínimo','Custo','Venda','Valor estoque'])
 for p in ps: ws.append([p.sku,p.barcode,p.name,p.category,p.quantity,p.minimum_quantity,float(p.cost_price),float(p.sale_price),float(p.stock_value)])
 stream=io.BytesIO(); wb.save(stream); stream.seek(0); return Response(stream.getvalue(),mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':'attachment; filename=stockflow.xlsx'})
