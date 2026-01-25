import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Simulador Imobiliário Pro v2.0", layout="wide")

# Estilização para visual mais "Premium"
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Simulador Avançado: Financiamento vs. Consórcio")
st.markdown("---")

# --- SIDEBAR - PARÂMETROS ---
with st.sidebar:
    st.header("🏠 Dados do Imóvel")
    v_imovel = st.number_input("Valor Atual do Imóvel (R$)", value=500000, step=10000)
    val_anual = st.slider("Valorização Anual do Imóvel (%)", 0.0, 15.0, 6.0) / 100
    
    st.header("📉 Financiamento (SAC)")
    entrada_fin = st.number_input("Valor da Entrada (R$)", value=100000, step=5000)
    juros_anual = st.slider("Taxa de Juros Anual (%)", 5.0, 15.0, 10.5) / 100
    prazo_fin = st.number_input("Prazo (Meses)", value=360, step=12)
    tr_mensal = st.slider("TR Mensal Média (%)", 0.0, 0.5, 0.08) / 100

    st.header("🤝 Consórcio + Aluguel")
    taxa_adm = st.slider("Taxa de Adm. Total (%)", 10.0, 25.0, 15.0) / 100
    prazo_cons = st.number_input("Prazo Consórcio (Meses)", value=200, step=1)
    lance_proprio = st.number_input("Lance Próprio (R$)", value=100000, step=5000)
    mes_contemplacao = st.slider("Mês de Contemplação", 1, prazo_cons, 12)
    aluguel_ini = st.number_input("Aluguel Inicial (R$)", value=2500, step=100)
    
    st.header("📊 Índices Econômicos")
    incc_anual = st.slider("INCC Anual (%)", 0.0, 12.0, 5.0) / 100
    igpm_anual = st.slider("IGP-M Anual (%)", 0.0, 15.0, 5.0) / 100
    selic_anual = st.slider("Rendimento Reserva (% a.a.)", 0.0, 15.0, 10.0) / 100

# --- MOTOR DE CÁLCULO ---
def calcular_cenarios():
    # Taxas Mensais
    j_mensal = (1 + juros_anual)**(1/12) - 1
    v_mensal = (1 + val_anual)**(1/12) - 1
    s_mensal = (1 + selic_anual)**(1/12) - 1
    
    data = []
    
    # --- 1. FINANCIAMENTO ---
    s_devedor = v_imovel - entrada_fin
    imovel_v = v_imovel
    amort_base = s_devedor / prazo_fin
    
    for m in range(1, prazo_fin + 1):
        s_devedor *= (1 + tr_mensal) # Ajuste TR
        juros = s_devedor * j_mensal
        parcela = amort_base + juros
        imovel_v *= (1 + v_mensal)
        s_devedor -= amort_base
        patrimonio = imovel_v - max(0, s_devedor)
        
        data.append({
            "Mês": m, "Tipo": "Financiamento", "Parcela": parcela,
            "Aluguel": 0, "Desembolso Total": parcela, "Patrimônio Líquido": patrimonio,
            "Valor Imóvel": imovel_v, "Saldo Devedor": s_devedor
        })

    # --- 2. CONSÓRCIO ---
    credito_c = v_imovel
    parc_cons = (credito_c * (1 + taxa_adm)) / prazo_cons
    reserva = entrada_fin - lance_proprio
    aluguel_c = aluguel_ini
    imovel_c = 0
    s_devedor_c = (credito_c * (1 + taxa_adm)) - (lance_proprio * (1 + (taxa_adm/prazo_cons)))
    
    for m in range(1, prazo_fin + 1):
        # Reajustes anuais (INCC e IGP-M)
        if m % 12 == 1 and m > 1:
            parc_cons *= (1 + incc_anual)
            aluguel_c *= (1 + igpm_anual)
            if m <= mes_contemplacao:
                credito_c *= (1 + incc_anual)
        
        # Dinâmica de Moradia e Patrimônio
        custo_aluguel = aluguel_c if m < mes_contemplacao else 0
        if m == mes_contemplacao:
            imovel_c = credito_c
        
        if imovel_c > 0: imovel_c *= (1 + v_mensal)
        reserva *= (1 + s_mensal)
        
        # Pagamento Consórcio
        p_atual = parc_cons if m <= prazo_cons else 0
        s_devedor_c -= (p_atual / (1 + taxa_adm)) if p_atual > 0 else 0
        
        patrimonio_c = imovel_c - max(0, s_devedor_c) + reserva
        
        data.append({
            "Mês": m, "Tipo": "Consórcio", "Parcela": p_atual,
            "Aluguel": custo_aluguel, "Desembolso Total": p_atual + custo_aluguel,
            "Patrimônio Líquido": patrimonio_c, "Valor Imóvel": imovel_c, "Saldo Devedor": s_devedor_c
        })
        
    return pd.DataFrame(data)

df = calcular_cenarios()

# --- INTERFACE DE RESULTADOS ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("📈 Evolução do Patrimônio Líquido")
    fig_pat = go.Figure()
    fig_pat.add_trace(go.Scatter(x=df[df['Tipo']=="Financiamento"]['Mês'], y=df[df['Tipo']=="Financiamento"]['Patrimônio Líquido'], name="Financiamento"))
    fig_pat.add_trace(go.Scatter(x=df[df['Tipo']=="Consórcio"]['Mês'], y=df[df['Tipo']=="Consórcio"]['Patrimônio Líquido'], name="Consórcio + Aluguel"))
    fig_pat.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02), margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_pat, use_container_width=True)

with c2:
    st.subheader("💸 Desembolso Mensal")
    fig_des = go.Figure()
    fig_des.add_trace(go.Scatter(x=df[df['Tipo']=="Financiamento"]['Mês'], y=df[df['Tipo']=="Financiamento"]['Desembolso Total'], name="Parcela SAC"))
    fig_des.add_trace(go.Scatter(x=df[df['Tipo']=="Consórcio"]['Mês'], y=df[df['Tipo']=="Consórcio"]['Desembolso Total'], name="Consórcio + Aluguel"))
    fig_des.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02), margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_des, use_container_width=True)

# --- QUADRO RESUMO ---
st.markdown("### 🎯 Comparativo Final")
final_m = df['Mês'].max()
res_fin = df[(df['Tipo']=="Financiamento") & (df['Mês']==final_m)].iloc[0]
res_con = df[(df['Tipo']=="Consórcio") & (df['Mês']==final_m)].iloc[0]

col_a, col_b, col_c = st.columns(3)
col_a.metric("Patrimônio Financiamento", f"R$ {res_fin['Patrimônio Líquido']:,.2f}")
col_b.metric("Patrimônio Consórcio", f"R$ {res_con['Patrimônio Líquido']:,.2f}")
col_c.metric("Diferença", f"R$ {abs(res_fin['Patrimônio Líquido'] - res_con['Patrimônio Líquido']):,.2f}")

# --- TABELA E DOWNLOAD ---
st.markdown("---")
st.subheader("📋 Memória de Cálculo (Mês a Mês)")

# Seletor para a tabela
opcao_tab = st.selectbox("Visualizar dados de:", ["Financiamento", "Consórcio"])
df_view = df[df['Tipo'] == opcao_tab].copy()

st.dataframe(
    df_view.style.format({
        "Parcela": "{:.2f}", "Aluguel": "{:.2f}", "Desembolso Total": "{:.2f}",
        "Patrimônio Líquido": "{:.2f}", "Valor Imóvel": "{:.2f}", "Saldo Devedor": "{:.2f}"
    }), 
    use_container_width=True
)

# Exportação
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Baixar Simulação Completa (CSV)",
    data=csv,
    file_name='comparativo_imobiliario_expert.csv',
    mime='text/csv',
)

st.markdown("---")
st.subheader("📑 Parecer Técnico")
if res_fin['Patrimônio Líquido'] > res_con['Patrimônio Líquido']:
    st.success("O **Financiamento** apresentou maior acúmulo patrimonial devido à alavancagem precoce e valorização do ativo desde o D0.")
else:
    st.info("O **Consórcio** apresentou melhor eficiência financeira, preservando capital e reduzindo o custo de juros nominais.")
