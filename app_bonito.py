import streamlit as st
import pandas as pd
import sqlite3
from babel.numbers import format_currency

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa Pessoal", layout="wide")

# --- CONEXÃO COM BANCO DE DADOS ---
conn = sqlite3.connect('financas.db', check_same_thread=False)
c = conn.cursor()

# Adicionamos a coluna 'tipo' na tabela para diferenciar Entrada de Saída
c.execute('''CREATE TABLE IF NOT EXISTS gastos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              mes TEXT, categoria TEXT, descricao TEXT, valor REAL, tipo TEXT)''')
conn.commit()

# Função para formatar moeda
def formatar_real(valor):
    return format_currency(valor, 'BRL', locale='pt_BR')

st.title("💰 Fluxo de Caixa Pessoal")

aba1, aba2 = st.tabs(["📊 Lançamentos e Gráficos", "📥 Configurações"])

with aba1:
    col_form, col_view = st.columns([1, 2])
    
    # --- FORMULÁRIO DE LANÇAMENTO ---
    with col_form:
        st.subheader("➕ Novo Registro")
        with st.form("form_fluxo", clear_on_submit=True):
            tipo_i = st.radio("Tipo de Registro", ["Saída", "Entrada"], horizontal=True)
            mes_list = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                        "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
            mes_i = st.selectbox("Mês de Referência", mes_list)
            cat_i = st.text_input("Categoria (ex: Salário, Moradia, Lazer)")
            desc_i = st.text_input("Descrição Detalhada")
            val_i = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
            
            if st.form_submit_button("Registrar no Fluxo"):
                if desc_i and val_i > 0:
                    c.execute("INSERT INTO gastos (mes, categoria, descricao, valor, tipo) VALUES (?, ?, ?, ?, ?)", 
                              (mes_i, cat_i, desc_i, val_i, tipo_i))
                    conn.commit()
                    st.success(f"{tipo_i} registrada com sucesso!")
                    st.rerun()

    # --- VISUALIZAÇÃO E ANÁLISE ---
    with col_view:
        st.subheader("🔎 Filtro por Mês")
        # Filtro único por mês para foco total
        mes_focado = st.selectbox("Selecione o mês para análise:", mes_list)
        
        dados = pd.read_sql_query(f"SELECT * FROM gastos WHERE mes = '{mes_focado}'", conn)
        
        if not dados.empty:
            # Cálculos de Fluxo
            entradas = dados[dados['tipo'] == 'Entrada']['valor'].sum()
            saidas = dados[dados['tipo'] == 'Saída']['valor'].sum()
            saldo = entradas - saidas
            
            # Cartões de Resumo
            c1, c2, c3 = st.columns(3)
            c1.metric("Entradas", formatar_real(entradas), delta_color="normal")
            c2.metric("Saídas", formatar_real(saidas), delta="- "+formatar_real(saidas), delta_color="inverse")
            c3.metric("Saldo Final", formatar_real(saldo), delta=formatar_real(saldo) if saldo >= 0 else formatar_real(saldo))

            st.divider()
            
            # --- PARTE GRÁFICA ---
            st.subheader("📊 Composição do Mês")
            df_grafico = pd.DataFrame({
                'Categoria': ['Entradas', 'Saídas'],
                'Valor': [entradas, saidas]
            })
            st.bar_chart(data=df_grafico.set_index('Categoria'))

            st.divider()

            # --- TABELA DE LANÇAMENTOS ---
            st.subheader("📑 Detalhes dos Lançamentos")
            df_view = dados.copy()
            
            # Cor
