import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Simulador Imobiliário Pro", layout="wide")

# CSS Corrigido: Removi o fundo branco dos cards para evitar o "texto invisível"
st.markdown("""
    <style>
    .metric-container {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Comparativo: Financiamento vs. Consórcio")
st.caption("Versão com Memória de Cálculo e Ajustes de Inflação/Valorização")

# --- SIDEBAR - PARÂMETROS ---
with st.sidebar:
    st.header("🏠 Imóvel e Economia")
    v_imovel = st.number_input("Valor do Imóvel (R$)", value=500000)
    val_anual = st.slider("Valorização Anual (%)", 0.0, 15.0, 6.0) / 100
    selic_anual = st.slider("Rendimento Reserva (% a.a.)", 0.0, 15.0, 10.0) / 100
    
    st.header("📉 Financiamento (SAC)")
    entrada_fin = st.number_input("Entrada (R$)", value=100000)
    juros_anual = st.slider("Juros Anual (%)", 5.0, 15.0, 10.5) / 100
    prazo_fin = st.number_input("Prazo (Meses)", value=360)
    tr_mensal = st.slider("TR Mensal (%)", 0.0, 0.5, 0.08) / 100

    st.header("🤝 Consórcio")
    taxa_adm = st.slider("Taxa de Adm. Total (%)", 10.0, 25.0, 15.0) / 100
    prazo_cons = st.number_input("Prazo Consórcio", value=200)
    lance_proprio = st.number_input("Lance Próprio (R$)", value=100000)
    mes_contemplacao = st.slider("Mês Contemplação", 1, prazo_cons, 120)
    aluguel_ini = st.number_input("Aluguel Inicial (R$)", value=2500)
    incc_anual = st.slider("INCC Anual (%)", 0.0, 12.0, 6.0) / 100
    igpm_anual = st.slider("IGP-M Anual (%)", 0.0, 15.0, 4.5) / 100

# --- MOTOR DE CÁLCULO ---
def rodar_simulacao():
    j_mensal = (1 + juros_anual)**(1/12) - 1
    v_mensal = (1 + val_anual)**(1/12) - 1
    s_mensal = (1 + selic_anual)**(1/12) - 1
    
    data = []
    
    # FINANCIAMENTO
    s_devedor = v_imovel - entrada_fin
    imovel_v = v_imovel
    amort_base = s_devedor / prazo_fin
    
    for m in range(1, prazo_fin + 1):
        s_devedor *= (1 + tr_mensal)
        juros = s_devedor * j_mensal
        parcela = amort_base + juros
        imovel_v *= (1 + v_mensal)
        s_devedor = max(0, s_devedor - amort_base)
        patrimonio = imovel_v - s_devedor
        
        data.append({"Mês": m, "Tipo": "Financiamento", "Parcela": parcela, "Patrimônio": patrimonio})

    # CONSÓRCIO
    credito_c = v_imovel
    p_cons = (credito_c * (1 + taxa_adm)) / prazo_cons
    reserva = entrada_fin - lance_proprio
    aluguel_c = aluguel_ini
    imovel_c = 0
    s_devedor_c = (credito_c * (1 + taxa_adm)) - (lance_proprio * (1 + taxa_adm/prazo_cons))
    
    for m in range(1, prazo_fin + 1):
        if m % 12 == 1 and m > 1:
            p_cons *= (1 + incc_anual)
            aluguel_c *= (1 + igpm_anual)
            if m <= mes_contemplacao: credito_c *= (1 + incc_anual)
        
        c_aluguel = aluguel_c if m < mes_contemplacao else 0
        if m == mes_contemplacao: imovel_c = credito_c
        if imovel_c > 0: imovel_c *= (1 + v_mensal)
        reserva *= (1 + s_mensal)
        
        p_atual = p_cons if m <= prazo_cons else 0
        s_devedor_c = max(0, s_devedor_c - (p_atual / (1 + taxa_adm)) if p_atual > 0 else 0)
        
        data.append({"Mês": m, "Tipo": "Consórcio", "Parcela": p_atual + c_aluguel, "Patrimônio": imovel_c - s_devedor_c + reserva})
        
    return pd.DataFrame(data)

df = rodar_simulacao()

# --- VISUALIZAÇÃO ---
col1, col2 = st.columns(2)
with col1:
    fig_pat = go.Figure()
    for t in ["Financiamento", "Consórcio"]:
        sub = df[df['Tipo']==t]
        fig_pat.add_trace(go.Scatter(x=sub['Mês'], y=sub['Patrimônio'], name=t))
    fig_pat.update_layout(title="Evolução Patrimonial", template="plotly_dark")
    st.plotly_chart(fig_pat, use_container_width=True)

with col2:
    fig_parc = go.Figure()
    for t in ["Financiamento", "Consórcio"]:
        sub = df[df['Tipo']==t]
        fig_parc.add_trace(go.Scatter(x=sub['Mês'], y=sub['Parcela'], name=t))
    fig_parc.update_layout(title="Desembolso Mensal", template="plotly_dark")
    st.plotly_chart(fig_parc, use_container_width=True)

# --- COMPARATIVO FINAL CORRIGIDO (Visibilidade Total) ---
st.subheader("🎯 Comparativo Final")
res_fin = df[(df['Tipo']=="Financiamento") & (df['Mês']==prazo_fin)].iloc[0]
res_con = df[(df['Tipo']=="Consórcio") & (df['Mês']==prazo_fin)].iloc[0]

c_a, c_b, c_c = st.columns(3)
with c_a: st.metric("Patrimônio Financiamento", f"R$ {res_fin['Patrimônio']:,.2f}")
with c_b: st.metric("Patrimônio Consórcio", f"R$ {res_con['Patrimônio']:,.2f}")
with c_c: st.metric("Diferença", f"R$ {abs(res_fin['Patrimônio']-res_con['Patrimônio']):,.2f}")

# --- PLANILHA DETALHADA (O que você queria acrescentar) ---
st.divider()
st.subheader("📋 Memória de Cálculo Detalhada")
aba1, aba2 = st.tabs(["📊 Tabela Mensal", "📥 Download"])

with aba1:
    tipo_tab = st.radio("Ver dados de:", ["Financiamento", "Consórcio"], horizontal=True)
    st.dataframe(df[df['Tipo']==tipo_tab].style.format({"Parcela": "{:.2f}", "Patrimônio": "{:.2f}"}), use_container_width=True)

with aba2:
    st.download_button("Baixar Dados Completos (CSV)", df.to_csv(index=False).encode('utf-8'), "simulacao.csv", "text/csv")

# --- PARECER DO HEAD DE CRÉDITO ---
st.divider()
st.subheader("📑 Parecer Técnico")
if res_con['Patrimônio'] > res_fin['Patrimônio']:
    st.success(f"**Estratégia Recomendada: Consórcio.** O menor custo financeiro e a preservação de capital via reserva superaram o custo do aluguel e a alavancagem do financiamento neste cenário. Diferença de **R$ {res_con['Patrimônio']-res_fin['Patrimônio']:,.2f}** a favor do cliente.")
else:
    st.info(f"**Estratégia Recomendada: Financiamento.** A alavancagem imediata permitiu capturar a valorização do imóvel desde o primeiro mês, compensando os juros pagos. Diferença de **R$ {res_fin['Patrimônio']-res_con['Patrimônio']:,.2f}**.")
