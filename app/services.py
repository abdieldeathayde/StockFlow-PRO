from datetime import datetime
from sqlalchemy import func
from app import db
from app.models import Product,Movement,AuditLog,Supplier,Purchase,PurchaseItem
class BusinessError(Exception): pass
def audit(org,user,action,entity,eid=None,details=''):
    db.session.add(AuditLog(organization_id=org,user_id=user,action=action,entity=entity,entity_id=eid,details=details))
def scoped_products(org): return Product.query.filter_by(organization_id=org,active=True)
def product_save(org,data,user,product=None):
    sku=data['sku'].strip().upper(); barcode=data.get('barcode','').strip() or None
    q=Product.query.filter_by(organization_id=org,sku=sku)
    if product: q=q.filter(Product.id!=product.id)
    if q.first(): raise BusinessError('SKU já cadastrado nesta empresa.')
    q=Product.query.filter_by(organization_id=org,barcode=barcode) if barcode else None
    if q and product: q=q.filter(Product.id!=product.id)
    if q and q.first(): raise BusinessError('Código de barras já cadastrado.')
    if any(data[k]<0 for k in ('cost_price','sale_price','quantity','minimum_quantity')): raise BusinessError('Valores e quantidades não podem ser negativos.')
    if not data['name'].strip() or not sku: raise BusinessError('SKU e nome são obrigatórios.')
    if not product:
        product=Product(organization_id=org,sku=sku,barcode=barcode,name=data['name'].strip(),description=data.get('description',''),category=data.get('category',''),cost_price=data['cost_price'],sale_price=data['sale_price'],quantity=data['quantity'],minimum_quantity=data['minimum_quantity'])
        db.session.add(product); db.session.flush(); audit(org,user,'CREATE','Product',product.id,sku)
    else:
        product.sku=sku; product.barcode=barcode; product.name=data['name'].strip(); product.description=data.get('description',''); product.category=data.get('category',''); product.cost_price=data['cost_price']; product.sale_price=data['sale_price']; product.minimum_quantity=data['minimum_quantity']; audit(org,user,'UPDATE','Product',product.id,sku)
    db.session.commit(); return product
def move(org,pid,kind,qty,note,user,reference=''):
    p=Product.query.filter_by(organization_id=org,id=pid,active=True).first()
    if not p: raise BusinessError('Produto não encontrado.')
    if kind not in ('IN','OUT') or qty<=0: raise BusinessError('Tipo ou quantidade inválida.')
    if kind=='OUT' and qty>p.quantity: raise BusinessError('Estoque insuficiente.')
    p.quantity=p.quantity+qty if kind=='IN' else p.quantity-qty
    db.session.add(Movement(organization_id=org,product_id=p.id,user_id=user,movement_type=kind,quantity=qty,balance_after=p.quantity,note=note,reference=reference)); audit(org,user,kind,'Product',p.id,f'{qty} unidades; saldo {p.quantity}'); db.session.commit(); return p
def adjust(org,pid,balance,note,user):
    p=Product.query.filter_by(organization_id=org,id=pid,active=True).first()
    if not p: raise BusinessError('Produto não encontrado.')
    if balance<0: raise BusinessError('Saldo não pode ser negativo.')
    delta=balance-p.quantity; p.quantity=balance
    db.session.add(Movement(organization_id=org,product_id=p.id,user_id=user,movement_type='ADJUSTMENT',quantity=delta,balance_after=balance,note=note)); audit(org,user,'ADJUST','Product',p.id,f'delta {delta}'); db.session.commit(); return p
def supplier_create(org,data,user):
    s=Supplier(organization_id=org,**data); db.session.add(s); db.session.flush(); audit(org,user,'CREATE','Supplier',s.id,s.name); db.session.commit(); return s
def purchase_create(org,sid,pid,qty,cost,note,user):
    s=Supplier.query.filter_by(organization_id=org,id=sid,active=True).first(); p=Product.query.filter_by(organization_id=org,id=pid,active=True).first()
    if not s or not p: raise BusinessError('Fornecedor ou produto inválido.')
    if qty<=0 or cost<0: raise BusinessError('Quantidade/custo inválidos.')
    po=Purchase(organization_id=org,supplier_id=sid,created_by=user,notes=note); db.session.add(po); db.session.flush(); db.session.add(PurchaseItem(purchase_id=po.id,product_id=pid,quantity=qty,unit_cost=cost)); audit(org,user,'CREATE','Purchase',po.id); db.session.commit(); return po
def purchase_receive(org,pid,user):
    po=Purchase.query.filter_by(organization_id=org,id=pid).first()
    if not po: raise BusinessError('Pedido não encontrado.')
    if po.status!='DRAFT': raise BusinessError('Pedido já recebido.')
    for i in po.items:
        p=Product.query.filter_by(organization_id=org,id=i.product_id).first()
        if not p: raise BusinessError('Produto relacionado não encontrado.')
        p.quantity+=i.quantity; p.cost_price=i.unit_cost
        db.session.add(Movement(organization_id=org,product_id=p.id,user_id=user,movement_type='IN',quantity=i.quantity,balance_after=p.quantity,reference=f'Compra #{po.id}',note=f'Recebimento: {po.supplier.name}'))
    po.status='RECEIVED'; po.received_at=datetime.utcnow(); audit(org,user,'RECEIVE','Purchase',po.id); db.session.commit(); return po
def dashboard(org):
    q=scoped_products(org)
    return dict(count=q.count(),units=db.session.query(func.coalesce(func.sum(Product.quantity),0)).filter_by(organization_id=org,active=True).scalar(),low=q.filter(Product.quantity<=Product.minimum_quantity).order_by(Product.quantity).all(),value=db.session.query(func.coalesce(func.sum(Product.quantity*Product.cost_price),0)).filter_by(organization_id=org,active=True).scalar(),recent=Movement.query.filter_by(organization_id=org).order_by(Movement.created_at.desc()).limit(10).all())
