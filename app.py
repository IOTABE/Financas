import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

from database import init_db
from auth import registrar_usuario, autenticar
from business import (
    gasto_excedeu_meta,
    criar_transacao,
    saldo_familiar,
    listar_membros_familia,
    definir_meta,
    despesas_por_categoria,
    transacoes_recentes_familia,
    criar_plano_divida,
    listar_planos_familia,
    parcelas_do_plano,
    pagar_parcela,
    editar_plano_divida,
    editar_parcela,
    deletar_plano_divida,
    total_parcelas_pendentes_mes,
    evolucao_parcelas_pendentes,
)

def render_html_table(df, class_name="data-table"):
    parts = [f'<table class="{class_name}"><thead><tr>']
    for col in df.columns:
        parts.append(f"<th>{col}</th>")
    parts.append("</tr></thead><tbody>")
    for _, row in df.iterrows():
        parts.append("<tr>")
        for val in row:
            parts.append(f"<td>{val}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)

# ---------------------------------------------------------------------------
# 1. Config inicial
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Finanças Familiares",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

for key, default in [
    ("authenticated", False),
    ("dark_mode", False),
    ("page", "dashboard"),
    ("user_id", None),
    ("user_name", None),
    ("familia_id", None),
    ("is_admin", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------------------------------------------------------
# 2. CSS de temas
# ---------------------------------------------------------------------------
MODAL_CSS = """
<style>
    /* backdrop em tela cheia com blur */
    div[data-testid="stDialog"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        backdrop-filter: blur(6px) !important;
        -webkit-backdrop-filter: blur(6px) !important;
        animation: modalFadeIn 0.25s ease-out;
        align-content: center !important;
    }
    /* card flutuante centralizado — altura exclusivamente do conteúdo */
    div[data-testid="stDialog"] > div {
        border-radius: 20px !important;
        padding: 0.3rem 1.8rem 0.4rem !important;
        box-shadow:
            0 25px 60px rgba(0,0,0,0.35),
            0 8px 20px rgba(0,0,0,0.15) !important;
        animation: modalSlideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        width: auto !important;
        min-width: 360px;
        max-width: 560px;
        min-height: 0 !important;
        height: fit-content !important;
        margin: 0 !important;
    }
    div[data-testid="stDialog"] > div > div {
        border-radius: 20px !important;
        padding: 0 !important;
        min-height: 0 !important;
        height: fit-content !important;
    }
    div[data-testid="stDialog"] div[data-testid="stVerticalBlockBorderSeparator"] {
        display: none !important;
    }
    div[data-testid="stDialog"] [data-testid="column"] {
        gap: 0 !important;
    }
    div[data-testid="stDialog"] [data-testid="stForm"] > div > div {
        gap: 0.25rem !important;
        min-height: 0 !important;
    }
    div[data-testid="stDialog"] [data-testid="stForm"] {
        min-height: 0 !important;
    }
    div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 {
        margin: 0 0 0.15rem 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stDialog"] .row-widget {
        margin-bottom: 0 !important;
    }
    div[data-testid="stDialog"] label {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stDialog"] [data-testid="stForm"] [data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }
    div[data-testid="stDialog"] hr {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }
    div[data-testid="stDialog"] .stAlert {
        padding: 0.4rem 0.8rem !important;
        margin-bottom: 0.3rem !important;
    }
    div[data-testid="stDialog"] .stButton {
        margin-bottom: 0 !important;
    }
    div[data-testid="stDialog"] .stButton button {
        padding: 0.15rem 0 !important;
        min-height: 0 !important;
        line-height: 1.3 !important;
    }
    div[data-testid="stDialog"] div[data-testid="stForm"] > div > div > div:last-child {
        margin-bottom: 0 !important;
    }
    div[data-testid="stDialog"] thead tr th:first-child {
        border-radius: 14px 0 0 0;
    }
    div[data-testid="stDialog"] thead tr th:last-child {
        border-radius: 0 14px 0 0;
    }
    @keyframes modalFadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes modalSlideUp {
        from { opacity: 0; transform: translateY(40px) scale(0.96); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
    }
</style>
"""

DARK_CSS = MODAL_CSS + """
<style>
    .stApp      { background-color: #0e1117; color: #f0f0f0; }
    section[data-testid="stSidebar"] { background-color: #1b1f2a; }
    h1, h2, h3, h4, h5, h6, p, li, label, span, div {
        color: #f0f0f0 !important;
    }
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stDateInput>div>div>input,
    .stSelectbox>div>div>div { background-color: #262730; color: #f0f0f0; border-color: #3c3c3c; }
    .st-bb { background-color: #262730 !important; }
    .stButton>button { background-color: #ff4b4b; color: #fff; border: none; }
    div[data-testid="stFormSubmitButton"] > button { background-color: #0068c9 !important; border: none !important; }
    div[data-testid="stFormSubmitButton"] > button, div[data-testid="stFormSubmitButton"] > button * { color: #ffffff !important; }
    div[data-testid="stFormSubmitButton"] > button:hover { background-color: #0056a3 !important; }
    .stAlert { background-color: #262730 !important; border: 1px solid #3c3c3c !important; color: #e0e0e0 !important; }
    div[data-testid="stMetric"] { background-color: #262730; padding: 12px; border-radius: 8px; border: 1px solid #3c3c3c; }
    div[data-testid="stDataFrame"] {
        background-color: #262730 !important;
    }
    div[data-testid="stDataFrame"] thead th {
        background-color: #1b1f2a !important;
        color: #f0f0f0 !important;
        border-bottom: 1px solid #3c3c3c !important;
    }
    div[data-testid="stDataFrame"] tbody td {
        background-color: #262730 !important;
        color: #e0e0e0 !important;
        border-bottom: 1px solid #333 !important;
    }
    div[data-testid="stDataFrame"] tbody tr:nth-child(even) td {
        background-color: #2a2d37 !important;
    }
    div[data-testid="stDataFrame"] * {
        color: #e0e0e0 !important;
    }
    table.data-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #262730 !important;
    }
    table.data-table th {
        background-color: #1b1f2a !important;
        color: #f0f0f0 !important;
        padding: 8px 12px;
        text-align: left;
        border-bottom: 1px solid #3c3c3c;
    }
    table.data-table td {
        background-color: #262730 !important;
        color: #e0e0e0 !important;
        padding: 8px 12px;
        border-bottom: 1px solid #333;
    }
    table.data-table tbody tr:nth-child(even) td {
        background-color: #2a2d37 !important;
    }
    div[data-testid="stProgress"] > div {
        background-color: #3c3c3c !important;
    }
    div[data-testid="stExpander"] details {
        background-color: #262730 !important;
        border: 1px solid #3c3c3c !important;
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"] details div {
        background-color: #262730 !important;
    }
    div[data-testid="stExpander"] summary {
        color: #f0f0f0 !important;
    }
    button[data-testid="stDialogCloseButton"] svg {
        fill: #f0f0f0 !important;
    }
    input::placeholder, textarea::placeholder {
        color: #888 !important;
    }
    .stCaption {
        color: #aaaaaa !important;
    }
    .block-container { padding-top: 2rem; }
    h1 { border-bottom: 1px solid #3c3c3c; padding-bottom: 0.5rem; }
    section[data-testid="stSidebar"] hr { border-color: #3c3c3c; }
    section[data-testid="stSidebar"] .stButton>button { width: 100%; text-align: left; background-color: transparent; color: #f0f0f0 !important; }
    section[data-testid="stSidebar"] .stButton>button:hover { background-color: #262730; }
    div[data-testid="stDialog"] > div {
        background-color: #1b1f2a !important;
        border: 1px solid #333 !important;
    }
    div[data-testid="stDialog"] > div > div {
        background-color: #1b1f2a !important;
    }
    div[data-testid="stDialog"] div[data-testid="stVerticalBlock"] {
        background: transparent !important;
    }
    div[data-testid="stDialog"] div[data-testid="column"] {
        background: transparent !important;
    }
    div[data-testid="stDialog"] [data-testid="stForm"] {
        background-color: #1b1f2a !important;
    }
    div[data-testid="stDialog"] input,
    div[data-testid="stDialog"] select,
    div[data-testid="stDialog"] textarea {
        background-color: #262730 !important;
        color: #f0f0f0 !important;
        border-color: #3c3c3c !important;
    }
    div[data-testid="stDialog"] .stSelectbox div[data-baseweb="select"] > div {
        background-color: #262730 !important;
    }
    div[data-testid="stDialog"] [data-baseweb="popover"] li,
    div[data-testid="stDialog"] [data-baseweb="popover"] div {
        background-color: #262730 !important;
        color: #f0f0f0 !important;
    }
    div[data-testid="stDialog"] label,
    div[data-testid="stDialog"] .stCaption {
        color: #cccccc !important;
    }
    div[data-testid="stDialog"] .stNumberInput button {
        background-color: #262730 !important;
        color: #f0f0f0 !important;
        border-color: #3c3c3c !important;
    }
</style>
"""

LIGHT_CSS = MODAL_CSS + """
<style>
    .stApp      { background-color: #ffffff; color: #111111; }
    section[data-testid="stSidebar"] { background-color: #f0f2f6; }
    h1, h2, h3, h4, h5, h6, p, li, label, span, div {
        color: #111111 !important;
    }
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stDateInput>div>div>input,
    .stSelectbox>div>div>div { background-color: #ffffff; color: #111111; border-color: #d0d0d0; }
    .st-bb { background-color: #ffffff !important; }
    .stButton>button { background-color: #ff4b4b; color: #fff; border: none; }
    div[data-testid="stFormSubmitButton"] > button { background-color: #0068c9 !important; border: none !important; }
    div[data-testid="stFormSubmitButton"] > button, div[data-testid="stFormSubmitButton"] > button * { color: #ffffff !important; }
    div[data-testid="stFormSubmitButton"] > button:hover { background-color: #0056a3 !important; }
    .stAlert { background-color: #f8f9fa !important; border: 1px solid #e0e0e0 !important; color: #111111 !important; }
    div[data-testid="stMetric"] { background-color: #f8f9fa; padding: 12px; border-radius: 8px; border: 1px solid #e0e0e0; }
    div[data-testid="stDataFrame"] {
        background-color: #ffffff !important;
    }
    div[data-testid="stDataFrame"] thead th {
        background-color: #ffffff !important;
        color: #111111 !important;
        border-bottom: 1px solid #e0e0e0 !important;
    }
    div[data-testid="stDataFrame"] tbody td {
        background-color: #ffffff !important;
        color: #111111 !important;
        border-bottom: 1px solid #f0f0f0 !important;
    }
    div[data-testid="stDataFrame"] tbody tr:nth-child(even) td {
        background-color: #f8f9fa !important;
    }
    div[data-testid="stDataFrame"] * {
        color: #111111 !important;
    }
    table.data-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #ffffff !important;
    }
    table.data-table th {
        background-color: #ffffff !important;
        color: #111111 !important;
        padding: 8px 12px;
        text-align: left;
        border-bottom: 1px solid #e0e0e0;
        font-weight: 600;
    }
    table.data-table td {
        background-color: #ffffff !important;
        color: #111111 !important;
        padding: 8px 12px;
        border-bottom: 1px solid #f0f0f0;
    }
    table.data-table tbody tr:nth-child(even) td {
        background-color: #f8f9fa !important;
    }
    div[data-testid="stProgress"] > div {
        background-color: #e0e0e0 !important;
    }
    div[data-testid="stDataFrame"] tbody td {
        background-color: #ffffff !important;
        color: #111111 !important;
        border-bottom: 1px solid #f0f0f0 !important;
    }
    div[data-testid="stDataFrame"] tbody tr:nth-child(even) td {
        background-color: #f8f9fa !important;
    }
    div[data-testid="stProgress"] > div {
        background-color: #e0e0e0 !important;
    }
    div[data-testid="stExpander"] details {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"] details div {
        background-color: #ffffff !important;
    }
    div[data-testid="stExpander"] summary {
        color: #111111 !important;
    }
    button[data-testid="stDialogCloseButton"] svg {
        fill: #555555 !important;
    }
    .block-container { padding-top: 2rem; }
    h1 { border-bottom: 1px solid #e0e0e0; padding-bottom: 0.5rem; }
    section[data-testid="stSidebar"] hr { border-color: #d0d0d0; }
    section[data-testid="stSidebar"] .stButton>button { width: 100%; text-align: left; background-color: transparent; color: #111111 !important; }
    section[data-testid="stSidebar"] .stButton>button:hover { background-color: #e8eaf0; }
    div[data-testid="stDialog"] > div {
        background-color: #ffffff !important;
        border: 1px solid rgba(0,0,0,0.08) !important;
    }
    div[data-testid="stDialog"] > div > div {
        background-color: #ffffff !important;
    }
    div[data-testid="stDialog"] div[data-testid="stVerticalBlock"] {
        background: transparent !important;
    }
    div[data-testid="stDialog"] div[data-testid="column"] {
        background: transparent !important;
    }
    div[data-testid="stDialog"] [data-testid="stForm"] {
        background-color: #ffffff !important;
    }
    div[data-testid="stDialog"] input,
    div[data-testid="stDialog"] select,
    div[data-testid="stDialog"] textarea {
        background-color: #ffffff !important;
        color: #111111 !important;
        border-color: #d0d0d0 !important;
    }
    div[data-testid="stDialog"] .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
    }
    div[data-testid="stDialog"] [data-baseweb="popover"] li,
    div[data-testid="stDialog"] [data-baseweb="popover"] div {
        background-color: #ffffff !important;
        color: #111111 !important;
    }
    div[data-testid="stDialog"] label,
    div[data-testid="stDialog"] .stCaption {
        color: #555555 !important;
    }
    div[data-testid="stDialog"] .stNumberInput button {
        background-color: #ffffff !important;
        color: #555555 !important;
        border: 1px solid #d0d0d0 !important;
    }
</style>
"""



def aplicar_tema():
    css = DARK_CSS if st.session_state["dark_mode"] else LIGHT_CSS
    st.markdown(css, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 3. Páginas
# ---------------------------------------------------------------------------

@st.dialog("Criar Conta")
def modal_cadastro():
    with st.form("register_form"):
        nome = st.text_input("Nome completo")
        email = st.text_input("Email", placeholder="seu@email.com")
        senha = st.text_input("Senha", type="password")
        senha_confirm = st.text_input("Confirmar senha", type="password")
        nome_familia = st.text_input(
            "Nome da família",
            placeholder='Ex: "Silva" — crie ou entre em uma família'
        )
        if st.form_submit_button("Cadastrar", width='stretch'):
            if senha != senha_confirm:
                st.error("Senhas não conferem.")
            elif not nome or not email or not senha or not nome_familia:
                st.warning("Preencha todos os campos.")
            else:
                usuario, erro = registrar_usuario(nome, email, senha, nome_familia)
                if usuario:
                    st.success("Cadastro realizado com sucesso! Faça login.")
                    st.rerun()
                else:
                    st.error(erro)


def pagina_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("💰 Finanças Familiares")
        st.markdown("---")

        with st.form("login_form"):
            email = st.text_input("Email", placeholder="seu@email.com")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", width='stretch'):
                usuario = autenticar(email, senha)
                if usuario:
                    st.session_state["authenticated"] = True
                    st.session_state["user_id"] = usuario.id
                    st.session_state["user_name"] = usuario.nome
                    st.session_state["user_email"] = usuario.email
                    st.session_state["familia_id"] = usuario.familia_id
                    st.session_state["is_admin"] = usuario.is_admin
                    st.session_state["page"] = "dashboard"
                    st.rerun()
                else:
                    st.error("Email ou senha inválidos.")

        st.markdown("---")
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        if st.button("🆕 Criar nova conta", width='stretch', type="secondary"):
            modal_cadastro()
        st.markdown("</div>", unsafe_allow_html=True)


def pagina_dashboard():
    hoje = date.today()
    mes, ano = hoje.month, hoje.year
    familia_id = st.session_state["familia_id"]

    col_title, col_fab = st.columns([3, 1])
    with col_title:
        st.title("📊 Dashboard Familiar")
    with col_fab:
        st.markdown("<div style='padding-top: 18px;'>", unsafe_allow_html=True)
        if st.button("➕ Nova Transação", width='stretch', type="primary"):
            modal_nova_transacao()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"**Período:** {mes:02d}/{ano}")

    receitas, despesas, saldo = saldo_familiar(familia_id, mes, ano)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receitas", f"R$ {receitas:,.2f}")
    col2.metric("Despesas", f"R$ {despesas:,.2f}")
    col3.metric("Saldo", f"R$ {saldo:,.2f}",
                delta=f"R$ {saldo:,.2f}" if saldo >= 0 else None)
    col4.metric("Economia (%)",
                f"{((receitas - despesas) / receitas * 100):.1f}%"
                if receitas > 0 else "N/A")

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        df_resumo = pd.DataFrame({
            "Tipo": ["Receitas", "Despesas"],
            "Valor (R$)": [receitas, despesas],
        })
        cores = {"Receitas": "#00cc96", "Despesas": "#ff4b4b"}
        fig1 = px.bar(
            df_resumo, x="Tipo", y="Valor (R$)", color="Tipo",
            color_discrete_map=cores, text_auto=".2f",
            title="Receitas vs Despesas — Total Familiar",
        )
        grid_c = "#3c3c3c" if st.session_state["dark_mode"] else "#e0e0e0"
        fig1.update_layout(
            showlegend=False, height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#f0f0f0" if st.session_state["dark_mode"] else "#111111",
            xaxis=dict(gridcolor=grid_c, zerolinecolor=grid_c),
            yaxis=dict(gridcolor=grid_c, zerolinecolor=grid_c),
        )
        st.plotly_chart(fig1, width='stretch')

    with c2:
        desp_cat = despesas_por_categoria(familia_id, mes, ano)
        if desp_cat:
            df_cat = pd.DataFrame(
                list(desp_cat.items()),
                columns=["Categoria", "Valor (R$)"]
            )
            fig2 = px.pie(
                df_cat, values="Valor (R$)", names="Categoria",
                title="Despesas por Categoria",
                color_discrete_sequence=px.colors.qualitative.Prism,
                hole=0.4,
            )
            fig2.update_layout(
                height=400,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#f0f0f0" if st.session_state["dark_mode"] else "#111111",
            )
            st.plotly_chart(fig2, width='stretch')
        else:
            st.info("Nenhuma despesa registrada neste mês.")

    st.markdown("---")

    membros_data = gastos_por_membro(familia_id, mes, ano)
    if membros_data:
        df_membros = pd.DataFrame(membros_data)
        df_membros["Saldo"] = df_membros["receita"] - df_membros["gasto"]
        df_membros["% Meta"] = df_membros.apply(
            lambda r: f"{min(r['gasto'] / r['meta'] * 100, 100):.0f}%"
            if r["meta"] > 0 else "—",
            axis=1,
        )

        fig3 = px.bar(
            df_membros,
            x="nome",
            y=["receita", "gasto"],
            barmode="group",
            title="Comparativo Individual — Receitas vs Gastos",
            color_discrete_map={"receita": "#00cc96", "gasto": "#ff4b4b"},
            text_auto=".2f",
        )
        grid_c = "#3c3c3c" if st.session_state["dark_mode"] else "#e0e0e0"
        fig3.update_layout(
            height=400, legend_title_text="Tipo",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#f0f0f0" if st.session_state["dark_mode"] else "#111111",
            xaxis=dict(gridcolor=grid_c, zerolinecolor=grid_c),
            yaxis=dict(gridcolor=grid_c, zerolinecolor=grid_c),
        )
        st.plotly_chart(fig3, width='stretch')

        fig4 = go.Figure()
        for _, row in df_membros.iterrows():
            fig4.add_trace(go.Bar(
                name=row["nome"],
                x=["Gasto Atual", "Meta"],
                y=[row["gasto"], row["meta"]],
                text=[f"R$ {row['gasto']:,.2f}", f"R$ {row['meta']:,.2f}"],
                textposition="outside",
            ))
        grid_c = "#3c3c3c" if st.session_state["dark_mode"] else "#e0e0e0"
        fig4.update_layout(
            barmode="group",
            title="Gasto vs Meta por Membro",
            height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#f0f0f0" if st.session_state["dark_mode"] else "#111111",
            xaxis=dict(gridcolor=grid_c, zerolinecolor=grid_c),
            yaxis=dict(gridcolor=grid_c, zerolinecolor=grid_c),
        )
        st.plotly_chart(fig4, width='stretch')

        with st.expander("📋 Tabela detalhada"):
            st.dataframe(
                df_membros.rename(columns={
                    "nome": "Membro",
                    "receita": "Receita (R$)",
                    "gasto": "Gasto (R$)",
                    "meta": "Meta (R$)",
                    "Saldo": "Saldo (R$)",
                    "% Meta": "Uso da Meta",
                }),
                width='stretch',
                hide_index=True,
            )

    st.markdown("---")
    st.subheader("💳 Dívidas — Previsão de Pagamentos")

    pendente_mes = total_parcelas_pendentes_mes(familia_id, mes, ano)
    col_pend, col_info = st.columns([1, 3])
    col_pend.metric(
        "Parcelas a pagar neste mês",
        f"R$ {pendente_mes:,.2f}" if pendente_mes > 0 else "Nenhuma",
        delta=None,
    )

    evolucao = evolucao_parcelas_pendentes(familia_id)
    if evolucao:
        df_evol = pd.DataFrame(evolucao)
        df_evol["Mês"] = df_evol.apply(
            lambda r: f"{int(r['mes']):02d}/{int(r['ano'])}", axis=1
        )
        df_evol["Total (R$)"] = df_evol["total"]

        fig5 = px.bar(
            df_evol, x="Mês", y="Total (R$)",
            title="Evolução das Parcelas Pendentes",
            text_auto=".2f",
            color_discrete_sequence=["#ffa600"],
        )
        grid_c = "#3c3c3c" if st.session_state["dark_mode"] else "#e0e0e0"
        fig5.update_layout(
            height=350,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#f0f0f0" if st.session_state["dark_mode"] else "#111111",
            xaxis=dict(gridcolor=grid_c, zerolinecolor=grid_c),
            yaxis=dict(gridcolor=grid_c, zerolinecolor=grid_c),
        )
        st.plotly_chart(fig5, width='stretch')
    else:
        st.info("🎉 Nenhuma parcela pendente no planejamento de dívidas.")

    st.markdown("---")
    st.subheader("📜 Últimas Transações")
    transacoes = transacoes_recentes_familia(familia_id, 20)
    if transacoes:
        rows = []
        membros_map = {m.id: m.nome for m in listar_membros_familia(familia_id)}
        for t in transacoes:
            rows.append({
                "Data": t.data,
                "Membro": membros_map.get(t.usuario_id, "—"),
                "Tipo": "💰 Receita" if t.tipo == "receita" else "💸 Despesa",
                "Categoria": t.categoria,
                "Valor": f"R$ {t.valor:,.2f}",
                "Descrição": t.descricao or "—",
            })
        st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
    else:
        st.info("Nenhuma transação encontrada. Registre a primeira!")


@st.dialog("Nova Transação")
def modal_nova_transacao():
    hoje = date.today()
    mes, ano = hoje.month, hoje.year
    user_id = st.session_state["user_id"]

    bloqueado, gasto_atual, limite = gasto_excedeu_meta(user_id, mes, ano)

    if bloqueado:
        st.error(
            f"🚫 **Limite de gastos atingido!** "
            f"Você já gastou **R$ {gasto_atual:,.2f}** "
            f"de **R$ {limite:,.2f}** permitidos."
        )
        st.warning(
            "🔒 Registro de **despesas** bloqueado. "
            "Apenas receitas podem ser lançadas até o próximo mês "
            "ou até o administrador ajustar sua meta."
        )

    with st.form("transacao_form"):

        categorias_receita = [
            "Salário", "Freelance", "Investimentos",
            "Aluguel", "Presente", "Restituição", "Outros"
        ]
        categorias_despesa = [
            "Alimentação", "Moradia", "Transporte",
            "Saúde", "Educação", "Lazer", "Vestuário",
            "Assinaturas", "Utilidades", "Dívidas", "Outros"
        ]

        lin1, lin2 = st.columns(2)
        with lin1:
            tipo = st.selectbox("Tipo", ["receita", "despesa"])
        with lin2:
            cat_list = categorias_receita if tipo == "receita" else categorias_despesa
            cat_disabled = (tipo == "despesa" and bloqueado)
            categoria = st.selectbox("Categoria", cat_list, disabled=cat_disabled)

        if tipo == "despesa" and bloqueado:
            st.caption("⚠️ Despesas bloqueadas pela meta.")

        lin3, lin4 = st.columns(2)
        with lin3:
            valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0, format="%.2f")
        with lin4:
            data = st.date_input("Data", hoje, format="DD/MM/YYYY")

        descricao = st.text_input("Descrição (opcional)", placeholder="Ex: Mercado do mês")

        disabled_submit = (tipo == "despesa" and bloqueado)

        st.markdown("---")

        submitted = st.form_submit_button(
            "Registrar Transação",
            width='stretch',
            disabled=disabled_submit,
        )

        if submitted:
            if disabled_submit:
                st.error("🚫 Operação cancelada. Você excedeu sua meta de gastos mensais.")
            else:
                try:
                    criar_transacao(
                        usuario_id=user_id,
                        familia_id=st.session_state["familia_id"],
                        tipo=tipo,
                        categoria=categoria,
                        valor=valor,
                        data=data,
                        descricao=descricao,
                    )
                    st.success("✅ Transação registrada com sucesso!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao registrar: {e}")

    if bloqueado:
        st.info(
            f"💡 **Resumo:** Gastos atuais = R$ {gasto_atual:,.2f} / "
            f"Limite = R$ {limite:,.2f}"
        )


@st.dialog("Definir Meta")
def modal_definir_meta():
    familia_id = st.session_state["familia_id"]
    membros = listar_membros_familia(familia_id)

    if not membros:
        st.info("Nenhum membro encontrado para definir meta.")
        return

    hoje = date.today()

    with st.form("meta_form"):
        membro_opts = {m.nome: m for m in membros}
        membro_selecionado = st.selectbox("Membro", list(membro_opts.keys()))
        usuario_alvo = membro_opts[membro_selecionado]

        st.caption("Limite global de gastos (sem categoria específica)")

        col1, col2, col3 = st.columns(3)
        with col1:
            valor_limite = st.number_input("Valor (R$)", min_value=0.01, step=50.0, format="%.2f")
        with col2:
            mes = st.number_input("Mês", min_value=1, max_value=12, value=hoje.month)
        with col3:
            ano = st.number_input("Ano", min_value=2020, max_value=2030, value=hoje.year)

        st.markdown("---")

        if st.form_submit_button("Salvar Meta", width='stretch'):
            try:
                definir_meta(
                    usuario_id=usuario_alvo.id,
                    familia_id=familia_id,
                    valor_limite=valor_limite,
                    mes=mes,
                    ano=ano,
                    categoria=None,
                )
                st.success(
                    f"✅ Meta de **R$ {valor_limite:,.2f}** definida para "
                    f"**{usuario_alvo.nome}** em **{mes:02d}/{ano}**."
                )
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar meta: {e}")


@st.dialog("Editar Meta")
def modal_editar_meta(usuario_id: str, mes: int, ano: int):
    from business import buscar_meta_objeto

    meta_obj = buscar_meta_objeto(usuario_id, mes, ano)
    if not meta_obj:
        st.error("Meta não encontrada para este usuário/mês.")
        return

    familia_id = st.session_state["familia_id"]
    membros = listar_membros_familia(familia_id)
    membro_opts = {m.id: m.nome for m in membros}
    nome_membro = membro_opts.get(usuario_id, "—")

    with st.form("editar_meta_form"):
        st.markdown(f"**Membro:** {nome_membro}")
        st.markdown(f"**Período:** {mes:02d}/{ano}")
        st.caption("Limite global de gastos (sem categoria específica)")

        valor_limite = st.number_input(
            "Valor (R$)",
            min_value=0.01,
            step=50.0,
            format="%.2f",
            value=round(meta_obj.valor_limite, 2),
        )

        st.markdown("---")

        if st.form_submit_button("Salvar Alterações", width='stretch'):
            try:
                definir_meta(
                    usuario_id=usuario_id,
                    familia_id=familia_id,
                    valor_limite=valor_limite,
                    mes=mes,
                    ano=ano,
                    categoria=None,
                )
                st.success(
                    f"✅ Meta atualizada para **R$ {valor_limite:,.2f}** "
                    f"({nome_membro} — {mes:02d}/{ano})."
                )
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar meta: {e}")


def pagina_metas():
    st.title("🎯 Metas de Orçamento")

    if not st.session_state["is_admin"]:
        st.warning("Apenas administradores podem definir metas de orçamento.")
        return

    familia_id = st.session_state["familia_id"]
    membros = listar_membros_familia(familia_id)

    if not membros:
        st.info("Nenhum membro encontrado.")
        return

    hoje = date.today()

    col_titulo, col_btn = st.columns([3, 1])
    with col_titulo:
        st.markdown("### Metas Atuais")
    with col_btn:
        st.markdown("<div style='padding-top: 6px;'>", unsafe_allow_html=True)
        if st.button("➕ Nova Meta", width='stretch', type="primary"):
            modal_definir_meta()
        st.markdown("</div>", unsafe_allow_html=True)

    from business import meta_mensal_usuario, gastos_usuario_mes

    data_rows = []
    for m in membros:
        lm = meta_mensal_usuario(m.id, hoje.month, hoje.year)
        gt = gastos_usuario_mes(m.id, hoje.month, hoje.year)
        data_rows.append({
            "Membro": m.nome,
            "Admin": "✅" if m.is_admin else "—",
            "Limite (R$)": f"R$ {lm:,.2f}" if lm else "—",
            "Gasto Atual (R$)": f"R$ {gt:,.2f}",
            "Status": "🔴 BLOQUEADO" if (lm and gt >= lm) else "🟢 OK",
            "id": m.id,
        })

    df_metas = pd.DataFrame(data_rows)

    for _, row in df_metas.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1.5, 1.5, 1.5, 0.7])
        c1.markdown(f"**{row['Membro']}**")
        c2.markdown(row["Admin"])
        c3.markdown(row["Limite (R$)"])
        c4.markdown(row["Gasto Atual (R$)"])
        c5.markdown(row["Status"])
        tem_meta = row["Limite (R$)"] != "—"
        if tem_meta:
            c6.button(
                "✏️", key=f"edit_meta_{row['id']}",
                help="Editar meta",
                on_click=modal_editar_meta,
                args=(row["id"], hoje.month, hoje.year),
            )
        else:
            c6.markdown("—")


# ---------------------------------------------------------------------------
# 4. Dívidas
# ---------------------------------------------------------------------------


@st.dialog("Novo Plano de Dívida")
def modal_novo_plano_divida():
    familia_id = st.session_state["familia_id"]
    membros = listar_membros_familia(familia_id)

    if not membros:
        st.info("Nenhum membro encontrado.")
        return

    hoje = date.today()

    with st.form("plano_divida_form"):
        membro_opts = {m.nome: m for m in membros}
        membro_selecionado = st.selectbox("Responsável pela dívida", list(membro_opts.keys()))
        usuario_alvo = membro_opts[membro_selecionado]

        credor = st.text_input("Credor", placeholder="Ex: Banco do Brasil, Cartão de Crédito")
        descricao = st.text_input("Descrição (opcional)", placeholder="Ex: Financiamento veículo")

        col1, col2 = st.columns(2)
        with col1:
            valor_total = st.number_input("Valor total (R$)", min_value=0.01, step=100.0, format="%.2f")
        with col2:
            num_parcelas = st.number_input("Número de parcelas", min_value=1, max_value=120, value=12, step=1)

        data_primeira = st.date_input("Data da primeira parcela", value=date(hoje.year, hoje.month, 1), format="DD/MM/YYYY")

        st.markdown("---")

        if st.form_submit_button("Criar Plano", width='stretch'):
            if not credor.strip():
                st.warning("Informe o credor.")
            else:
                try:
                    criar_plano_divida(
                        usuario_id=usuario_alvo.id,
                        familia_id=familia_id,
                        credor=credor,
                        valor_total=valor_total,
                        numero_parcelas=num_parcelas,
                        descricao=descricao,
                        data_primeira_parcela=data_primeira,
                    )
                    st.success(f"✅ Plano de {num_parcelas}x de R$ {valor_total/num_parcelas:,.2f} criado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao criar plano: {e}")


@st.dialog("Editar Plano de Dívida")
def modal_editar_plano_divida(plano_id: str):
    planos = listar_planos_familia(st.session_state["familia_id"])
    plano = next((p for p in planos if p.id == plano_id), None)
    if not plano:
        st.error("Plano não encontrado.")
        return

    parcelas = parcelas_do_plano(plano_id)

    with st.form("editar_plano_form"):
        credor = st.text_input("Credor", value=plano.credor)
        descricao = st.text_input("Descrição", value=plano.descricao)

        st.markdown("---")
        st.markdown("### Parcelas")

        edits = []
        for p in parcelas:
            disabled = p.paga
            if disabled:
                st.markdown(f"**Parcela {p.numero}** — ✅ Paga — R$ {p.valor:,.2f}")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    val = st.number_input(
                        f"Parcela {p.numero} — Valor (R$)",
                        value=round(p.valor, 2),
                        min_value=0.01,
                        step=10.0,
                        format="%.2f",
                        key=f"edit_val_{p.id}",
                    )
                with c2:
                    dt = st.date_input(
                        f"Parcela {p.numero} — Vencimento",
                        value=p.data_vencimento,
                        format="DD/MM/YYYY",
                        key=f"edit_dt_{p.id}",
                    )
                edits.append((p.id, val, dt))

        st.markdown("---")

        if st.form_submit_button("Salvar Alterações", width='stretch'):
            try:
                editar_plano_divida(plano_id, credor, descricao)
                for pid, val, dt in edits:
                    editar_parcela(pid, val, dt)
                st.success("✅ Plano atualizado!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao editar: {e}")


@st.dialog("Excluir Plano de Dívida")
def modal_excluir_plano_divida(plano_id: str):
    planos = listar_planos_familia(st.session_state["familia_id"])
    plano = next((p for p in planos if p.id == plano_id), None)
    if not plano:
        st.error("Plano não encontrado.")
        return

    parcelas = parcelas_do_plano(plano_id)
    pagas = sum(1 for p in parcelas if p.paga)

    st.warning(
        f"Tem certeza que deseja excluir o plano **{plano.credor}** "
        f"(R$ {plano.valor_total:,.2f})?"
    )
    if pagas > 0:
        st.info(
            f"ℹ️ {pagas} parcela(s) já foi/foram paga(s). "
            "As transações financeiras geradas **não** serão removidas."
        )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Sim, Excluir", width='stretch', type="primary"):
            try:
                deletar_plano_divida(plano_id)
                st.success("✅ Plano excluído!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")
    with c2:
        if st.button("❌ Cancelar", width='stretch'):
            st.rerun()


def pagina_dividas():
    st.title("💳 Planejamento de Dívidas")

    familia_id = st.session_state["familia_id"]

    col_titulo, col_btn = st.columns([3, 1])
    with col_titulo:
        st.markdown("### Planos Ativos")
    with col_btn:
        st.markdown("<div style='padding-top: 6px;'>", unsafe_allow_html=True)
        if st.button("➕ Novo Plano", width='stretch', type="primary"):
            modal_novo_plano_divida()
        st.markdown("</div>", unsafe_allow_html=True)

    planos = listar_planos_familia(familia_id)

    if not planos:
        st.info("Nenhum plano de dívida cadastrado.")
        return

    membros_map = {m.id: m.nome for m in listar_membros_familia(familia_id)}

    for plano in planos:
        parcelas = parcelas_do_plano(plano.id)
        total_pagas = sum(1 for p in parcelas if p.paga)
        total_pendentes = len(parcelas) - total_pagas
        valor_pago = sum(p.valor for p in parcelas if p.paga)
        valor_pendente = sum(p.valor for p in parcelas if not p.paga)
        progresso = total_pagas / len(parcelas) if parcelas else 0

        with st.expander(
            f"**{plano.credor}** — R$ {plano.valor_total:,.2f} — "
            f"{total_pagas}/{len(parcelas)} parcelas pagas",
            expanded=(total_pendentes > 0),
        ):
            cols = st.columns([2, 1, 1, 1, 1, 1, 1])
            cols[0].markdown(f"**Descrição:** {plano.descricao or '—'}")
            cols[1].markdown(f"**Responsável:** {membros_map.get(plano.usuario_id, '—')}")
            cols[2].markdown(f"**Pendente:** R$ {valor_pendente:,.2f}")
            cols[3].markdown(f"**Pago:** R$ {valor_pago:,.2f}")
            cols[4].markdown(f"**Progresso:** {progresso:.0%}")
            cols[5].button("✏️", key=f"edit_{plano.id}", help="Editar",
                           on_click=modal_editar_plano_divida, args=(plano.id,))
            cols[6].button("🗑️", key=f"del_{plano.id}", help="Excluir",
                           on_click=modal_excluir_plano_divida, args=(plano.id,))

            st.progress(progresso)

            if parcelas:
                st.markdown("#### Parcelas")
                rows = []
                hoje = date.today()
                for p in parcelas:
                    venc = p.data_vencimento
                    status = "✅ Paga" if p.paga else (
                        "🔴 Vencida" if venc < hoje else "🟡 A vencer"
                    )
                    rows.append({
                        "Parcela": f"{p.numero}/{len(parcelas)}",
                        "Vencimento": venc.strftime("%d/%m/%Y"),
                        "Valor": f"R$ {p.valor:,.2f}",
                        "Status": status,
                    })

                df_parcelas = pd.DataFrame(rows)

                col_table, col_action = st.columns([3, 1])
                with col_table:
                    st.markdown(render_html_table(df_parcelas), unsafe_allow_html=True)
                with col_action:
                    pendentes = [p for p in parcelas if not p.paga]
                    if pendentes:
                        prox = pendentes[0]
                        st.markdown("##### Próxima parcela")
                        st.markdown(
                            f"**{prox.numero}/{len(parcelas)}** — "
                            f"R$ {prox.valor:,.2f}"
                        )
                        if st.button(
                            f"💳 Pagar Parcela {prox.numero}",
                            key=f"pay_{prox.id}",
                            width='stretch',
                            type="primary",
                        ):
                            try:
                                pagar_parcela(
                                    parcela_id=prox.id,
                                    usuario_id=st.session_state["user_id"],
                                    familia_id=familia_id,
                                )
                                st.success(f"✅ Parcela {prox.numero} paga!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao pagar: {e}")
                    else:
                        st.success("🎉 Todas as parcelas pagas!")


# ---------------------------------------------------------------------------
# 5. Sidebar e roteamento
# ---------------------------------------------------------------------------

def sidebar():
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state['user_name']}")
        is_admin = st.session_state["is_admin"]
        if is_admin:
            st.markdown("🏅 **Administrador**")
        st.markdown("---")

        if st.button("📊 Dashboard", width='stretch',
                     type="primary" if st.session_state["page"] == "dashboard" else "secondary"):
            st.session_state["page"] = "dashboard"
            st.rerun()

        if st.button("💰 Nova Transação", width='stretch', type="secondary"):
            modal_nova_transacao()

        if st.button("💳 Dívidas", width='stretch',
                     type="primary" if st.session_state["page"] == "dividas" else "secondary"):
            st.session_state["page"] = "dividas"
            st.rerun()

        if is_admin:
            if st.button("🎯 Metas", width='stretch',
                         type="primary" if st.session_state["page"] == "metas" else "secondary"):
                st.session_state["page"] = "metas"
                st.rerun()

        st.markdown("---")

        if st.button("🚪 Sair", width='stretch'):
            for k in ["authenticated", "user_id", "user_name",
                      "user_email", "familia_id", "is_admin"]:
                st.session_state.pop(k, None)
            st.session_state["authenticated"] = False
            st.session_state["page"] = "dashboard"
            st.rerun()


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------

dark_mode = st.sidebar.toggle(
    "🌙 Modo Escuro" if not st.session_state["dark_mode"] else "☀️ Modo Claro",
    value=st.session_state["dark_mode"],
)
st.session_state["dark_mode"] = dark_mode

aplicar_tema()

if not st.session_state["authenticated"]:
    pagina_login()
else:
    sidebar()
    page = st.session_state["page"]
    if page == "dashboard":
        pagina_dashboard()
    elif page == "dividas":
        pagina_dividas()
    elif page == "metas":
        pagina_metas()
