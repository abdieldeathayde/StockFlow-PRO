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
 yield a; tmp.cleanup()
@pytest.fixture
def client(app): return app.test_client()
def test_login_page(client): assert client.get('/login').status_code==200
def test_dashboard_requires_auth(client): assert client.get('/').status_code==302
def test_login_success(client): assert client.post('/login',data={'email':'admin@test','password':'senha-teste'},follow_redirects=True).status_code==200
