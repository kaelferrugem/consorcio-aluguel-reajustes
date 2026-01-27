import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Estrategista Imobiliário Pro", layout="wide")

# --- CSS: APP DARK E IMPRESSÃO COM RESUMO DE PREMISSAS ---
st.markdown("""
    <style>
    /* 1. VISUALIZAÇÃO NO NAVEGADOR */
    [data-testid="stMetricValue"] { font-size: 24px; color: #00ffcc; }
    [data-testid="stMetricLabel"] { font-size: 16px; }
    
    .main-description {
        background-color: rgba(0, 255, 204, 0.05);
        padding: 25px;
        border-radius: 12px;
        border-left: 6px solid #00ffcc;
        margin-bottom: 30px;
    }

    .disclaimer {
        font-size: 11px;
        color: #888;
        margin-top: 40px;
        text-align: justify;
    }

    /* Oculta a seção de premissas no navegador */
    .print-only-premissas {
        display: none;
    }

    /* 2. 🖨️ LÓGICA DE IMPRESSÃO (PDF) */
    @media print {
        body, .stApp, .main, .main-description, [data-testid="metric-container"], .stMetric {
            background-color: white !important;
            color: black !important;
        }
        
        /* Torna a seção de premissas visível apenas no papel */
        .print-only-premissas {
            display: block !important;
            margin-bottom: 20px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 13px;
        }

        .main-description {
            border: 1px solid #000 !important;
            background-color: #f9f9f9 !important;
            color: black !important;
        }

        [data-testid="stMetricValue"], [data-testid="stMetricLabel"], h1, h2, h3, h4, p, span, div, b {
            color: black !important;
        }

        [data-testid="stDataFrame"], [data-testid="stTable"], .js-plotly-plot {
            filter: invert(1) brightness(1) contrast(1.2) !important;
        }

        .stButton, .sidebar, [data-testid="stSidebar"], .stRadio, footer, hr, .stDownloadButton {
            display: none !important;
        }

        .print-footer {
            display: block !important;
            position: fixed;
            bottom: 0;
            width: 100%;
            text-align: center;
            font-size: 10px;
            border-top: 0.5px solid #eee;
            padding-top: 5px;
            color: #555 !important;
        }
    }
    
    .print-footer { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO ESTRATÉGICO ---
st.markdown("""
    <div class="main-description">
        <h2 style="margin-top:0;">🏰 Estrategista Imobiliário: O Caminho Mais Curto para o seu Patrimônio</h2>
        <p style="font-size: 1.15em;">
            Financiar ou planejar? Se você hoje paga aluguel e possui capital para uma entrada, sua decision não deve ser baseada apenas na parcela, mas no seu <b>Patrimônio Líquido Final</b> e na sua <b>Liquidez</b>.
        </p>
        <p>
            Este simulador utiliza algoritmos de mercado para comparar o custo real do financiamento bancário contra a estratégia de <b>Consórcio com Parcela Reduzida</b>, considerando valorização imobiliária, inflação (INCC/IGP-M) e custo de oportunidade.
        </p>
        <small><i>"Matemática não tem opinião. Ela tem resultados."</i></small>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Identificação Obrigatória")
    nome_assessor = st.text_input("Nome do Assessor:")
    nome_cliente = st.text_input("Nome do Cliente:")
    st.divider()
    st.header("🏠 Parâmetros Gerais")
    v_imovel = st.number_input("Valor Atual do Imóvel (R$)", value=500000)
    val_anual = st.slider("Valorização Anual (%)", 0.0, 15.0, 6.0) / 100
    selic_anual = st.slider("Rendimento CDI (% a.a.)", 0.0, 15.0, 10.5) / 100
    st.header("📉 Financiamento (SAC)")
    entrada_fin = st.number_input("Entrada (R$)", value=100000)
    juros_anual = st.slider("Juros Anual (%)", 5.0, 18.0, 12.3) / 100
    prazo_fin = st.number_input("Prazo Financiamento (Meses)", value=420)
    tr_mensal = st.slider("TR Mensal (%)", 0.0, 0.5, 0.12) / 100
    st.header("🤝 Consórcio (XP/Embracon)")
    v_contratacao_cons = st.number_input("Valor de Contratação (R$)", value=500000)
    taxa_adm = st.slider("Taxa de Adm. Total (%)", 10.0, 30.0, 20.0) / 100
    fundo_reserva = st.slider("Fundo de Reserva (%)", 0.0, 5.0, 2.0) / 100
    prazo_cons = st.number_input("Prazo Consórcio (Meses)", value=240)
    lance_proprio = st.number_input("Lance Próprio (R$)", value=0)
    pct_lance_embutido = st.slider("% Lance Embutido", 0, 30, 25) / 100
    pct_redutor = st.slider("% Redutor de Parcela", 0, 50, 50) / 100
    mes_contemplacao = st.slider("Mês Contemplação (Estimado)", 1, prazo_cons, 120)
    aluguel_ini = st.number_input("Aluguel Inicial (R$)", value=2500)
    incc_anual = st.slider("INCC Anual (%)", 0.0, 12.0, 6.0) / 100
    igpm_anual = st.slider("IGP-M Anual (%)", 0.0, 15.0, 8.0) / 100

if not nome_assessor or not nome_cliente:
    st.warning("⚠️ **Acesso Restrito:** Identifique Assessor e Cliente na lateral.")
    st.stop()

# --- SEÇÃO EXCLUSIVA DE PREMISSAS PARA O PDF (ATUALIZADA) ---
st.markdown(f"""
    <div class="print-only-premissas">
        <h3 style="margin-top:0; color: #333; border-bottom: 2px solid #00ffcc; padding-bottom: 5px;">📋 Detalhamento das Premissas Simuladas</h3>
        <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>Valor do Imóvel:</b> R$ {v_imovel:,.2f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>Valor do Consórcio:</b> R$ {v_contratacao_cons:,.2f}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>Aluguel Inicial:</b> R$ {aluguel_ini:,.2f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>Valorização Imobiliária:</b> {val_anual*100:.1f}% a.a.</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>Contemplação Estimada:</b> Mês {mes_contemplacao}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>Rendimento CDI (Liquidez):</b> {selic_anual*100:.1f}% a.a.</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>INCC (Reajuste Anual):</b> {incc_anual*100:.1f}%</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;"><b>IGP-M (Reajuste Aluguel):</b> {igpm_anual*100:.1f}%</td>
            </tr>
            <tr>
                <td colspan="2" style="padding: 15px 0 5px 0; border-bottom: 1px solid #eee;"><b>⚙️ Parâmetros Comparativos:</b></td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Financiamento:</b> {prazo_fin} meses | Juros: {juros_anual*100:.1f}% a.a.</td>
                <td style="padding: 8px;"><b>Consórcio:</b> {prazo_cons} meses | Taxa Total: {taxa_adm*100:.1f}%</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Entrada (Cash):</b> R$ {entrada_fin:,.2f}</td>
                <td style="padding: 8px;"><b>Lance Embutido:</b> {pct_lance_embutido*100:.0f}% | Redutor: {pct_redutor*100:.0f}%</td>
            </tr>
        </table>
    </div>
""", unsafe_allow_html=True)

# --- MOTOR DE CÁLCULO (INALTERADO) ---
def rodar_simulacao():
    j_mensal = (1 + juros_anual)**(1/12) - 1
    v_mensal = (1 + val_anual)**(1/12) - 1
    s_mensal = (1 + selic_anual)**(1/12) - 1
    data = []
    
    s_devedor_f = v_imovel - entrada_fin
    imovel_v_f = v_imovel
    amort_f = s_devedor_f / prazo_fin
    custo_f = entrada_fin
    for m in range(1, prazo_fin + 1):
        s_devedor_f *= (1 + tr_mensal)
        parcela = amort_f + (s_devedor_f * j_mensal)
        imovel_v_f *= (1 + v_mensal)
        s_devedor_f = max(0, s_devedor_f - amort_f)
        custo_f += parcela
        data.append({"Mês": m, "Tipo": "Financiamento", "Parcela": parcela, "Desembolso": parcela, "Patrimônio": imovel_v_f - s_devedor_f, "Custo Acumulado": custo_f, "Liquidez": 0})

    cred_n = v_contratacao_cons
    taxa_total_anual = (taxa_adm + fundo_reserva)
    reserva = entrada_fin - lance_proprio
    aluguel_c = aluguel_ini
    s_devedor_c = (cred_n * (1 + taxa_total_anual)) - (lance_proprio * (1 + taxa_total_anual/prazo_cons))
    custo_c = (entrada_fin - reserva)
    dif_red_acum = 0
    imovel_c = 0
    p_at = 0
    pct_propriedade = 0

    for m in range(1, prazo_fin + 1):
        if m % 12 == 1 and m > 1:
            aluguel_c *= (1 + igpm_anual)
            fator_incc = (1 + incc_anual)
            cred_n *= fator_incc
            s_devedor_c *= fator_incc
            if p_at > 0: p_at *= fator_incc

        imovel_mercado = v_imovel * (1 + v_mensal)**m
        
        if m < mes_contemplacao:
            p_ch = (cred_n * (1 + taxa_total_anual)) / prazo_cons
            p_re = ((cred_n * (1 + fundo_reserva)) * (1 - pct_redutor) + (cred_n * taxa_adm)) / prazo_cons
            p_at = p_re
            dif_red_acum += (p_ch - p_re)
            aluguel_at = aluguel_c
        elif m == mes_contemplacao:
            s_devedor_c += dif_red_acum
            v_em = cred_n * pct_lance_embutido
            s_devedor_c -= v_em
            poder_compra = (cred_n - v_em) + lance_proprio
            imovel_c = min(imovel_mercado, poder_compra + reserva)
            pct_propriedade = imovel_c / imovel_mercado
            reserva = max(0, reserva - max(0, imovel_mercado - poder_compra))
            meses_restantes = max(1, prazo_cons - m + 1)
            p_at = s_devedor_c / meses_restantes
            aluguel_at = 0
        else:
            imovel_c = imovel_mercado * pct_propriedade
            if m > prazo_cons: p_at = 0
            aluguel_at = 0

        reserva *= (1 + s_mensal)
        if m <= prazo_cons: s_devedor_c = max(0, s_devedor_c - p_at)
        custo_c += (p_at + aluguel_at)
        data.append({"Mês": m, "Tipo": "Consórcio", "Parcela": p_at, "Desembolso": p_at + aluguel_at, "Patrimônio": imovel_c - s_devedor_c + reserva, "Custo Acumulado": custo_c, "Liquidez": reserva})
    return pd.DataFrame(data)

df = rodar_simulacao()

# --- EXIBIÇÃO ---
st.info(f"📋 **Simulação preparada para:** {nome_cliente} | **Responsável:** {nome_assessor}")
res_fin = df[(df['Tipo']=="Financiamento") & (df['Mês']==prazo_fin)].iloc[0]
res_con = df[(df['Tipo']=="Consórcio") & (df['Mês']==prazo_fin)].iloc[0]

st.markdown("### 🎯 Comparativo Final")
c1, c2 = st.columns(2)
with c1:
    st.metric("Patrimônio Financiamento", f"R$ {res_fin['Patrimônio']:,.2f}")
    st.metric("Custo Total Financiamento", f"R$ {res_fin['Custo Acumulado']:,.2f}")
with c2:
    st.metric("Patrimônio Consórcio", f"R$ {res_con['Patrimônio']:,.2f}")
    st.metric("Custo Total Consórcio + Aluguel", f"R$ {res_con['Custo Acumulado']:,.2f}")

# --- GRÁFICOS ---
st.divider()
st.subheader("📊 Evolução do Patrimônio Líquido")
fig_pat = go.Figure()
for t in ["Financiamento", "Consórcio"]:
    sub = df[df['Tipo']==t]
    fig_pat.add_trace(go.Scatter(x=sub['Mês'], y=sub['Patrimônio'], name=t))
fig_pat.update_layout(template="plotly_dark", hovermode="x unified")
st.plotly_chart(fig_pat, use_container_width=True)

st.divider()
st.subheader("💰 Evolução da Liquidez (Capital em Conta)")
fig_liq = go.Figure()
for t in ["Financiamento", "Consórcio"]:
    sub = df[df['Tipo']==t]
    fig_liq.add_trace(go.Scatter(x=sub['Mês'], y=sub['Liquidez'], name=f"Reserva {t}", fill='tozeroy'))
fig_liq.update_layout(template="plotly_dark", hovermode="x unified")
st.plotly_chart(fig_liq, use_container_width=True)

# --- PLANILHA ---
st.divider()
st.subheader("📋 Memória de Cálculo Detalhada")
tipo_view = st.radio("Visualizar dados de:", ["Financiamento", "Consórcio"], horizontal=True)
st.dataframe(df[df['Tipo']==tipo_view].style.format({"Parcela": "{:.2f}", "Desembolso": "{:.2f}", "Patrimônio": "{:.2f}", "Custo Acumulado": "{:.2f}", "Liquidez": "{:.2f}"}), use_container_width=True)

# --- PARECER TÉCNICO ---
st.divider()
st.subheader("📑 Parecer Técnico: Especialista em Crédito")
anos_fin, anos_cons = prazo_fin / 12, prazo_cons / 12
anos_economizados = (prazo_fin - prazo_cons) / 12
dif_patrimonio = abs(res_con['Patrimônio'] - res_fin['Patrimônio'])

if res_con['Patrimônio'] > res_fin['Patrimônio']:
    st.success(f"### ✅ Recomendação: Planejamento Financeiro Estruturado (Consórcio)")
    st.write(f"""
    **Análise de Viabilidade:** A estratégia de **Consórcio com Parcela Reduzida** se provou superior neste cenário, entregando um patrimônio **R$ {dif_patrimonio:,.2f} maior**.
    
    1. **Ciclo de Dívida Curto:** Enquanto o financiamento prenderia seu capital por **{anos_fin:.0f} anos**, o consórcio liquida em **{anos_cons:.1f} anos**. Você ganha **{anos_economizados:.1f} anos** de liberdade financeira.
    2. **Segurança de Liquidez:** Você mantém capital investido rendendo a **{selic_anual*100:.1f}% a.a.**, protegendo seu caixa pessoal.
    3. **Poder de Barganha:** Com a carta contemplada, você compra como "pagador à vista".
    4. **Eficiência de Taxas:** Você foge dos juros compostos bancários incidindo sobre saldo devedor corrigido pela TR.
    """)
else:
    st.info(f"### 🏠 Recomendação: Alavancagem Imediata (Financiamento)")
    st.write(f"**Análise de Viabilidade:** Para este perfil e cenário, o **Financiamento Imobiliário** resultou em um patrimônio **R$ {dif_patrimonio:,.2f} superior**.")

# --- DISCLAIMER ---
st.markdown("""
    <div class="disclaimer">
        <b>AVISO LEGAL:</b> Este simulador é uma ferramenta de apoio à decisão baseada em projeções matemáticas e premissas econômicas (INCC, IGP-M, TR e Taxas de Juros). 
        A contratação de qualquer produto financeiro deve ser precedida de análise cuidadosa dos contratos. Esta simulação não constitui garantia de crédito ou contemplação.
    </div>
""", unsafe_allow_html=True)

st.divider()
if st.button("🖨️ Gerar Resumo para Impressão"):
    components.html("""<script>window.parent.print();</script>""", height=0)

# --- RODAPÉ DE IMPRESSÃO ---
st.markdown(f"""
    <div class="print-footer">
        Consultoria Estratégica de Patrimônio - Cliente: {nome_cliente} | Assessor: {nome_assessor}<br>
        <b>Responsável Técnico:</b> Especialista em Crédito e Consórcio
    </div>
""", unsafe_allow_html=True)
