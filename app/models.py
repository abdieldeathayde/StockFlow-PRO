from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from app import db
class Organization(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(160),nullable=False); created_at=db.Column(db.DateTime,default=datetime.utcnow)
class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True); organization_id=db.Column(db.Integer,db.ForeignKey('organization.id'),index=True,nullable=False); name=db.Column(db.String(120),nullable=False); email=db.Column(db.String(190),unique=True,nullable=False); password_hash=db.Column(db.String(255),nullable=False); role=db.Column(db.String(20),default='VIEWER'); active=db.Column(db.Boolean,default=True); organization=db.relationship('Organization')
    def set_password(self,p): self.password_hash=generate_password_hash(p)
    def check_password(self,p): return check_password_hash(self.password_hash,p)
class Product(db.Model):
    id=db.Column(db.Integer,primary_key=True); organization_id=db.Column(db.Integer,db.ForeignKey('organization.id'),index=True,nullable=False); sku=db.Column(db.String(60),nullable=False); barcode=db.Column(db.String(80)); name=db.Column(db.String(160),nullable=False); location=db.Column(db.String(120),default='',server_default='',nullable=False); ncm=db.Column(db.String(20),default='',server_default='',nullable=False); description=db.Column(db.Text,default=''); category=db.Column(db.String(100),default=''); cost_price=db.Column(db.Numeric(12,2),default=0,nullable=False); sale_price=db.Column(db.Numeric(12,2),default=0,nullable=False); quantity=db.Column(db.Integer,default=0,nullable=False); minimum_quantity=db.Column(db.Integer,default=0,nullable=False); active=db.Column(db.Boolean,default=True); created_at=db.Column(db.DateTime,default=datetime.utcnow); updated_at=db.Column(db.DateTime,default=datetime.utcnow,onupdate=datetime.utcnow); __table_args__=(db.UniqueConstraint('organization_id','sku'),db.UniqueConstraint('organization_id','barcode'))
    @property
    def low_stock(self): return self.quantity<=self.minimum_quantity
    @property
    def stock_value(self): return self.quantity*self.cost_price
class Supplier(db.Model):
    id=db.Column(db.Integer,primary_key=True); organization_id=db.Column(db.Integer,db.ForeignKey('organization.id'),index=True,nullable=False); name=db.Column(db.String(160),nullable=False); document=db.Column(db.String(40),default=''); email=db.Column(db.String(190),default=''); phone=db.Column(db.String(40),default=''); notes=db.Column(db.Text,default=''); active=db.Column(db.Boolean,default=True)
class Movement(db.Model):
    id=db.Column(db.Integer,primary_key=True); organization_id=db.Column(db.Integer,db.ForeignKey('organization.id'),index=True,nullable=False); product_id=db.Column(db.Integer,db.ForeignKey('product.id'),nullable=False); user_id=db.Column(db.Integer,db.ForeignKey('user.id')); movement_type=db.Column(db.String(20),nullable=False); quantity=db.Column(db.Integer,nullable=False); balance_after=db.Column(db.Integer,nullable=False); reference=db.Column(db.String(100),default=''); note=db.Column(db.String(250),default=''); created_at=db.Column(db.DateTime,default=datetime.utcnow); product=db.relationship('Product'); user=db.relationship('User')
class Purchase(db.Model):
    id=db.Column(db.Integer,primary_key=True); organization_id=db.Column(db.Integer,db.ForeignKey('organization.id'),index=True,nullable=False); supplier_id=db.Column(db.Integer,db.ForeignKey('supplier.id'),nullable=False); created_by=db.Column(db.Integer,db.ForeignKey('user.id')); status=db.Column(db.String(20),default='DRAFT'); notes=db.Column(db.Text,default=''); created_at=db.Column(db.DateTime,default=datetime.utcnow); received_at=db.Column(db.DateTime); supplier=db.relationship('Supplier'); items=db.relationship('PurchaseItem',cascade='all,delete-orphan')
class PurchaseItem(db.Model):
    id=db.Column(db.Integer,primary_key=True); purchase_id=db.Column(db.Integer,db.ForeignKey('purchase.id'),nullable=False); product_id=db.Column(db.Integer,db.ForeignKey('product.id'),nullable=False); quantity=db.Column(db.Integer,nullable=False); unit_cost=db.Column(db.Numeric(12,2),nullable=False); product=db.relationship('Product')
class AuditLog(db.Model):
    id=db.Column(db.Integer,primary_key=True); organization_id=db.Column(db.Integer,db.ForeignKey('organization.id'),index=True,nullable=False); user_id=db.Column(db.Integer,db.ForeignKey('user.id')); action=db.Column(db.String(80)); entity=db.Column(db.String(80)); entity_id=db.Column(db.Integer); details=db.Column(db.Text,default=''); created_at=db.Column(db.DateTime,default=datetime.utcnow)
