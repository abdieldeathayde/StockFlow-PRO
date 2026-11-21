import os,tempfile,pytest
from app import create_app,db
from app.models import Organization,User
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
