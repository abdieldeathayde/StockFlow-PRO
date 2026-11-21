import os
from flask import Flask
from sqlalchemy import inspect, text
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from config import Config

db=SQLAlchemy(); migrate=Migrate(); login=LoginManager(); csrf=CSRFProtect()
def create_app(config=Config):
    app=Flask(__name__); app.config.from_object(config)
    db.init_app(app); migrate.init_app(app,db); login.init_app(app); csrf.init_app(app)
    login.login_view='auth.login'; login.login_message='Faça login para acessar.'
    from app import models
    from app.routes import auth, main, products, movements, suppliers, purchases, reports, api
    for bp,prefix in [(auth.bp,None),(main.bp,None),(products.bp,'/products'),(movements.bp,'/movements'),(suppliers.bp,'/suppliers'),(purchases.bp,'/purchases'),(reports.bp,'/reports'),(api.bp,'/api')]: app.register_blueprint(bp,url_prefix=prefix)
    with app.app_context():
        uri=app.config['SQLALCHEMY_DATABASE_URI']
        if uri.startswith('sqlite:///'):
            db_file=uri.replace('sqlite:///','',1)
            os.makedirs(os.path.dirname(os.path.abspath(db_file)),exist_ok=True)
        db.create_all()
        ensure_product_import_columns()
        bootstrap()
    return app

def ensure_product_import_columns():
    inspector=inspect(db.engine)
    if not inspector.has_table('product'): return
    columns={column['name'] for column in inspector.get_columns('product')}
    additions={
        'location': "VARCHAR(120) NOT NULL DEFAULT ''",
        'ncm': "VARCHAR(20) NOT NULL DEFAULT ''",
    }
    with db.engine.begin() as connection:
        for name,definition in additions.items():
            if name not in columns:
                connection.execute(text(f'ALTER TABLE product ADD COLUMN {name} {definition}'))

def bootstrap():
    from app.models import Organization,User
    email=os.getenv('BOOTSTRAP_ADMIN_EMAIL','').strip().lower(); password=os.getenv('BOOTSTRAP_ADMIN_PASSWORD')
    if not email or not password or User.query.filter_by(email=email).first(): return
    org=Organization(name=os.getenv('BOOTSTRAP_ORG_NAME','Empresa Demo')); db.session.add(org); db.session.flush()
    user=User(organization_id=org.id,name=os.getenv('BOOTSTRAP_ADMIN_NAME','Administrador'),email=email,role='ADMIN'); user.set_password(password)
    db.session.add(user); db.session.commit()

@login.user_loader
def load_user(uid):
    from app.models import User
    return db.session.get(User,int(uid))
