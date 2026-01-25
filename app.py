import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Simulador Imobiliário Pro - Wealth Management", layout="wide")

st.title("🏦 Comparador de Estratégias Imobiliárias")
st.markdown("""
Esta versão avançada simula a evolução patrimonial mensal considerando:
* **TR** no saldo devedor do financiamento.
* **INCC** no crédito e parcelas do consórcio.
* **IGP-M** no reajuste de aluguel.
* **Valorização Real** do imóvel ao longo do tempo.
""")

# --- SIDEBAR - INPUTS ---
with st.sidebar:
    st.header("📌 Parâmetros do Imóvel")
    valor_imovel = st.number_input("Valor Atual do Imóvel (R$)", value=500000, step=10000)
    valorizacao_anual = st.slider("Valorização Anual do Imóvel (%)", 0.0, 15.0, 6.0) / 100
    
    st.header("💰 Financiamento (SAC)")
    entrada_fin = st.number_input("Valor da Entrada (R$)", value=100000, step=5000)
    taxa_juros_anual = st.slider("Taxa de Juros Anual (Efetiva %)", 5.0, 15.0, 10.5) / 100
    prazo_fin = st.number_input("Prazo do Financiamento (Meses)", value=360, step=12)
    taxa_tr_mensal = st.slider("TR Mensal Estimada (%)", 0.0, 0.5, 0.10) / 100

    st.header("🤝 Consórcio + Aluguel")
    taxa_adm = st.slider("Taxa de Adm. Total (%)", 10.0, 25.0, 15.0) / 100
    prazo_cons = st.number_input("Prazo do Consórcio (Meses)", value=200, step=1)
    lance_proprio = st.number_input("Lance Próprio (R$)", value=100000, step=5000)
    mes_contemplacao = st.slider("Mês da Contemplação (Estimado)", 1, prazo_cons, 12)
    aluguel_inicial = st.number_input("Valor do Aluguel Inicial (R$)", value=2500, step=100)
    
    st.header("📈 Indicadores Econômicos")
    incc_anual = st.slider("INCC Anual (Reajuste Consórcio %)", 0.0, 12.0, 5.0) / 100
    igpm_anual = st.slider("IGP-M Anual (Reajuste Aluguel %)", 0.0, 15.0, 5.0) / 100
    rendimento_selic = st.slider("Rendimento Reserva (Selic Líquida % a.a.)", 0.0, 15.0, 9.0) / 100

# --- LÓGICA DE SIMULAÇÃO ---
def rodar_simulacao():
    # Conversões
    juros_mensal = (1 + taxa_juros_anual)**(1/12) - 1
    incc_mensal = (1 + incc_anual)**(1/12) - 1
    igpm_mensal = (1 + igpm_anual)**(1/12) - 1
    val_mensal = (1 + valorizacao_anual)**(1/12) - 1
    selic_mensal = (1 + rendimento_selic)**(1/12) - 1
    
    # Listas para DataFrame
    resultados = []

    # --- SIMULAÇÃO FINANCIAMENTO ---
    saldo_devedor = valor_imovel - entrada_fin
    imovel_valorizado = valor_imovel
    principal_original = saldo_devedor
    
    for m in range(1, prazo_fin + 1):
        # Correção TR
        saldo_devedor *= (1 + taxa_tr_mensal)
        
        # SAC: Amortização é fixa sobre o principal original (simplificado)
        amortizacao = principal_original / prazo_fin
        juros = saldo_devedor * juros_mensal
        parcela = amortizacao + juros
        
        # Valorização do Ativo
        imovel_valorizado *= (1 + val_mensal)
        saldo_devedor -= amortizacao
        
        patrimonio_liquido = imovel_valorizado - max(0, saldo_devedor)
        
        resultados.append({
            "Mes": m, "Parcela": parcela, "Patrimônio": patrimonio_liquido,
            "Custo Acumulado": 0, "Tipo": "Financiamento"
        })

    # --- SIMULAÇÃO CONSÓRCIO ---
    credito_atual = valor_imovel
    taxa_mensal_cons = (taxa_adm / prazo_cons)
    parcela_cons = (credito_atual * (1 + taxa_adm)) / prazo_cons
    reserva = entrada_fin - lance_proprio
    aluguel_atual = aluguel_inicial
    imovel_cons = 0
    saldo_devedor_cons = (credito_atual * (1 + taxa_adm)) - (lance_proprio * (1 + taxa_adm/prazo_cons)) # simplificado
    
    for m in range(1, prazo_fin + 1):
        # Reajustes Anuais
        if m % 12 == 1 and m > 1:
            parcela_cons *= (1 + incc_anual)
            aluguel_atual *= (1 + igpm_anual)
            if m <= mes_contemplacao:
                credito_atual *= (1 + incc_anual)
        
        # Evento de Contemplação
        custo_moradia = 0
        if m < mes_contemplacao:
            custo_moradia = aluguel_atual
            reserva = (reserva + 0) * (1 + selic_mensal) # Rendendo o que sobrou
            patrimonio_cons = reserva
        else:
            if m == mes_contemplacao:
                imovel_cons = credito_atual
            imovel_cons *= (1 + val_mensal)
            reserva *= (1 + selic_mensal)
            patrimonio_cons = imovel_cons - max(0, saldo_devedor_cons) + reserva
        
        # Pagamento da Parcela
        if m <= prazo_cons:
            total_mes_cons = parcela_cons + custo_moradia
            saldo_devedor_cons -= (parcela_cons / (1 + taxa_adm))
        else:
            total_mes_cons = custo_moradia
            
        resultados.append({
            "Mes": m, "Parcela": total_mes_cons, "Patrimônio": patrimonio_cons,
            "Tipo": "Consórcio + Aluguel"
        })
        
    return pd.DataFrame(resultados)

df = rodar_simulacao()

# --- VISUALIZAÇÃO ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Evolução do Patrimônio Líquido")
    fig_pat = go.Figure()
    for tipo in df['Tipo'].unique():
        sub = df[df['Tipo'] == tipo]
        fig_pat.add_trace(go.Scatter(x=sub['Mes'], y=sub['Patrimônio'], name=tipo, fill='tozeroy'))
    fig_pat.update_layout(yaxis_title="R$ Patrimonio", xaxis_title="Meses")
    st.plotly_chart(fig_pat, use_container_width=True)

with col2:
    st.subheader("📉 Valor das Parcelas / Desembolso Mensal")
    fig_parc = go.Figure()
    for tipo in df['Tipo'].unique():
        sub = df[df['Tipo'] == tipo]
        fig_parc.add_trace(go.Scatter(x=sub['Mes'], y=sub['Parcela'], name=tipo))
    fig_parc.update_layout(yaxis_title="R$ Mensalidade", xaxis_title="Meses")
    st.plotly_chart(fig_parc, use_container_width=True)

# --- QUADRO RESUMO ---
st.divider()
st.subheader("🎯 Análise Final (Patrimônio no final do período)")
resumo = df[df['Mes'] == prazo_fin]
st.table(resumo[['Tipo', 'Patrimônio']].style.format({'Patrimônio': 'R$ {:,.2f}'}))

st.info(f"""
**Insight do Especialista:**
1. O **Financiamento** aproveita a valorização de 100% do imóvel desde o mês 1 (Alavancagem).
2. O **Consórcio** sofre com o reajuste do **INCC** nas parcelas e o **IGP-M** no aluguel, mas economiza em juros nominais.
3. Observe o ponto de cruzamento no gráfico de patrimônio: é onde a estratégia de menor custo supera a de maior alavancagem.
""")
