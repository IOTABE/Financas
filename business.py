from datetime import date
from sqlalchemy import extract, func
from database import SessionLocal
from models import Transacao, MetasOrcamento, Usuario, PlanoDivida, ParcelaDivida, CartaoCredito


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


def buscar_meta_objeto(usuario_id: str, mes: int, ano: int) -> MetasOrcamento | None:
    session = SessionLocal()
    try:
        return session.query(MetasOrcamento).filter(
            MetasOrcamento.usuario_id == usuario_id,
            MetasOrcamento.mes == mes,
            MetasOrcamento.ano == ano,
            MetasOrcamento.categoria.is_(None),
        ).first()
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
                    descricao: str = "",
                    forma_pagamento: str | None = None,
                    cartao_credito_id: str | None = None) -> Transacao | None:
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
            forma_pagamento=forma_pagamento,
            cartao_credito_id=cartao_credito_id,
        )
        session.add(transacao)
        session.commit()
        return transacao
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao criar transação: {e}") from e
    finally:
        session.close()


def editar_transacao(transacao_id: str, tipo: str, categoria: str,
                     valor: float, data: date, descricao: str = "",
                     forma_pagamento: str | None = None) -> Transacao:
    session = SessionLocal()
    try:
        t = session.query(Transacao).filter_by(id=transacao_id).first()
        if not t:
            raise ValueError("Transação não encontrada.")
        t.tipo = tipo
        t.categoria = categoria
        t.valor = valor
        t.data = data
        t.descricao = descricao
        t.forma_pagamento = forma_pagamento
        session.commit()
        return t
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao editar transação: {e}") from e
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


def criar_plano_divida(
    usuario_id: str, familia_id: str, credor: str,
    valor_total: float, numero_parcelas: int,
    descricao: str = "", data_primeira_parcela: date | None = None,
) -> PlanoDivida:
    session = SessionLocal()
    try:
        plano = PlanoDivida(
            usuario_id=usuario_id,
            familia_id=familia_id,
            credor=credor.strip(),
            descricao=descricao.strip(),
            valor_total=valor_total,
            numero_parcelas=numero_parcelas,
        )
        session.add(plano)
        session.flush()

        valor_parcela = valor_total / numero_parcelas
        inicio = data_primeira_parcela or date.today().replace(day=1)

        for i in range(numero_parcelas):
            mes = inicio.month + i
            ano = inicio.year + (mes - 1) // 12
            mes = ((mes - 1) % 12) + 1
            dia = min(inicio.day, 28)
            vencimento = date(ano, mes, dia)

            parcela = ParcelaDivida(
                plano_divida_id=plano.id,
                numero=i + 1,
                valor=round(valor_parcela, 2),
                data_vencimento=vencimento,
            )
            session.add(parcela)

        session.commit()
        return plano
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao criar plano de dívida: {e}") from e
    finally:
        session.close()


def listar_planos_familia(familia_id: str) -> list[PlanoDivida]:
    session = SessionLocal()
    try:
        return (
            session.query(PlanoDivida)
            .filter_by(familia_id=familia_id)
            .order_by(PlanoDivida.created_at.desc())
            .all()
        )
    except Exception as e:
        raise RuntimeError(f"Erro ao listar planos: {e}") from e
    finally:
        session.close()


def parcelas_do_plano(plano_id: str) -> list[ParcelaDivida]:
    session = SessionLocal()
    try:
        return (
            session.query(ParcelaDivida)
            .filter_by(plano_divida_id=plano_id)
            .order_by(ParcelaDivida.numero)
            .all()
        )
    except Exception as e:
        raise RuntimeError(f"Erro ao listar parcelas: {e}") from e
    finally:
        session.close()


def pagar_parcela(parcela_id: str, usuario_id: str, familia_id: str, data_pagamento: date | None = None) -> ParcelaDivida:
    session = SessionLocal()
    try:
        parcela = session.query(ParcelaDivida).filter_by(id=parcela_id).first()
        if not parcela:
            raise ValueError("Parcela não encontrada.")
        if parcela.paga:
            raise ValueError("Parcela já foi paga.")

        plano = session.query(PlanoDivida).filter_by(id=parcela.plano_divida_id).first()

        transacao = Transacao(
            usuario_id=usuario_id,
            familia_id=familia_id,
            tipo="despesa",
            categoria="Dívidas",
            valor=parcela.valor,
            data=data_pagamento or date.today(),
            descricao=f"{plano.credor} — Parcela {parcela.numero}/{plano.numero_parcelas}",
        )
        session.add(transacao)
        session.flush()

        parcela.paga = True
        parcela.transacao_id = transacao.id
        session.commit()
        return parcela
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao pagar parcela: {e}") from e
    finally:
        session.close()


def editar_plano_divida(plano_id: str, credor: str, descricao: str) -> PlanoDivida:
    session = SessionLocal()
    try:
        plano = session.query(PlanoDivida).filter_by(id=plano_id).first()
        if not plano:
            raise ValueError("Plano não encontrado.")
        plano.credor = credor.strip()
        plano.descricao = descricao.strip()
        session.commit()
        return plano
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao editar plano: {e}") from e
    finally:
        session.close()


def editar_parcela(parcela_id: str, valor: float, data_vencimento: date) -> ParcelaDivida:
    session = SessionLocal()
    try:
        parcela = session.query(ParcelaDivida).filter_by(id=parcela_id).first()
        if not parcela:
            raise ValueError("Parcela não encontrada.")
        if parcela.paga:
            raise ValueError("Não é possível editar uma parcela já paga.")
        parcela.valor = valor
        parcela.data_vencimento = data_vencimento
        session.commit()
        return parcela
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao editar parcela: {e}") from e
    finally:
        session.close()


def deletar_plano_divida(plano_id: str) -> None:
    session = SessionLocal()
    try:
        plano = session.query(PlanoDivida).filter_by(id=plano_id).first()
        if not plano:
            raise ValueError("Plano não encontrado.")

        parcelas = session.query(ParcelaDivida).filter_by(plano_divida_id=plano_id).all()
        for p in parcelas:
            session.delete(p)
        session.delete(plano)
        session.commit()
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao deletar plano: {e}") from e
    finally:
        session.close()


def total_parcelas_pendentes_mes(familia_id: str, mes: int, ano: int) -> float:
    session = SessionLocal()
    try:
        valor = session.query(func.coalesce(func.sum(ParcelaDivida.valor), 0.0)).join(
            PlanoDivida, ParcelaDivida.plano_divida_id == PlanoDivida.id
        ).filter(
            PlanoDivida.familia_id == familia_id,
            ParcelaDivida.paga == False,
            extract("month", ParcelaDivida.data_vencimento) == mes,
            extract("year", ParcelaDivida.data_vencimento) == ano,
        ).scalar()
        return float(valor)
    except Exception as e:
        raise RuntimeError(f"Erro ao calcular pendências do mês: {e}") from e
    finally:
        session.close()


def evolucao_parcelas_pendentes(familia_id: str) -> list[dict]:
    session = SessionLocal()
    try:
        hoje = date.today()
        rows = session.query(
            extract("year", ParcelaDivida.data_vencimento).label("ano"),
            extract("month", ParcelaDivida.data_vencimento).label("mes"),
            func.coalesce(func.sum(ParcelaDivida.valor), 0.0).label("total"),
        ).join(
            PlanoDivida, ParcelaDivida.plano_divida_id == PlanoDivida.id
        ).filter(
            PlanoDivida.familia_id == familia_id,
            ParcelaDivida.paga == False,
            ParcelaDivida.data_vencimento >= hoje,
        ).group_by(
            "ano", "mes"
        ).order_by(
            "ano", "mes"
        ).all()
        return [{"ano": int(r.ano), "mes": int(r.mes), "total": float(r.total)} for r in rows]
    except Exception as e:
        raise RuntimeError(f"Erro ao calcular evolução: {e}") from e
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Cartões de crédito
# ---------------------------------------------------------------------------


def _proximo_vencimento(dia_vencimento: int) -> date:
    hoje = date.today()
    try:
        proximo = date(hoje.year, hoje.month, dia_vencimento)
    except ValueError:
        import calendar
        ultimo = calendar.monthrange(hoje.year, hoje.month)[1]
        proximo = date(hoje.year, hoje.month, min(dia_vencimento, ultimo))
    if proximo <= hoje:
        if hoje.month == 12:
            ano, mes = hoje.year + 1, 1
        else:
            ano, mes = hoje.year, hoje.month + 1
        try:
            proximo = date(ano, mes, dia_vencimento)
        except ValueError:
            import calendar
            ultimo = calendar.monthrange(ano, mes)[1]
            proximo = date(ano, mes, min(dia_vencimento, ultimo))
    return proximo


def criar_cartao_credito(usuario_id: str, familia_id: str, nome: str,
                         bandeira: str, dia_vencimento: int,
                         dia_fechamento: int) -> CartaoCredito:
    session = SessionLocal()
    try:
        cartao = CartaoCredito(
            usuario_id=usuario_id,
            familia_id=familia_id,
            nome=nome.strip(),
            bandeira=bandeira.strip(),
            dia_vencimento=dia_vencimento,
            dia_fechamento=dia_fechamento,
        )
        session.add(cartao)
        session.commit()
        return cartao
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao criar cartão: {e}") from e
    finally:
        session.close()


def listar_cartoes_familia(familia_id: str) -> list[CartaoCredito]:
    session = SessionLocal()
    try:
        return session.query(CartaoCredito).filter_by(familia_id=familia_id).all()
    except Exception as e:
        raise RuntimeError(f"Erro ao listar cartões: {e}") from e
    finally:
        session.close()


def editar_cartao_credito(cartao_id: str, nome: str, bandeira: str,
                          dia_vencimento: int, dia_fechamento: int) -> CartaoCredito:
    session = SessionLocal()
    try:
        cartao = session.query(CartaoCredito).filter_by(id=cartao_id).first()
        if not cartao:
            raise ValueError("Cartão não encontrado.")
        cartao.nome = nome.strip()
        cartao.bandeira = bandeira.strip()
        cartao.dia_vencimento = dia_vencimento
        cartao.dia_fechamento = dia_fechamento
        session.commit()
        return cartao
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao editar cartão: {e}") from e
    finally:
        session.close()


def deletar_cartao_credito(cartao_id: str) -> None:
    session = SessionLocal()
    try:
        cartao = session.query(CartaoCredito).filter_by(id=cartao_id).first()
        if not cartao:
            raise ValueError("Cartão não encontrado.")
        session.delete(cartao)
        session.commit()
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao deletar cartão: {e}") from e
    finally:
        session.close()


def criar_compra_cartao(usuario_id: str, familia_id: str, cartao_id: str,
                        descricao: str, valor: float, categoria: str,
                        data_compra: date) -> ParcelaDivida:
    session = SessionLocal()
    try:
        cartao = session.query(CartaoCredito).filter_by(id=cartao_id).first()
        if not cartao:
            raise ValueError("Cartão não encontrado.")

        vencimento = _proximo_vencimento(cartao.dia_vencimento)

        plano = session.query(PlanoDivida).filter(
            PlanoDivida.familia_id == familia_id,
            PlanoDivida.credor == f"Cartão {cartao.nome}",
        ).first()

        if not plano:
            plano = PlanoDivida(
                usuario_id=usuario_id,
                familia_id=familia_id,
                credor=f"Cartão {cartao.nome}",
                descricao="Fatura cartão de crédito",
                valor_total=0,
                numero_parcelas=0,
            )
            session.add(plano)
            session.flush()

        parcela = ParcelaDivida(
            plano_divida_id=plano.id,
            numero=plano.numero_parcelas + 1,
            valor=valor,
            data_vencimento=vencimento,
        )
        session.add(parcela)
        plano.valor_total += valor
        plano.numero_parcelas += 1
        session.commit()
        return parcela
    except Exception as e:
        session.rollback()
        raise RuntimeError(f"Erro ao registrar compra no cartão: {e}") from e
    finally:
        session.close()
