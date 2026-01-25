import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Simulador Imobiliário Pro - Parcela Reduzida Real", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 22px; color: #00ffcc; }
    [data-testid="stMetricLabel"] { font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Dashboard de Decisão: Financiamento vs. Consórcio")

# --- SIDEBAR ---
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

    st.header("🤝 Consórcio")
    v_contratacao_cons = st.number_input("Valor de Contratação (R$)", value=500000)
    taxa_adm = st.slider("Taxa de Adm. Total (%)", 10.0, 30.0, 20.0) / 100
    fundo_reserva = st.slider("Fundo de Reserva (%)", 0.0, 5.0, 2.0) / 100
    prazo_cons = st.number_input("Prazo Consórcio", value=240)
    lance_proprio = st.number_input("Lance Próprio (R$)", value=100000)
    pct_lance_embutido = st.slider("% Lance Embutido (do crédito)", 0, 30, 25) / 100
    
    # VARIÁVEL DE PARCELA REDUZIDA (Ajustada para Fundo Comum)
    pct_redutor_fundo_comum = st.slider("% Redutor do Fundo Comum", 0, 50, 50) / 100
    
    mes_contemplacao = st.slider("Mês Contemplação", 1, prazo_cons, 12)
    aluguel_ini = st.number_input("Aluguel Inicial (R$)", value=2500)
    incc_anual = st.slider("INCC Anual (%)", 0.0, 12.0, 6.0) / 100
    igpm_anual = st.slider("IGP-M Anual (%)", 0.0, 15.0, 4.5) / 100

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
        data.append({"Mês": m, "Tipo": "Financiamento", "Parcela": parcela, "Desembolso": parcela, "Patrimônio": imovel_v_fin - s_devedor_fin, "Custo Acumulado": custo_acum_fin})

    # 2. CONSÓRCIO
    credito_nom = v_contratacao_cons
    reserva = entrada_fin - lance_proprio
    aluguel_c = aluguel_ini
    imovel_c = 0
    s_devedor_c = (credito_nom * (1 + taxa_adm + fundo_reserva)) - (lance_proprio * (1 + (taxa_adm + fundo_reserva)/prazo_cons))
    
    custo_acum_cons = (entrada_fin - reserva)
    fundo_comum_nao_pago_acumulado = 0
    
    for m in range(1, prazo_fin + 1):
        if m % 12 == 1 and m > 1:
            aluguel_c *= (1 + igpm_anual)
            if m <= mes_contemplacao: credito_nom *= (1 + incc_anual)

        # Cálculo das partes da parcela
        p_fundo_comum_cheia = credito_nom / prazo_cons
        p_taxas = (credito_nom * (taxa_adm + fundo_reserva)) / prazo_cons
        
        imovel_mercado_atual = v_imovel * (1 + v_mensal)**m
        c_aluguel = aluguel_c if m < mes_contemplacao else 0
        
        if m < mes_contemplacao:
            # Redução APENAS no fundo comum
            p_fundo_comum_atual = p_fundo_comum_cheia * (1 - pct_redutor_fundo_comum)
            fundo_comum_nao_pago_acumulado += (p_fundo_comum_cheia - p_fundo_comum_atual)
            p_atual = p_fundo_comum_atual + p_taxas
        elif m == mes_contemplacao:
            # Momento da Contemplação: Acerta a dívida do redutor
            s_devedor_c += fundo_comum_nao_pago_acumulado
            v_embutido = credito_nom * pct_lance_embutido
            liquido_disponivel = credito_nom - v_embutido
            poder_compra = liquido_disponivel + lance_proprio
            
            necessidade_complemento = max(0, imovel_mercado_atual - poder_compra)
            reserva = max(0, reserva - necessidade_complemento)
            
            imovel_c = imovel_mercado_atual
            s_devedor_c -= v_embutido
            p_atual = p_fundo_comum_cheia + p_taxas # Volta para cheia
        else:
            # Recálculo pós-contemplação
            meses_restantes = max(1, prazo_cons - m + 1)
            p_atual = s_devedor_c / meses_restantes if m <= prazo_cons else 0
        
        if imovel_c > 0: imovel_c *= (1 + v_mensal)
        reserva *= (1 + s_mensal)
        
        if m <= prazo_cons:
            s_devedor_c = max(0, s_devedor_c - (p_atual / (1 + taxa_adm + fundo_reserva)))
        
        desembolso_mes = p_atual + c_aluguel
        custo_acum_cons += desembolso_mes
        
        data.append({
            "Mês": m, "Tipo": "Consórcio", "Parcela": p_atual, "Desembolso": desembolso_mes,
            "Patrimônio": imovel_c - s_devedor_c + reserva, "Custo Acumulado": custo_acum_cons
        })
        
    return pd.DataFrame(data)

df = rodar_simulacao()

# --- EXIBIÇÃO ---
res_fin = df[(df['Tipo']=="Financiamento") & (df['Mês']==prazo_fin)].iloc[0]
res_con = df[(df['Tipo']=="Consórcio") & (df['Mês']==prazo_fin)].iloc[0]

st.markdown("### 🎯 Comparativo Final Detalhado")

st.markdown("#### 💎 Patrimônio Líquido Final")
col1, col2 = st.columns(2)
with col1: st.metric("Patrimônio com Financiamento", f"R$ {res_fin['Patrimônio']:,.2f}")
with col2: st.metric("Patrimônio com Consórcio", f"R$ {res_con['Patrimônio']:,.2f}")

st.markdown("#### 💸 Custo Total da Jornada")
col3, col4 = st.columns(2)
with col3: st.metric("Custo Total Financiamento", f"R$ {res_fin['Custo Acumulado']:,.2f}")
with col4: st.metric("Custo Total Consórcio + Aluguel", f"R$ {res_con['Custo Acumulado']:,.2f}")

st.divider()
st.subheader("📊 Evolução Patrimonial")
fig_pat = go.Figure()
for t in ["Financiamento", "Consórcio"]:
    sub = df[df['Tipo']==t]
    fig_pat.add_trace(go.Scatter(x=sub['Mês'], y=sub['Patrimônio'], name=t))
fig_pat.update_layout(template="plotly_dark")
st.plotly_chart(fig_pat, use_container_width=True)

st.divider()
st.subheader("📋 Memória de Cálculo Detalhada")
tipo_view = st.radio("Selecione a modalidade:", ["Financiamento", "Consórcio"], horizontal=True)
st.dataframe(df[df['Tipo']==tipo_view].style.format({"Parcela": "{:.2f}", "Desembolso": "{:.2f}", "Patrimônio": "{:.2f}", "Custo Acumulado": "{:.2f}"}), use_container_width=True)
