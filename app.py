import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Estrategista Imobiliário Pro", layout="wide")

# CSS para métricas e visual
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; color: #00ffcc; }
    [data-testid="stMetricLabel"] { font-size: 16px; }
    .main-description {
        background-color: rgba(0, 255, 204, 0.05);
        padding: 25px;
        border-radius: 12px;
        border-left: 6px solid #00ffcc;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO ESTRATÉGICO ---
st.markdown("""
    <div class="main-description">
        <h2 style="margin-top:0;">🏰 Estrategista Imobiliário: O Caminho Mais Curto para o seu Patrimônio</h2>
        <p style="font-size: 1.15em;">
            Financiar ou planejar? Se você hoje paga aluguel e possui capital para uma entrada, sua decisão não deve ser baseada apenas na parcela, mas no seu <b>Patrimônio Líquido Final</b> e na sua <b>Liquidez</b>.
        </p>
        <p>
            Este simulador avançado, desenvolvido para o padrão de atendimento <b>GB</b>, compara o custo real do financiamento bancário contra a estratégia de <b>Consórcio com Parcela Reduzida</b>.
        </p>
    </div>
""", unsafe_allow_html=True)

# --- SIDEBAR: PARÂMETROS PADRÃO ---
with st.sidebar:
    st.header("🏠 Parâmetros Gerais")
    v_imovel = st.number_input("Valor Atual do Imóvel (R$)", value=500000)
    val_anual = st.slider("Valorização Anual (%)", 0.0, 15.0, 6.0) / 100
    selic_anual = st.slider("Rendimento CDI (% a.a.)", 0.0, 15.0, 10.5) / 100
    
    st.header("📉 Financiamento (SAC)")
    entrada_fin = st.number_input("Entrada (R$)", value=100000)
    juros_anual = st.slider("Juros Anual (%)", 5.0, 18.0, 12.3) / 100
    prazo_fin = st.number_input("Prazo Financiamento (Meses)", value=420)
    tr_mensal = st.slider("TR Mensal (%)", 0.0, 0.5, 0.12) / 100

    st.header("🤝 Consórcio")
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

# --- CHECKLIST DE PERFIL ---
st.subheader("📝 Perfil do Investidor")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    urgencia = st.radio("Urgência para mudar?", ["Tenho pressa (D0)", "Posso aguardar o planejamento"])
with col_p2:
    foco = st.radio("Qual seu foco principal?", ["Menor custo total", "Morar hoje mesmo"])
with col_p3:
    liquidez_pref = st.radio("Prefere manter dinheiro em conta?", ["Sim, segurança acima de tudo", "Não, prefiro imobilizar"])

# --- MOTOR DE CÁLCULO ---
def rodar_simulacao():
    j_mensal = (1 + juros_anual)**(1/12) - 1
    v_mensal = (1 + val_anual)**(1/12) - 1
    s_mensal = (1 + selic_anual)**(1/12) - 1
    
    data = []
    
    # 1. FINANCIAMENTO
    s_devedor_fin = v_imovel - entrada_fin
    imovel_v_fin = v_imovel
    amort_base_fin = s_devedor_fin / prazo_fin
    custo_acum_fin = entrada_fin
    
    for m in range(1, prazo_fin + 1):
        s_devedor_fin *= (1 + tr_mensal)
        juros = s_devedor_fin * j_mensal
        parcela = amort_base_fin + juros
        imovel_v_fin *= (1 + v_mensal)
        s_devedor_fin = max(0, s_devedor_fin - amort_base_fin)
        custo_acum_fin += parcela
        data.append({"Mês": m, "Tipo": "Financiamento", "Parcela": parcela, "Desembolso": parcela, "Patrimônio": imovel_v_fin - s_devedor_fin, "Custo Acumulado": custo_acum_fin, "Liquidez": 0})

    # 2. CONSÓRCIO
    credito_nom = v_contratacao_cons
    reserva = entrada_fin - lance_proprio
    aluguel_c = aluguel_ini
    imovel_c = 0
    s_devedor_c = (credito_nom * (1 + taxa_adm + fundo_reserva)) - (lance_proprio * (1 + (taxa_adm + fundo_reserva)/prazo_cons))
    custo_acum_cons = (entrada_fin - reserva)
    dif_redutor_acum = 0
    
    for m in range(1, prazo_fin + 1):
        if m % 12 == 1 and m > 1:
            aluguel_c *= (1 + igpm_anual)
            if m <= mes_contemplacao: credito_nom *= (1 + incc_anual)

        p_cheia = (credito_nom * (1 + taxa_adm + fundo_reserva)) / prazo_cons
        p_reduzida = ((credito_nom * (1 + fundo_reserva)) * (1 - pct_redutor) + (credito_nom * taxa_adm)) / prazo_cons
        
        imovel_mercado_atual = v_imovel * (1 + v_mensal)**m
        c_aluguel = aluguel_c if m < mes_contemplacao else 0
        
        if m < mes_contemplacao:
            p_atual = p_reduzida
            dif_redutor_acum += (p_cheia - p_reduzida)
        elif m == mes_contemplacao:
            s_devedor_c += dif_redutor_acum
            v_embutido = credito_nom * pct_lance_embutido
            poder_compra = (credito_nom - v_embutido) + lance_proprio
            necessidade_complemento = max(0, imovel_mercado_atual - poder_compra)
            reserva = max(0, reserva - necessidade_complemento)
            imovel_c = imovel_mercado_atual
            s_devedor_c -= v_embutido
            p_atual = p_cheia
        else:
            meses_restantes = max(1, prazo_cons - m + 1)
            p_atual = s_devedor_c / meses_restantes if m <= prazo_cons else 0
        
        if imovel_c > 0: imovel_c *= (1 + v_mensal)
        reserva *= (1 + s_mensal)
        
        if m <= prazo_cons:
            s_devedor_c = max(0, s_devedor_c - (p_atual / (1 + taxa_adm + fundo_reserva)))
        
        custo_acum_cons += (p_atual + c_aluguel)
        data.append({"Mês": m, "Tipo": "Consórcio", "Parcela": p_atual, "Desembolso": p_atual + c_aluguel, "Patrimônio": imovel_c - s_devedor_c + reserva, "Custo Acumulado": custo_acum_cons, "Liquidez": reserva})
        
    return pd.DataFrame(data)

df = rodar_simulacao()

# --- RESULTADOS FINAIS ---
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
    fig_pat.add_trace(go.Scatter(x=sub['Mês'], y=sub['Patrimônio'], name=t, hovertemplate="Mês %{x}<br>Patrimônio: R$ %{y:,.2f}"))
fig_pat.update_layout(template="plotly_dark", hovermode="x unified")
st.plotly_chart(fig_pat, use_container_width=True)

st.divider()
st.subheader("💰 Evolução da Liquidez (Capital em Conta)")
fig_liq = go.Figure()
for t in ["Financiamento", "Consórcio"]:
    sub = df[df['Tipo']==t]
    fig_liq.add_trace(go.Scatter(x=sub['Mês'], y=sub['Liquidez'], name=f"Reserva {t}", fill='tozeroy', hovertemplate="Mês %{x}<br>Liquidez: R$ %{y:,.2f}"))
fig_liq.update_layout(template="plotly_dark", hovermode="x unified")
st.plotly_chart(fig_liq, use_container_width=True)

# --- PLANILHA (ACIMA DO PARECER) ---
st.divider()
st.subheader("📋 Memória de Cálculo Detalhada")
tipo_view = st.radio("Visualizar dados de:", ["Financiamento", "Consórcio"], horizontal=True)
st.dataframe(df[df['Tipo']==tipo_view].style.format({"Parcela": "{:.2f}", "Desembolso": "{:.2f}", "Patrimônio": "{:.2f}", "Custo Acumulado": "{:.2f}", "Liquidez": "{:.2f}"}), use_container_width=True)

# --- PARECER DO HEAD DE CRÉDITO (RESTAURADO COM VANTAGENS) ---
st.divider()
st.subheader("📑 Parecer Técnico: Head de Crédito e Consórcio")

anos_fin = prazo_fin / 12
anos_cons = prazo_cons / 12
anos_economizados = (prazo_fin - prazo_cons) / 12
dif_patrimonio = abs(res_con['Patrimônio'] - res_fin['Patrimônio'])

if res_con['Patrimônio'] > res_fin['Patrimônio']:
    st.success(f"### ✅ Recomendação: Planejamento Financeiro Estruturado (Consórcio)")
    st.write(f"""
    **Análise de Viabilidade:** A estratégia de **Consórcio com Parcela Reduzida** se provou superior neste cenário, entregando um patrimônio **R$ {dif_patrimonio:,.2f} maior**.
    
    **Por que esta é a melhor decisão?**
    1. **Ciclo de Dívida Curto:** Enquanto o financiamento prenderia seu capital por **{anos_fin:.0f} anos**, o consórcio liquida sua dívida em apenas **{anos_cons:.1f} anos**. Você ganha **{anos_economizados:.1f} anos** de liberdade financeira.
    2. **Segurança de Liquidez:** Como demonstrado no gráfico, você mantém capital investido rendendo a {selic_anual*100:.1f}% a.a., protegendo seu caixa pessoal enquanto aguarda a contemplação.
    3. **Poder de Barganha:** Com a carta contemplada, você compra como "pagador à vista", permitindo descontos que podem anular o custo da taxa de administração.
    4. **Eficiência de Taxas:** Você foge dos juros compostos bancários que incidem sobre um saldo devedor corrigido mensalmente.
    """)
else:
    st.info(f"### 🏠 Recomendação: Alavancagem Imediata (Financiamento)")
    st.write(f"""
    **Análise de Viabilidade:** Para este perfil e cenário, o **Financiamento Imobiliário** é a escolha técnica, resultando em um patrimônio **R$ {dif_patrimonio:,.2f} superior**.
    
    **Por que esta é a melhor decisão?**
    1. **Captura de Valorização (D0):** Ao assumir o imóvel hoje, você captura 100% da valorização imobiliária desde o mês 1. Em cenários de alta valorização, isso supera a economia do consórcio.
    2. **Fim do Aluguel:** A economia imediata do aluguel projetado com reajuste de {igpm_anual*100:.1f}% a.a. compensou o custo de juros.
    3. **Hospedagem Imediata:** A urgência em morar no imóvel próprio foi atendida sem depender de sorteios ou lances.
    """)
