# StockFlow Pro
MVP comercial de estoque: Flask, SQLAlchemy, SQLite/PostgreSQL, login, isolamento multiempresa, perfis, produtos/SKU/barcode, movimentações, fornecedores, pedidos/recebimento, relatórios CSV/Excel, API autenticada por sessão, CSRF, Docker.

## Local
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate | Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```
PowerShell bootstrap:
```powershell
$env:BOOTSTRAP_ADMIN_EMAIL='admin@empresa.com'
$env:BOOTSTRAP_ADMIN_PASSWORD='Senha-forte-para-trocar'
$env:BOOTSTRAP_ORG_NAME='Minha Empresa'
python app.py
```
Acesse http://127.0.0.1:5000. Configure SECRET_KEY forte e não use credenciais de exemplo em produção.

## Docker
Configure variáveis de bootstrap/SECRET_KEY e rode `docker compose up --build`; abra localhost:5000. O Compose utiliza PostgreSQL persistido em volume.

## Testes
`pytest -q`

## Deploy
Use Gunicorn (`gunicorn app:app`). PythonAnywhere: confira plano atual, suporte ao banco e limites; SQLite é demo/uso pequeno, PostgreSQL recomendado para multiusuário. AWS: container em EC2/ECS com banco persistente (RDS ou PostgreSQL em volume), HTTPS, backups, logs e monitoramento; custos/free tier variam. Leia DEPLOY.md.

## Limitações que ainda precisam ser resolvidas antes de produção
- Bootstrap cria um usuário admin/organização por variáveis de ambiente; não existe onboarding seguro nem gestão de usuários na UI.
- Compras têm um item por pedido no MVP; falta cancelamento, devolução, recebimento parcial e aprovação.
- API usa sessão web; não é API externa com token.
- Não há rate limit, MFA, recuperação de senha, alertas por e-mail, billing, nem política completa de backup.
- Testes de regras e isolamento multiempresa precisam ser ampliados; revise o código e faça teste de segurança antes de uso com dados reais.
- `db.create_all()` é usado para facilitar a primeira execução; configure migrations como parte do deploy.
