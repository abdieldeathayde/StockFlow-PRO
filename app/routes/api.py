from flask import Blueprint,jsonify,request
from flask_login import login_required,current_user
from app.models import Product
from app.services import move,BusinessError
bp=Blueprint('api',__name__)
@bp.get('/products')
@login_required
def products():
 ps=Product.query.filter_by(organization_id=current_user.organization_id,active=True).all(); return jsonify([dict(id=p.id,sku=p.sku,barcode=p.barcode,name=p.name,quantity=p.quantity,minimum=p.minimum_quantity,low_stock=p.low_stock) for p in ps])
@bp.post('/movements')
@login_required
def movement():
 if current_user.role=='VIEWER': return jsonify(error='Forbidden'),403
 d=request.get_json(silent=True) or {}
 try: p=move(current_user.organization_id,int(d['product_id']),d['type'],int(d['quantity']),d.get('note',''),current_user.id); return jsonify(ok=True,balance=p.quantity),201
 except (ValueError,KeyError,BusinessError) as e: return jsonify(ok=False,error=str(e)),400
