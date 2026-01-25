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

# No topo do seu app.py, logo após o título:

st.markdown("""
    <div style="background-color: rgba(0, 255, 204, 0.05); padding: 20px; border-radius: 10px; border-left: 5px solid #00ffcc;">
        <h3 style="margin-top:0;">🏰 Estrategista Imobiliário: O Caminho Mais Curto para o seu Patrimônio</h3>
        <p style="font-size: 1.1em;">
            Financiar ou planejar? Se você hoje paga aluguel e possui capital para uma entrada, sua decisão não deve ser baseada apenas na parcela, mas no seu <b>Patrimônio Líquido Final</b>. 
        </p>
        <p>
            Este simulador compara o custo real do financiamento bancário contra a estratégia de <b>Consórcio com Parcela Reduzida</b>, considerando valorização imobiliária, inflação e o impacto real do aluguel no seu tempo de espera.
        </p>
        <small><i>"Matemática não tem opinião. Ela tem resultados."</i></small>
    </div>
    <br>
""", unsafe_allow_html=True)

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

    st.header("🤝 Consórcio (Proporções XP/Embracon)")
    v_contratacao_cons = st.number_input("Valor de Contratação (R$)", value=500000)
    taxa_adm = st.slider("Taxa de Adm. Total (%)", 10.0, 30.0, 20.0) / 100
    fundo_reserva = st.slider("Fundo de Reserva (%)", 0.0, 5.0, 2.0) / 100
    prazo_cons = st.number_input("Prazo Consórcio", value=240)
    lance_proprio = st.number_input("Lance Próprio (R$)", value=100000)
    pct_lance_embutido = st.slider("% Lance Embutido", 0, 30, 25) / 100
    
    # VARIÁVEL DE PARCELA REDUZIDA (Baseada na Imagem)
    pct_redutor = st.slider("% Redutor (Até contemplar)", 0, 50, 50) / 100
    
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
    # Saldo devedor total (incluindo todas as taxas)
    s_devedor_c = (credito_nom * (1 + taxa_adm + fundo_reserva)) - (lance_proprio * (1 + (taxa_adm + fundo_reserva)/prazo_cons))
    
    custo_acum_cons = (entrada_fin - reserva)
    diferenca_redutor_acumulada = 0
    
    for m in range(1, prazo_fin + 1):
        if m % 12 == 1 and m > 1:
            aluguel_c *= (1 + igpm_anual)
            if m <= mes_contemplacao: credito_nom *= (1 + incc_anual)

        # CÁLCULO PROPORCIONAL DA IMAGEM
        # Parcela Cheia = (Crédito * (1 + F.R + Taxa Adm)) / Prazo
        p_cheia = (credito_nom * (1 + taxa_adm + fundo_reserva)) / prazo_cons
        
        # Parcela Reduzida (50% do Crédito + F.R. + 100% da Taxa Adm)
        p_reduzida = ((credito_nom * (1 + fundo_reserva)) * (1 - pct_redutor) + (credito_nom * taxa_adm)) / prazo_cons
        
        imovel_mercado_atual = v_imovel * (1 + v_mensal)**m
        c_aluguel = aluguel_c if m < mes_contemplacao else 0
        
        if m < mes_contemplacao:
            p_atual = p_reduzida
            diferenca_redutor_acumulada += (p_cheia - p_reduzida)
        elif m == mes_contemplacao:
            s_devedor_c += diferenca_redutor_acumulada
            v_embutido = credito_nom * pct_lance_embutido
            liquido_disponivel = credito_nom - v_embutido
            poder_compra = liquido_disponivel + lance_proprio
            
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

# Linha 1: Patrimônio
col1, col2 = st.columns(2)
with col1: st.metric("Patrimônio com Financiamento", f"R$ {res_fin['Patrimônio']:,.2f}")
with col2: st.metric("Patrimônio com Consórcio", f"R$ {res_con['Patrimônio']:,.2f}")

# Linha 2: Custo
col3, col4 = st.columns(2)
with col3: st.metric("Custo Total Financiamento", f"R$ {res_fin['Custo Acumulado']:,.2f}")
with col4: st.metric("Custo Total Consórcio + Aluguel", f"R$ {res_con['Custo Acumulado']:,.2f}")

# --- GRÁFICOS ---
st.divider()
st.subheader("📊 Evolução Patrimonial")
fig_pat = go.Figure()
for t in ["Financiamento", "Consórcio"]:
    sub = df[df['Tipo']==t]
    fig_pat.add_trace(go.Scatter(x=sub['Mês'], y=sub['Patrimônio'], name=t))
fig_pat.update_layout(template="plotly_dark")
st.plotly_chart(fig_pat, use_container_width=True)

# --- MEMÓRIA DE CÁLCULO ---
st.divider()
st.subheader("📋 Memória de Cálculo Detalhada")
tipo_view = st.radio("Selecione a modalidade:", ["Financiamento", "Consórcio"], horizontal=True)
st.dataframe(df[df['Tipo']==tipo_view].style.format({"Parcela": "{:.2f}", "Desembolso": "{:.2f}", "Patrimônio": "{:.2f}", "Custo Acumulado": "{:.2f}"}), use_container_width=True)

# --- PARECER DO HEAD DE CRÉDITO (VERSÃO TURBINADA) ---
st.divider()
st.subheader("📑 Parecer Técnico: Análise do Head de Crédito e Consórcio")

dif_patrimonio = abs(res_con['Patrimônio'] - res_fin['Patrimônio'])

if res_con['Patrimônio'] > res_fin['Patrimônio']:
    st.success(f"### ✅ Recomendação: Estratégia de Planejamento (Consórcio)")
    st.write(f"""
    **Análise de Viabilidade:** A estratégia de **Consórcio com Parcela Reduzida** se provou superior neste cenário, entregando um patrimônio **R$ {dif_patrimonio:,.2f} maior** ao final do ciclo.
    
    **Por que esta é a melhor decisão?**
    1. **Ciclo de Dívida Reduzido:** Enquanto o financiamento prenderia seu capital por 30 anos (360 meses), o consórcio liquida sua dívida em no máximo {prazo_cons/12:.1f} anos. Você ganha quase uma década de liberdade financeira.
    2. **Poder de Barganha:** Com a carta contemplada, você compra o imóvel como "pagador à vista", permitindo negociar descontos que o financiamento bancário não alcança.
    3. **Preservação de Liquidez:** O uso do redutor de 50% protege seu fluxo de caixa enquanto você ainda paga aluguel, evitando o sufocamento financeiro comum nos primeiros anos de um financiamento SAC.
    4. **Eficiência de Taxas:** Você foge dos juros compostos. A taxa de administração é fixa e diluída, ao contrário dos juros bancários que incidem sobre um saldo devedor corrigido mensalmente pela TR.
    """)
else:
    st.info(f"### 🏠 Recomendação: Alavancagem Imediata (Financiamento)")
    st.write(f"""
    **Análise de Viabilidade:** Para este perfil e cenário de valorização, o **Financiamento Imobiliário** é a escolha técnica, resultando em um patrimônio **R$ {dif_patrimonio:,.2f} superior**.
    
    **Por que esta é a melhor decisão?**
    1. **Captura de Valorização (D0):** Ao assumir o imóvel hoje, você se torna dono de 100% da valorização imobiliária desde o primeiro mês. Em cenários de alta valorização, isso supera qualquer economia de taxas.
    2. **Hospedagem Imediata:** O fim imediato do aluguel compensa o custo de juros mais elevado.
    3. **Custo de Oportunidade:** Se o tempo de contemplação estimado for muito longo, o reajuste do aluguel (IGP-M) e do imóvel pode tornar a entrada no consórcio mais cara do que o juro travado hoje.
    
    *Nota: Recomenda-se amortizações extraordinárias sempre que possível para reduzir o prazo total de 30 anos.*
    """)

st.caption("⚠️ Este parecer é uma simulação baseada em projeções econômicas e não garante resultados futuros.")
