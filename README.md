# Finanças Familiares

Aplicativo web para gestão financeira familiar com Streamlit.

## Funcionalidades

- **Controle de receitas e despesas** — lançamento de transações com categorias, datas e descrição
- **Dashboard mensal** — métricas de receitas, despesas, saldo e economia%; gráficos de barras e pizza
- **Plano de dívidas** — cadastro de planos de pagamento com geração automática de parcelas; pagamento de parcelas com lançamento automático de despesa no extrato financeiro
- **Metas de orçamento** — administradores definem limites mensais por membro; bloqueio automático de novas despesas quando a meta é atingida
- **Múltiplos membros** — cada família agrupa seus usuários; o primeiro a se cadastrar torna-se administrador
- **Tema claro/escuro** — toggle na barra lateral
- **Autenticação** — cadastro e login com senha hasheada (werkzeug)
- **Categorias** — Alimentação, Moradia, Transporte, Saúde, Educação, Lazer, Vestuário, Assinaturas, Utilidades, Dívidas, Outros

## Instalação

### Pré-requisitos

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/) (recomendado) ou pip

### Via uv

```bash
uv sync
```

### Via pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuração (opcional)

O banco de dados padrão é SQLite (`financas.db`). Para usar PostgreSQL, defina a variável de ambiente:

```bash
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/financas"
```

## Execução

```bash
streamlit run app.py
```

Acesse em `http://localhost:8501`.

## Estrutura do projeto

```
.
├── app.py          # Interface Streamlit (páginas, modais, CSS, roteamento)
├── auth.py         # Autenticação (cadastro e login)
├── business.py     # Lógica de negócio e consultas ao banco
├── database.py     # Configuração do SQLAlchemy (engine, sessão)
├── models.py       # Modelos ORM (Familia, Usuario, Transacao, MetasOrcamento, PlanoDivida, ParcelaDivida)
├── main.py         # Ponto de entrada (placeholder)
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## Fluxo de uso

1. **Cadastre-se** — o primeiro usuário de uma família é automaticamente administrador
2. **Registre transações** — receitas (salário, freelance, etc.) e despesas (alimentação, moradia, etc.)
3. **Defina metas** (admin) — limite de gastos mensais por membro
4. **Crie planos de dívida** — informe credor, valor total e parcelas; as parcelas são geradas automaticamente
5. **Pague parcelas** — cada pagamento gera automaticamente uma despesa na categoria "Dívidas"
6. **Acompanhe no Dashboard** — gráficos de receitas vs despesas, despesas por categoria, comparativo por membro e evolução das parcelas pendentes
