from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

from database import SessionLocal
from models import Usuario, Familia


def registrar_usuario(nome: str, email: str, senha: str, nome_familia: str) -> tuple:
    session = SessionLocal()
    try:
        familia = session.query(Familia).filter_by(nome=nome_familia.strip()).first()
        is_admin = False

        if not familia:
            familia = Familia(nome=nome_familia.strip())
            session.add(familia)
            session.flush()
            is_admin = True

        existing = session.query(Usuario).filter_by(email=email.strip().lower()).first()
        if existing:
            return None, "Este email já está cadastrado."

        usuario = Usuario(
            nome=nome.strip(),
            email=email.strip().lower(),
            senha_hash=generate_password_hash(senha),
            familia_id=familia.id,
            is_admin=is_admin,
        )
        session.add(usuario)
        session.commit()

        return usuario, None

    except Exception as e:
        session.rollback()
        return None, f"Erro ao cadastrar: {str(e)}"

    finally:
        session.close()


def autenticar(email: str, senha: str) -> Usuario | None:
    session = SessionLocal()
    try:
        usuario = session.query(Usuario).filter_by(email=email.strip().lower()).first()
        if usuario and check_password_hash(usuario.senha_hash, senha):
            return usuario
        return None
    except Exception:
        return None
    finally:
        session.close()
