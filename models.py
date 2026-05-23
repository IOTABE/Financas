import uuid
from datetime import datetime, date

from sqlalchemy import (
    Column, String, Float, Boolean, DateTime, Date,
    ForeignKey, Integer, UniqueConstraint,
)
from database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Familia(Base):
    __tablename__ = "familias"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    nome = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Familia {self.nome}>"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    familia_id = Column(String(36), ForeignKey("familias.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Usuario {self.nome}>"


class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False, index=True)
    familia_id = Column(String(36), ForeignKey("familias.id"), nullable=False, index=True)
    tipo = Column(String(10), nullable=False)
    categoria = Column(String(50), nullable=False)
    valor = Column(Float, nullable=False)
    data = Column(Date, default=date.today, index=True)
    descricao = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transacao {self.tipo} R${self.valor:.2f}>"


class PlanoDivida(Base):
    __tablename__ = "planos_divida"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False, index=True)
    familia_id = Column(String(36), ForeignKey("familias.id"), nullable=False, index=True)
    credor = Column(String(100), nullable=False)
    descricao = Column(String(255), default="")
    valor_total = Column(Float, nullable=False)
    numero_parcelas = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PlanoDivida {self.credor} R${self.valor_total:.2f}>"


class ParcelaDivida(Base):
    __tablename__ = "parcelas_divida"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    plano_divida_id = Column(String(36), ForeignKey("planos_divida.id"), nullable=False, index=True)
    numero = Column(Integer, nullable=False)
    valor = Column(Float, nullable=False)
    data_vencimento = Column(Date, nullable=False, index=True)
    paga = Column(Boolean, default=False)
    transacao_id = Column(String(36), ForeignKey("transacoes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Parcela {self.numero}/{self.plano_divida_id} {'PAGA' if self.paga else 'PENDENTE'}>"


class MetasOrcamento(Base):
    __tablename__ = "metas_orcamento"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    usuario_id = Column(String(36), ForeignKey("usuarios.id"), nullable=False, index=True)
    familia_id = Column(String(36), ForeignKey("familias.id"), nullable=False, index=True)
    categoria = Column(String(50), nullable=True)
    valor_limite = Column(Float, nullable=False)
    mes = Column(Integer, nullable=False)
    ano = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "categoria", "mes", "ano",
            name="uq_meta_usuario_categoria_mes_ano"
        ),
    )

    def __repr__(self):
        return f"<Meta {self.usuario_id} {self.mes}/{self.ano} R${self.valor_limite:.2f}>"
