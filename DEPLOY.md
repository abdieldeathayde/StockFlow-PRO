# Deploy (orientação)
## PythonAnywhere
Confirme os limites e disponibilidade do plano para web app, banco e persistência. Faça clone do repositório, crie virtualenv, instale requirements e configure WSGI com `from app import create_app; application=create_app()`. Configure SECRET_KEY e DATABASE_URL. Se não houver PostgreSQL no plano, considere a demo SQLite e backups; não é ideal para multiusuário concorrente. HTTPS deve ser habilitado; então COOKIE_SECURE=1.
## AWS
Docker + EC2/ECS, PostgreSQL gerenciado ou com volume persistente, HTTPS, backups e logs. Verifique preço e elegibilidade de free tier antes de criar recursos.
