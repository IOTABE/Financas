from datetime import date
from sqlalchemy import extract, func
from database import SessionLocal
from models import Transacao, MetasOrcamento, Usuario


def gastos_usuario_mes(usuario_id: str, mes: int, ano: int) -> float:
    session = SessionLocal()
    try:
        valor = session.query(func.coalesce(func.sum(Transacao.valor), 0.0)).filter(
            Transacao.usuario_id == usuario_id,
            Transacao.tipo == "despesa",
            extract("month", Transacao.data) == mes,
            extract("year", Transacao.data) == ano,
        ).scalar()
        return float(valor)
    except Exception as e:
        raise RuntimeError(f"Erro ao calcular gastos do usuário: {e}") from e
    finally:
        session.close()


def receitas_usuario_mes(usuario_id: str, mes: int, ano: int) -> float:
    session = SessionLocal()
    try:
        valor = session.query(func.coalesce(func.sum(Transacao.valor), 0.0)).filter(
            Transacao.usuario_id == usuario_id,
            Transacao.tipo == "receita",
            extract("month", Transacao.data) == mes,
            extract("year", Transacao.data) == ano,
        ).scalar()
        return float(valor)
    except Exception as e:
        raise RuntimeError(f"Erro ao calcular receitas do usuário: {e}") from e
    finally:
        session.close()


def gastos_familia_mes(familia_id: str, mes: int, ano: int) -> float:
    session = SessionLocal()
    try:
        valor = session.query(func.coalesce(func.sum(Transacao.valor), 0.0)).filter(
            Transacao.familia_id == familia_id,
            Transacao.tipo == "despesa",
            extract("month", Transacao.data) == mes,
            extract("year", Transacao.data) == ano,
        ).scalar()
        return float(valor)
    except Exception as e:
        raise RuntimeError(f"Erro ao calcular gastos da família: {e}") from e
    finally:
        session.close()


def receitas_familia_mes(familia_id: str, mes: int, ano: int) -> float:
    session = SessionLocal()
    try:
        valor = session.query(func.coalesce(func.sum(Transacao.valor), 0.0)).filter(
            Transacao.familia_id == familia_id,
            Transacao.tipo == "receita",
            extract("month", Transacao.data) == mes,
            extract("year", Transacao.data) == ano,
        ).scalar()
        return float(valor)
    except Exception as e:
        raise RuntimeError(f"Erro ao calcular receitas da família: {e}") from e
    finally:
        session.close()


def saldo_familiar(familia_id: str, mes: int, ano: int) -> tuple:
    receitas = receitas_familia_mes(familia_id, mes, ano)
    despesas = gastos_familia_mes(familia_id, mes, ano)
    return receitas, despesas, receitas - despesas


def meta_mensal_usuario(usuario_id: str, mes: int, ano: int) -> float | None:
    session = SessionLocal()
    try:
        meta = session.query(MetasOrcamento).filter(
            MetasOrcamento.usuario_id == usuario_id,
            MetasOrcamento.mes == mes,
            MetasOrcamento.ano == ano,
            MetasOrcamento.categoria.is_(None),
        ).first()
        return float(meta.valor_limite) if meta else None
    except Exception as e:
        raise RuntimeError(f"Erro ao buscar meta: {e}") from e
    finally:
        session.close()


def gasto_excedeu_meta(usuario_id: str, mes: int, ano: int) -> tuple:
    total_gasto = gastos_usuario_mes(usuario_id, mes, ano)
    limite = meta_mensal_usuario(usuario_id, mes, ano)
    if limite is None:
        return False, total_gasto, None
    return (total_gasto >= limite), total_gasto, limite


def listar_membros_familia(familia_id: str) -> list:
    session = SessionLocal()
    try:
        return session.query(Usuario).filter_by(familia_id=familia_id).all()
    except Exception as e:
        raise RuntimeError(f"Erro ao listar membros: {e}") from e
    finally:
        session.close()


def criar_transacao(usuario_id: str, familia_id: str, tipo: str,
                    categoria: str, valor: float, data: date,
                    descricao: str = "") -> Transacao | None:
    session = SessionLocal()
    try:
        transacao = Transacao(
            usuario_id=usuario_id,
            familia_id=familia_id,
            tipo=tipo,
            categoria=categoria,
            valor=valor,
            data=data,
            descricao=descricao,
        )
        session.add(transacao)
        session.commit()
        return transacao
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao criar transação: {e}") from e
    finally:
        session.close()


def definir_meta(usuario_id: str, familia_id: str, valor_limite: float,
                 mes: int, ano: int, categoria: str | None = None) -> MetasOrcamento:
    session = SessionLocal()
    try:
        existing = session.query(MetasOrcamento).filter(
            MetasOrcamento.usuario_id == usuario_id,
            MetasOrcamento.mes == mes,
            MetasOrcamento.ano == ano,
            (
                MetasOrcamento.categoria.is_(None)
                if categoria is None
                else MetasOrcamento.categoria == categoria
            ),
        ).first()

        if existing:
            existing.valor_limite = valor_limite
            meta = existing
        else:
            meta = MetasOrcamento(
                usuario_id=usuario_id,
                familia_id=familia_id,
                valor_limite=valor_limite,
                mes=mes,
                ano=ano,
                categoria=categoria,
            )
            session.add(meta)

        session.commit()
        return meta
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao definir meta: {e}") from e
    finally:
        session.close()


def transacoes_recentes_familia(familia_id: str, limite: int = 50) -> list:
    session = SessionLocal()
    try:
        return (
            session.query(Transacao)
            .filter_by(familia_id=familia_id)
            .order_by(Transacao.data.desc(), Transacao.created_at.desc())
            .limit(limite)
            .all()
        )
    except Exception as e:
        raise RuntimeError(f"Erro ao listar transações: {e}") from e
    finally:
        session.close()


def despesas_por_categoria(familia_id: str, mes: int, ano: int) -> dict:
    session = SessionLocal()
    try:
        rows = (
            session.query(
                Transacao.categoria,
                func.coalesce(func.sum(Transacao.valor), 0.0)
            )
            .filter(
                Transacao.familia_id == familia_id,
                Transacao.tipo == "despesa",
                extract("month", Transacao.data) == mes,
                extract("year", Transacao.data) == ano,
            )
            .group_by(Transacao.categoria)
            .all()
        )
        return {cat: float(val) for cat, val in rows}
    except Exception as e:
        raise RuntimeError(f"Erro ao agregar despesas: {e}") from e
    finally:
        session.close()


def gastos_por_membro(familia_id: str, mes: int, ano: int) -> list[dict]:
    session = SessionLocal()
    try:
        membros = session.query(Usuario).filter_by(familia_id=familia_id).all()
        resultado = []
        for m in membros:
            gasto = gastos_usuario_mes(m.id, mes, ano)
            receita = receitas_usuario_mes(m.id, mes, ano)
            meta = meta_mensal_usuario(m.id, mes, ano)
            resultado.append({
                "nome": m.nome,
                "gasto": gasto,
                "receita": receita,
                "meta": meta or 0,
            })
        return resultado
    except Exception as e:
        raise RuntimeError(f"Erro ao calcular gastos por membro: {e}") from e
    finally:
        session.close()
