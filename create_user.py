from app import create_app, db
from app.models import User, Organization
from getpass import getpass

app = create_app()

with app.app_context():
    print("\n=== StockFlow Pro | Criar usuário ===\n")

    organizations = Organization.query.all()

    if not organizations:
        print("Nenhuma empresa cadastrada.")
        exit()

    print("Empresas cadastradas:\n")

    for organization in organizations:
        print(f"{organization.id} - {organization.name}")

    organization_id = int(input("\nID da empresa: "))

    organization = db.session.get(Organization, organization_id)

    if not organization:
        print("Empresa não encontrada.")
        exit()

    name = input("Nome completo: ").strip()
    email = input("E-mail: ").strip().lower()

    print("\nPerfis disponíveis:")
    print("ADMIN - Administrador")
    print("OPERATOR - Operador")
    print("VIEWER - Somente consulta")

    role = input("Perfil: ").strip().upper()

    if role not in ["ADMIN", "OPERATOR", "VIEWER"]:
        print("Perfil inválido.")
        exit()

    if User.query.filter_by(email=email).first():
        print("Este e-mail já está cadastrado.")
        exit()

    password = getpass("Senha: ")
    confirm_password = getpass("Confirmar senha: ")

    if password != confirm_password:
        print("As senhas não coincidem.")
        exit()

    if len(password) < 8:
        print("A senha deve possuir pelo menos 8 caracteres.")
        exit()

    user = User(
        name=name,
        email=email,
        role=role,
        organization_id=organization.id
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    print("\nUsuário criado com sucesso!")
    print(f"Nome: {user.name}")
    print(f"E-mail: {user.email}")
    print(f"Empresa: {organization.name}")
    print(f"Perfil: {user.role}")