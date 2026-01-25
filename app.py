import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Simulador Imobiliário Pro", layout="wide")

# CSS para garantir visibilidade e estilo dos cards
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
    # VARIÁVEL: VALOR DE CONTRATAÇÃO (Pode ser diferente do valor do imóvel)
    v_contratacao_cons = st.number_input("Valor de Contratação (R$)", value=500000)
    
    taxa_adm = st.slider("Taxa de Adm. Total (%)", 10.0, 25.0, 15.0) / 100
    prazo_cons = st.number_input("Prazo Consórcio", value=200)
    lance_proprio = st.number_input("Lance Próprio (R$)", value=100000)
    pct_lance_embutido = st.slider("% Lance Embutido (do crédito)", 0, 30, 20) / 100
    
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
    s_devedor = v_imovel - entrada_fin
    imovel_v = v_imovel
    amort_base = s_devedor / prazo_fin
    custo_acum_fin = entrada_fin
    
    for m in range(1, prazo_fin + 1):
        s_devedor *= (1 + tr_mensal)
        juros = s_devedor * j_mensal
        parcela = amort_base + juros
        imovel_v *= (1 + v_mensal)
        s_devedor = max(0, s_devedor - amort_base)
        custo_acum_fin += parcela
        data.append({
            "Mês": m, "Tipo": "Financiamento", 
            "Parcela": parcela, "Desembolso": parcela,
            "Patrimônio": imovel_v - s_devedor, "Custo Acumulado": custo_acum_fin
        })

    # 2. CONSÓRCIO
    credito_nom = v_contratacao_cons
    p_cons = (credito_nom * (1 + taxa_adm)) / prazo_cons
    reserva = entrada_fin - lance_proprio
    aluguel_c = aluguel_ini
    imovel_c = 0
    s_devedor_c = (credito_nom * (1 + taxa_adm)) - (lance_proprio * (1 + taxa_adm/prazo_cons))
    
    custo_acum_cons = (entrada_fin - reserva)
    
    for m in range(1, prazo_fin + 1):
        if m % 12 == 1 and m > 1:
            p_cons *= (1 + incc_anual)
            aluguel_c *= (1 + igpm_anual)
            if m <= mes_contemplacao: 
                credito_nom *= (1 + incc_anual)
        
        imovel_mercado_atual = v_imovel * (1 + v_mensal)**m
        c_aluguel = aluguel_c if m < mes_contemplacao else 0
        
        if m == mes_contemplacao:
            v_embutido = credito_nom * pct_lance_embutido
            liquido_disponivel = credito_nom - v_embutido
            poder_compra = liquido_disponivel + lance_proprio
            
            # Ajuste da reserva se o poder de compra for menor que o valor de mercado do imóvel
            necessidade_complemento = max(0, imovel_mercado_atual - poder_compra)
            reserva = max(0, reserva - necessidade_complemento)
            
            imovel_c = imovel_mercado_atual
            s_devedor_c -= v_embutido
        
        if imovel_c > 0: imovel_c *= (1 + v_mensal)
        reserva *= (1 + s_mensal)
        
        p_atual = p_cons if m <= prazo_cons else 0
        s_devedor_c = max(0, s_devedor_c - (p_atual / (1 + taxa_adm)) if p_atual > 0 else 0)
        
        desembolso_mes = p_atual + c_aluguel
        custo_acum_cons += desembolso_mes
        
        data.append({
            "Mês": m, "Tipo": "Consórcio", 
            "Parcela": p_atual, "Desembolso": desembolso_mes,
            "Patrimônio": imovel_c - s_devedor_c + reserva, "Custo Acumulado": custo_acum_cons
        })
        
    return pd.DataFrame(data)

df = rodar_simulacao()

# --- RESUMO DE RESULTADOS (Layout Anterior Restaurado) ---
res_fin = df[(df['Tipo']=="Financiamento") & (df['Mês']==prazo_fin)].iloc[0]
res_con = df[(df['Tipo']=="Consórcio") & (df['Mês']==prazo_fin)].iloc[0]

st.markdown("### 🎯 Comparativo Final Detalhado")

# Linha 1: Patrimônio Construído
st.markdown("#### 💎 Patrimônio Líquido Final (Valor do Imóvel - Dívida + Investimentos)")
col1, col2 = st.columns(2)
with col1:
    st.metric("Patrimônio com Financiamento", f"R$ {res_fin['Patrimônio']:,.2f}")
with col2:
    st.metric("Patrimônio com Consórcio", f"R$ {res_con['Patrimônio']:,.2f}")

# Linha 2: Custo Total
st.markdown("#### 💸 Custo Total da Jornada (Total pago ao Banco/Administradora + Aluguéis)")
col3, col4 = st.columns(2)
with col3:
    st.metric("Custo Total Financiamento", f"R$ {res_fin['Custo Acumulado']:,.2f}")
with col4:
    st.metric("Custo Total Consórcio + Aluguel", f"R$ {res_con['Custo Acumulado']:,.2f}")

# --- GRÁFICOS ---
st.divider()
st.subheader("📊 Evolução Patrimonial")
fig_pat = go.Figure()
for t in ["Financiamento", "Consórcio"]:
    sub = df[df['Tipo']==t]
    fig_pat.add_trace(go.Scatter(x=sub['Mês'], y=sub['Patrimônio'], name=t))
fig_pat.update_layout(template="plotly_dark")
st.plotly_chart(fig_pat, use_container_width=True)

# --- PLANILHA DETALHADA ---
st.divider()
st.subheader("📋 Memória de Cálculo Detalhada")
tipo_view = st.radio("Selecione a modalidade:", ["Financiamento", "Consórcio"], horizontal=True)
st.dataframe(df[df['Tipo']==tipo_view].style.format({
    "Parcela": "{:.2f}", 
    "Desembolso": "{:.2f}", 
    "Patrimônio": "{:.2f}", 
    "Custo Acumulado": "{:.2f}"
}), use_container_width=True)
