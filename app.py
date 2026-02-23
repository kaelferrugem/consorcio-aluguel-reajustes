import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Estrategista Imobiliário Pro", layout="wide")

# --- CSS: APP DARK E IMPRESSÃO EXECUTIVA ---
st.markdown("""
    <style>
    /* 1. VISUALIZAÇÃO NO NAVEGADOR (DARK MODE) */
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

    .print-only-premissas { display: none; }

    /* 2. 🖨️ LÓGICA DE IMPRESSÃO (PDF EXECUTIVO) */
    @media print {
        body { 
            background-color: white !important; 
            color: black !important;
            margin-bottom: 80px !important; /* Margem de segurança para o rodapé */
        }
        
        .stApp { background-color: white !important; }

        /* Remove elementos desnecessários no PDF */
        .no-print, .stButton, .sidebar, [data-testid="stSidebar"], .stRadio, footer, hr, .stDownloadButton {
            display: none !important;
        }

        /* Controle de Quebra de Página */
        .chart-container, .parecer-tecnico {
            page-break-inside: avoid !important;
            margin-top: 30px;
        }

        .page-break { page-break-before: always !important; }

        .print-only-premissas {
            display: block !important;
            margin-bottom: 30px;
            padding: 25px;
            border: 1px solid #ddd;
            border-radius: 10px;
            font-size: 12px;
        }

        .main-description {
            border: 1px solid #000 !important;
            background-color: #f9f9f9 !important;
            color: black !important;
        }

        [data-testid="stMetricValue"], [data-testid="stMetricLabel"], h1, h2, h3, h4, p, span, div, b {
            color: black !important;
        }

        /* Inversão para Gráficos no PDF */
        .js-plotly-plot {
            filter: invert(1) brightness(1) contrast(1.2) !important;
        }

        .print-footer {
            display: block !important;
            position: fixed;
            bottom: 0;
            width: 100%;
            text-align: center;
            font-size: 10px;
            border-top: 1px solid #eee;
            padding-top: 10px;
            padding-bottom: 10px;
            color: #444 !important;
            background-color: white !important;
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
            Financiar ou planejar? Sua decisão não deve ser baseada apenas na parcela, mas no seu <b>Patrimônio Líquido Final</b> e na sua <b>Liquidez</b>.
        </p>
        <p>
            Comparativo entre financiamento bancário e <b>Consórcio com Parcela Reduzida</b>, considerando valorização imobiliária, inflação e custo de oportunidade.
        </p>
        <small><i>"Matemática não tem opinião. Ela tem resultados."</i></small>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR: INPUTS ---
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
    mes_contemplacao = st.slider("Mês Contemplação (Estimado)", 1, prazo_cons, 60)
    aluguel_ini = st.number_input("Aluguel Inicial (R$)", value=2500)
    incc_anual = st.slider("INCC Anual (%)", 0.0, 12.0, 6.0) / 100
    igpm_anual = st.slider("IGP-M Anual (%)", 0.0, 15.0, 8.0) / 100

if not nome_assessor or not nome_cliente:
    st.warning("⚠️ Identifique Assessor e Cliente para liberar a simulação.")
    st.stop()

# --- RELATÓRIO DE PREMISSAS (PDF) ---
st.markdown(f"""
    <div class="print-only-premissas">
        <h3 style="margin-top:0; border-bottom: 2px solid #00ffcc; padding-bottom: 5px;">📋 Memória de Dados: Premissas da Simulação</h3>
        <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
            <tr style="background-color: #f2f2f2;"><td colspan="4" style="padding: 5px;"><b>📊 Dados de Mercado</b></td></tr>
            <tr>
                <td style="padding: 5px; border: 1px solid #ddd;">Valor Imóvel:</td><td style="padding: 5px; border: 1px solid #ddd;">R$ {v_imovel:,.2f}</td>
                <td style="padding: 5px; border: 1px solid #ddd;">Valorização Imob:</td><td style="padding: 5px; border: 1px solid #ddd;">{val_anual*100:.1f}% a.a.</td>
            </tr>
            <tr>
                <td style="padding: 5px; border: 1px solid #ddd;">Rendimento CDI:</td><td style="padding: 5px; border: 1px solid #ddd;">{selic_anual*100:.1f}% a.a.</td>
                <td style="padding: 5px; border: 1px solid #ddd;">Aluguel Inicial:</td><td style="padding: 5px; border: 1px solid #ddd;">R$ {aluguel_ini:,.2f}</td>
            </tr>
            <tr style="background-color: #f2f2f2;"><td colspan="4" style="padding: 5px;"><b>📉 Financiamento Bancário (SAC)</b></td></tr>
            <tr>
                <td style="padding: 5px; border: 1px solid #ddd;">Entrada Cash:</td><td style="padding: 5px; border: 1px solid #ddd;">R$ {entrada_fin:,.2f}</td>
                <td style="padding: 5px; border: 1px solid #ddd;">Juros:</td><td style="padding: 5px; border: 1px solid #ddd;">{juros_anual*100:.1f}% a.a.</td>
            </tr>
            <tr style="background-color: #f2f2f2;"><td colspan="4" style="padding: 5px;"><b>🤝 Estratégia de Consórcio</b></td></tr>
            <tr>
                <td style="padding: 5px; border: 1px solid #ddd;">Valor da Carta:</td><td style="padding: 5px; border: 1px solid #ddd;">R$ {v_contratacao_cons:,.2f}</td>
                <td style="padding: 5px; border: 1px solid #ddd;">Redutor Parcela:</td><td style="padding: 5px; border: 1px solid #ddd;">{pct_redutor*100:.0f}%</td>
            </tr>
            <tr>
                <td style="padding: 5px; border: 1px solid #ddd;">Lance Embutido:</td><td style="padding: 5px; border: 1px solid #ddd;">{pct_lance_embutido*100:.0f}%</td>
                <td style="padding: 5px; border: 1px solid #ddd;">Contemplação:</td><td style="padding: 5px; border: 1px solid #ddd;">Mês {mes_contemplacao}</td>
            </tr>
        </table>
    </div>
""", unsafe_allow_html=True)

# --- MOTOR DE CÁLCULO ---
def rodar_simulacao():
    j_mensal = (1 + juros_anual)**(1/12) - 1
    v_mensal = (1 + val_anual)**(1/12) - 1
    s_mensal = (1 + selic_anual)**(1/12) - 1
    data = []
    
    # 1. FINANCIAMENTO
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

    # 2. CONSÓRCIO
    cred_n = v_contratacao_cons
    taxa_total_anual = (taxa_adm + fundo_reserva)
    reserva = entrada_fin - lance_proprio
    aluguel_c = aluguel_ini
    s_devedor_c = (cred_n * (1 + taxa_total_anual)) - (lance_proprio * (1 + taxa_total_anual/prazo_cons))
    custo_c = (entrada_fin - reserva)
    dif_red_acum = 0
    imovel_c = 0
    p_at = 0
    pct_prop = 0
    p_pos_contemp = 0

    for m in range(1, prazo_fin + 1):
        if m % 12 == 1 and m > 1:
            aluguel_c *= (1 + igpm_anual)
            f_incc = (1 + incc_anual)
            cred_n *= f_incc
            s_devedor_c *= f_incc
            dif_red_acum *= f_incc
            if p_pos_contemp > 0: p_pos_contemp *= f_incc

        im_mercado = v_imovel * (1 + v_mensal)**m
        
        if m < mes_contemplacao:
            p_ch = (cred_n * (1 + taxa_total_anual)) / prazo_cons
            p_re = ((cred_n * (1 + fundo_reserva)) * (1 - pct_redutor) + (cred_n * taxa_adm)) / prazo_cons
            p_at = p_re
            dif_red_acum += (p_ch - p_re)
            amort_ref = p_ch
            al_mes = aluguel_c
        elif m == mes_contemplacao:
            p_ch = (cred_n * (1 + taxa_total_anual)) / prazo_cons
            p_re = ((cred_n * (1 + fundo_reserva)) * (1 - pct_redutor) + (cred_n * taxa_adm)) / prazo_cons
            p_at = p_re
            dif_red_acum += (p_ch - p_re)
            amort_ref = p_ch
            al_mes = aluguel_c
            v_em = cred_n * pct_lance_embutido
            p_compra = (cred_n - v_em) + lance_proprio
            imovel_c = min(im_mercado, p_compra + reserva)
            pct_prop = imovel_c / im_mercado
            reserva = max(0, reserva - max(0, im_mercado - p_compra))
        else: # m > mes_contemplacao
            if p_pos_contemp == 0:
                v_em = cred_n * pct_lance_embutido
                s_devedor_c = (s_devedor_c + dif_red_acum) - v_em
                dif_red_acum = 0
                restantes = max(1, prazo_cons - (m - 1))
                p_pos_contemp = s_devedor_c / restantes
            
            p_at = p_pos_contemp
            amort_ref = p_at
            if m > prazo_cons: p_at = amort_ref = 0
            al_mes = 0
            imovel_c = im_mercado * pct_prop

        reserva *= (1 + s_mensal)
        if m <= prazo_cons: s_devedor_c = max(0, s_devedor_c - amort_ref)
        custo_c += (p_at + al_mes)
        data.append({"Mês": m, "Tipo": "Consórcio", "Parcela": p_at, "Desembolso": p_at + al_mes, "Patrimônio": imovel_c - s_devedor_c + reserva, "Custo Acumulado": custo_c, "Liquidez": reserva})
    return pd.DataFrame(data)

df = rodar_simulacao()

# --- EXIBIÇÃO NO BROWSER ---
st.info(f"📋 Simulação: **{nome_cliente}** | Assessor: **{nome_assessor}**")
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

with st.container():
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    fig_pat = go.Figure()
    for t in ["Financiamento", "Consórcio"]:
        sub = df[df['Tipo']==t]
        fig_pat.add_trace(go.Scatter(x=sub['Mês'], y=sub['Patrimônio'], name=t))
    fig_pat.update_layout(template="plotly_dark", hovermode="x unified")
    st.plotly_chart(fig_pat, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Quebra de página estratégica para o PDF
st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)

# --- PARECER TÉCNICO ---
st.subheader("📑 Parecer Técnico: Especialista em Crédito")
with st.container():
    st.markdown('<div class="parecer-tecnico">', unsafe_allow_html=True)
    dif_patrimonio = abs(res_con['Patrimônio'] - res_fin['Patrimônio'])
    if res_con['Patrimônio'] > res_fin['Patrimônio']:
        st.success(f"### ✅ Recomendação: Consórcio")
        st.write(f"A estratégia estruturada de consórcio entrega um patrimônio **R$ {dif_patrimonio:,.2f} maior**.")
        st.write("1. Ciclo de dívida reduzido | 2. Segurança de liquidez | 3. Poder de barganha à vista.")
    else:
        st.info(f"### 🏠 Recomendação: Financiamento")
        st.write(f"O financiamento bancário resultou em um patrimônio líquido **R$ {dif_patrimonio:,.2f} superior**.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- MEMÓRIA DE CÁLCULO (Oculta no PDF) ---
st.markdown('<div class="no-print">', unsafe_allow_html=True)
st.divider()
st.subheader("📋 Memória de Cálculo Detalhada (Consulta Online)")
v_tipo = st.radio("Dados:", ["Financiamento", "Consórcio"], horizontal=True)
st.dataframe(df[df['Tipo']==v_tipo].style.format("{:.2f}"), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- BOTÃO DE IMPRESSÃO ---
st.divider()
if st.button("🖨️ Gerar Relatório PDF"):
    js_print = f"""
    <script>
        const originalTitle = window.parent.document.title;
        window.parent.document.title = "Simulação - {nome_cliente}";
        window.parent.print();
        setTimeout(() => {{ window.parent.document.title = originalTitle; }}, 2000);
    </script>
    """
    components.html(js_print, height=0)

# --- RODAPÉ ---
st.markdown(f"""
    <div class="print-footer">
        Relatório Estratégico de Patrimônio - Cliente: {nome_cliente} | Assessor: {nome_assessor}<br>
        <b>Responsável Técnico:</b> Especialista em Crédito e Consórcio
    </div>
""", unsafe_allow_html=True)
