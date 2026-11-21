import os,tempfile,pytest
from decimal import Decimal
from io import BytesIO
from openpyxl import Workbook,load_workbook
from sqlalchemy import inspect,text
from app import create_app,db,ensure_product_import_columns
from app.models import Organization,Product,User
@pytest.fixture
def app():
 tmp=tempfile.TemporaryDirectory()
 class TestConfig:
  SECRET_KEY='test'; SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join(tmp.name,'test.db'); SQLALCHEMY_TRACK_MODIFICATIONS=False; TESTING=True; WTF_CSRF_ENABLED=False
 a=create_app(TestConfig)
 with a.app_context():
  o=Organization(name='Teste'); db.session.add(o); db.session.flush(); u=User(organization_id=o.id,name='Admin',email='admin@test',role='ADMIN'); u.set_password('senha-teste'); db.session.add(u); db.session.commit()
 yield a
 with a.app_context():
  db.session.remove()
  db.engine.dispose()
 tmp.cleanup()
@pytest.fixture
def client(app): return app.test_client()
def test_login_page(client): assert client.get('/login').status_code==200
def test_dashboard_requires_auth(client): assert client.get('/').status_code==302
def test_login_success(client): assert client.post('/login',data={'email':'admin@test','password':'senha-teste'},follow_redirects=True).status_code==200

def test_register_creates_admin_and_logs_in(client, app):
 response=client.post('/cadastro',data={
  'name':'Nova Pessoa','organization':'Nova Empresa','email':'NOVA@EXEMPLO.COM',
  'password':'senha-segura','password_confirmation':'senha-segura',
 },follow_redirects=True)
 assert response.status_code==200
 with app.app_context():
  user=User.query.filter_by(email='nova@exemplo.com').one()
  assert user.name=='Nova Pessoa'
  assert user.role=='ADMIN'
  assert user.organization.name=='Nova Empresa'
  assert user.check_password('senha-segura')

def test_register_rejects_mismatched_passwords(client, app):
 response=client.post('/cadastro',data={
  'name':'Nova Pessoa','organization':'Nova Empresa','email':'nova@exemplo.com',
  'password':'senha-segura','password_confirmation':'outra-senha',
 })
 assert response.status_code==200
 assert b'As senhas n\xc3\xa3o conferem.' in response.data
 with app.app_context():
  assert User.query.filter_by(email='nova@exemplo.com').first() is None

def test_register_rejects_duplicate_email(client, app):
 response=client.post('/cadastro',data={
  'name':'Outra Pessoa','organization':'Outra Empresa','email':'ADMIN@TEST',
  'password':'senha-segura','password_confirmation':'senha-segura',
 })
 assert response.status_code==200
 assert b'J\xc3\xa1 existe uma conta com este e-mail.' in response.data
 with app.app_context():
  assert Organization.query.count()==1

def make_product_workbook(rows):
 workbook=Workbook()
 worksheet=workbook.active
 worksheet.append(['Nome da Peça','Locação','Quantidade','Preço Unitário','NCM'])
 for row in rows:
  worksheet.append(row)
 stream=BytesIO()
 workbook.save(stream)
 stream.seek(0)
 return stream

def login_admin(client):
 return client.post('/login',data={'email':'admin@test','password':'senha-teste'})

def test_product_import_maps_fields_and_skips_duplicate_names(client, app):
 with app.app_context():
  organization=Organization.query.one()
  db.session.add(Product(
   organization_id=organization.id,sku='EXISTING',name='Peça já cadastrada',
   quantity=2,cost_price=Decimal('5.00'),sale_price=Decimal('0.00'),
  ))
  db.session.commit()
 login_admin(client)
 response=client.post('/products/import',data={
  'file':(make_product_workbook([
   ['Filtro de Óleo','A-01',5,'1.234,56',12345678],
   [' filtro de óleo ','A-02',99,10,'87654321'],
   ['Peça já cadastrada','B-01',7,20,'12345678'],
  ]),'pecas.xlsx'),
 },content_type='multipart/form-data',follow_redirects=True)
 assert response.status_code==200
 assert b'1 pe\xc3\xa7a(s) importada(s); 2 duplicada(s), 0 incompleta(s) e 0 inv\xc3\xa1lida(s) ignorada(s).' in response.data
 with app.app_context():
  product=Product.query.filter_by(name='Filtro de Óleo').one()
  assert product.sku.startswith('IMPORT-')
  assert product.location=='A-01'
  assert product.quantity==5
  assert product.cost_price==Decimal('1234.56')
  assert product.sale_price==Decimal('0.00')
  assert product.ncm=='12345678'
  assert Product.query.count()==2

def test_product_import_skips_invalid_numeric_row(client, app):
 login_admin(client)
 response=client.post('/products/import',data={
  'file':(make_product_workbook([
   ['Peça válida','A-01',5,10,'12345678'],
   ['Peça inválida','A-02','duas',20,'87654321'],
   ['Preço inválido','A-03',2,'sem preço','12345678'],
  ]),'pecas.xlsx'),
 },content_type='multipart/form-data',follow_redirects=True)
 assert response.status_code==200
 assert b'1 pe\xc3\xa7a(s) importada(s); 0 duplicada(s), 0 incompleta(s) e 2 inv\xc3\xa1lida(s) ignorada(s).' in response.data
 with app.app_context():
  assert Product.query.filter_by(name='Peça válida').count()==1
  assert Product.query.filter_by(name='Peça inválida').count()==0
  assert Product.query.filter_by(name='Preço inválido').count()==0

def test_product_import_skips_rows_missing_required_values(client, app):
 login_admin(client)
 response=client.post('/products/import',data={
  'file':(make_product_workbook([
   ['Peça válida','A-01',5,10,'12345678'],
   ['Sem preço','A-02',3,None,'87654321'],
   [None,'A-03',3,20,'12345678'],
  ]),'pecas.xlsx'),
 },content_type='multipart/form-data',follow_redirects=True)
 assert response.status_code==200
 assert b'1 pe\xc3\xa7a(s) importada(s); 0 duplicada(s), 2 incompleta(s) e 0 inv\xc3\xa1lida(s) ignorada(s).' in response.data
 with app.app_context():
  assert Product.query.count()==1

def test_product_import_template_has_expected_columns(client):
 login_admin(client)
 response=client.get('/products/import/template')
 assert response.status_code==200
 worksheet=load_workbook(BytesIO(response.data),read_only=True).active
 assert [cell.value for cell in next(worksheet.iter_rows())]==[
  'Nome da Peça','Locação','Quantidade','Preço Unitário','NCM',
 ]

def test_existing_product_table_gets_import_columns(app):
 with app.app_context():
  db.session.remove()
  with db.engine.begin() as connection:
   connection.execute(text('ALTER TABLE product DROP COLUMN location'))
   connection.execute(text('ALTER TABLE product DROP COLUMN ncm'))
  ensure_product_import_columns()
  columns={column['name'] for column in inspect(db.engine).get_columns('product')}
  assert {'location','ncm'}.issubset(columns)
