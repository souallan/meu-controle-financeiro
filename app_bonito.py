import streamlit as st
import pandas as pd
import sqlite3
from babel.numbers import format_currency

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa Pessoal", layout="wide")

# --- CONEXÃO COM BANCO DE DADOS ---
conn = sqlite3.connect('financas.db', check_same_thread=False)
c = conn.cursor()

# 1. Cria a tabela base se não existir
c.execute('''CREATE TABLE IF NOT EXISTS gastos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              mes TEXT, categoria TEXT, descricao TEXT, valor REAL, tipo TEXT)''')

# 2. CORREÇÃO DE ERRO: Garante que a coluna 'tipo' exista caso o banco seja antigo
try:
    c.execute("ALTER TABLE gastos ADD COLUMN tipo TEXT DEFAULT 'Saída'")
except:
    pass # Se a coluna já existir, ele ignora o erro e segue em frente

conn.commit()

# Função para formatar moeda
def formatar_real(valor):
    return format_currency(valor, 'BRL', locale='pt_BR')

st.title("💰 Fluxo de Caixa Pessoal")

aba1, aba2 = st.tabs(["📊 Lançamentos e Gráficos", "📥 Configurações"])

mes_list = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
            "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]

with aba1:
    col_form, col_view = st.columns([1, 2])
    
    with col_form:
        st.subheader("➕ Novo Registro")
        with st.form("form_fluxo", clear_on_submit=True):
            tipo_i = st.radio("Tipo de Registro", ["Saída", "Entrada"], horizontal=True)
            mes_i = st.selectbox("Mês de Referência", mes_list)
            cat_i = st.text_input("Categoria")
            desc_i = st.text_input("Descrição Detalhada")
            val_i = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
            
            if st.form_submit_button("Registrar"):
                if desc_i and val_i > 0:
                    c.execute("INSERT INTO gastos (mes, categoria, descricao, valor, tipo) VALUES (?, ?, ?, ?, ?)", 
                              (mes_i, cat_i, desc_i, val_i, tipo_i))
                    conn.commit()
                    st.success("Registrado!")
                    st.rerun()

    with col_view:
        st.subheader("🔎 Filtro por Mês")
        mes_focado = st.selectbox("Selecione o mês:", mes_list)
        
        # Carrega os dados do mês
        dados = pd.read_sql_query(f"SELECT * FROM gastos WHERE mes = '{mes_focado}'", conn)
        
        if not dados.empty:
            # Cálculos
            entradas = dados[dados['tipo'] == 'Entrada']['valor'].sum()
            saidas = dados[dados['tipo'] == 'Saída']['valor'].sum()
            saldo = entradas - saidas
            
            # Métricas
            c1, c2, c3 = st.columns(3)
            c1.metric("Entradas", formatar_real(entradas))
            c2.metric("Saídas", formatar_real(saidas), delta_color="inverse")
            c3.metric("Saldo", formatar_real(saldo))

            # Gráfico de Barras
            st.write("### Comparativo Entrada vs Saída")
            df_chart = pd.DataFrame({'Tipo': ['Entradas', 'Saídas'], 'Total': [entradas, saidas]})
            st.bar_chart(df_chart.set_index('Tipo'))

            # Tabela
            st.write("### Detalhes")
            df_display = dados.copy()
            df_display['valor'] = df_display['valor'].apply(formatar_real)
            st.dataframe(df_display.drop(columns=['id']), use_container_width=True, hide_index=True)

            # Deletar
            with st.expander("🗑️ Excluir Registro"):
                mapa = {f"{r['tipo']} - {r['descricao']} ({formatar_real(r['
