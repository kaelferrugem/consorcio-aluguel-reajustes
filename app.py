import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Simulador Imobiliário Pro v3.0", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 22px; color: #00ffcc; }
    [data-testid="stMetricLabel"] { font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# --- TOPO DO APP: DESCRIÇÃO ESTRATÉGICA ---
st.markdown("""
    <div style="background-color: rgba(0, 255, 204, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #00ffcc;">
        <h3 style="margin-top:0;">🏰 Estrategista Imobiliário: O Caminho Mais Curto para o seu Patrimônio</h3>
        <p style="font-size: 1.1em;">
            Financiar ou planejar? Se você hoje paga aluguel e possui capital para uma entrada, sua decisão deve ser baseada no seu <b>Patrimônio Líquido Final</b> e na sua <b>Liquidez</b>. 
        </p>
        <p>
            Este simulador compara o custo real do financiamento bancário contra a estratégia de <b>Consórcio com Parcela Reduzida</b>, considerando valorização imobiliária e inflação.
        </p>
    </div>
    <br>
""", unsafe_allow_html=True)

# --- SIDEBAR: INPUTS TÉCNICOS ---
with st.sidebar:
    st.header("🏠 Parâmetros Gerais")
    v_imovel = st.number_input("Valor Atual do Imóvel (R$)", value=500000)
    val_anual = st.slider("Valorização Anual (%)", 0.0, 15.0, 6.0) / 100
    selic_anual = st.slider("Rendimento Reserva (% a.a.)", 0.0, 15.0, 10.0) / 100
    
    st.header("📉 Financiamento (SAC)")
    entrada_fin = st.number_input("Entrada (R$)", value=100000)
    juros_anual = st.slider("Juros Anual (%)", 5.0, 15.0, 10.5) / 100
    prazo_fin = st.number_input("Prazo Financiamento (Meses)", value=360)
    tr_mensal = st.slider("TR Mensal (%)", 0.0, 0.5, 0.08) / 100

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
    igpm_anual = st.slider("IGP-M Anual (%)", 0.0, 15.0, 4.5) / 100

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
        # No financiamento a liquidez é 0 pois a entrada foi gasta
        data.append({"Mês": m, "Tipo": "Financiamento", "Parcela": parcela, "Patrimônio": imovel_v_fin - s_devedor_fin, "Custo Acumulado": custo_acum_fin, "Liquidez": 0})

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
        
        data.append({
            "Mês": m, "Tipo": "Consórcio", "Parcela": p_atual, "Desembolso": p_atual + c_aluguel,
            "Patrimônio": imovel_c - s_devedor_c + reserva, "Custo Acumulado": custo_acum_cons, "Liquidez": reserva
        })
        
    return pd.DataFrame(data)

df = rodar_simulacao()

# --- EXIBIÇÃO ---
res_fin = df[(df['Tipo']=="Financiamento") & (df['Mês']==prazo_fin)].iloc[0]
res_con = df[(df['Tipo']=="Consórcio") & (df['Mês']==prazo_fin)].iloc[0]

st.markdown("### 🎯 Comparativo Final Detalhado")
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Patrimônio Financiamento", f"R$ {res_fin['Patrimônio']:,.2f}")
with c2: st.metric("Custo Financiamento", f"R$ {res_fin['Custo Acumulado']:,.2f}")
with c3: st.metric("Patrimônio Consórcio", f"R$ {res_con['Patrimônio']:,.2f}")
with c4: st.metric("Custo Consórcio", f"R$ {res_con['Custo Acumulado']:,.2f}")

st.divider()
tab_pat, tab_liq = st.tabs(["📊 Evolução Patrimonial", "💰 Liquidez (Dinheiro em Conta)"])

with tab_pat:
    fig_pat = go.Figure()
    for t in ["Financiamento", "Consórcio"]:
        sub = df[df['Tipo']==t]
        fig_pat.add_trace(go.Scatter(x=sub['Mês'], y=sub['Patrimônio'], name=t))
    fig_pat.update_layout(title="Quem enriquece mais o cliente?", template="plotly_dark")
    st.plotly_chart(fig_pat, use_container_width=True)

with tab_liq:
    fig_liq = go.Figure()
    for t in ["Financiamento", "Consórcio"]:
        sub = df[df['Tipo']==t]
        fig_liq.add_trace(go.Scatter(x=sub['Mês'], y=sub['Liquidez'], name=f"Reserva {t}", fill='tozeroy'))
    fig_liq.update_layout(title="Dinheiro Disponível (Liquidez) ao longo do tempo", template="plotly_dark")
    st.plotly_chart(fig_liq, use_container_width=True)
    st.info("💡 A Liquidez no Consórcio representa o capital que você mantém rendendo enquanto aguarda a contemplação, protegendo seu caixa pessoal.")

# --- PARECER TÉCNICO DINÂMICO ---
st.divider()
st.subheader("📑 Parecer do Head de Crédito e Consórcio")

anos_fin = prazo_fin / 12
anos_cons = prazo_cons / 12
anos_economizados = (prazo_fin - prazo_cons) / 12

if res_con['Patrimônio'] > res_fin['Patrimônio']:
    st.success(f"### ✅ Recomendação: Estratégia de Planejamento (Consórcio)")
    st.write(f"""
    **Análise Técnica:** Com base na sua preferência por **{liquidez_pref.lower()}** e no foco em **{foco.lower()}**, o consórcio é a ferramenta ideal.
    
    1. **Ciclo de Dívida:** Você liquida sua dívida em apenas **{anos_cons:.1f} anos**, ganhando **{anos_economizados:.1f} anos** de liberdade em relação a quem financiou em {anos_fin:.0f} anos.
    2. **Segurança de Caixa:** Como mostra o gráfico de **Liquidez**, você mantém capital investido rendendo a {selic_anual*100:.1f}% a.a., algo impossível no financiamento SAC onde a entrada é imobilizada no D0.
    3. **Vantagem Financeira:** Seu patrimônio final será **R$ {res_con['Patrimônio'] - res_fin['Patrimônio']:,.2f} maior**.
    """)
else:
    st.info(f"### 🏠 Recomendação: Alavancagem Imediata (Financiamento)")
    st.write(f"""
    **Análise Técnica:** Como sua prioridade é **{urgencia.lower()}**, o financiamento é o caminho, apesar do custo maior.
    
    1. **Valorização D0:** Você trava o preço do imóvel hoje. Em {anos_fin:.0f} anos, a valorização capturada superou a economia de taxas do consórcio.
    2. **Custo de Oportunidade:** O custo do aluguel projetado foi o principal detrator da estratégia de planejamento neste cenário.
    """)
