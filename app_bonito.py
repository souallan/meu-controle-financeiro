import streamlit as st
import pandas as pd
import sqlite3
from babel.numbers import format_currency

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa Pessoal", layout="wide")

# --- CONEXÃO COM BANCO DE DADOS ---
conn = sqlite3.connect('financas.db', check_same_thread=False)
c = conn.cursor()

# CRIAR TABELA (Se ela não existir)
c.execute('''CREATE TABLE IF NOT EXISTS gastos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              mes TEXT, categoria TEXT, descricao TEXT, valor REAL, tipo TEXT)''')

# GARANTIR COLUNA 'TIPO' (Caso o banco seja antigo)
try:
    c.execute("ALTER TABLE gastos ADD COLUMN tipo TEXT DEFAULT 'Saída'")
except:
    pass
conn.commit()

def formatar_real(valor):
    return format_currency(valor, 'BRL', locale='pt_BR')

st.title("💰 Fluxo de Caixa Pessoal")

aba1, aba2 = st.tabs(["📊 Lançamentos e Análise", "📥 Configurações"])

mes_list = ["TODOS OS MESES", "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
            "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]

with aba1:
    col_form, col_view = st.columns([1, 2.5])
    
    with col_form:
        st.subheader("➕ Novo Registro")
        with st.form("form_fluxo", clear_on_submit=True):
            tipo_i = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
            mes_i = st.selectbox("Mês de Referência", mes_list[1:]) # Remove o 'TODOS' para cadastro
            cat_i = st.text_input("Categoria")
            desc_i = st.text_input("Descrição")
            val_i = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
            
            if st.form_submit_button("Registrar"):
                if desc_i and val_i > 0:
                    c.execute("INSERT INTO gastos (mes, categoria, descricao, valor, tipo) VALUES (?, ?, ?, ?, ?)", 
                              (mes_i, cat_i, desc_i, val_i, tipo_i))
                    conn.commit()
                    st.success("✅ Registrado!")
                    st.rerun()

    with col_view:
        st.subheader("🔎 Visualização")
        mes_focado = st.selectbox("Período exibido:", mes_list)
        
        # BUSCA DE DADOS
        if mes_focado == "TODOS OS MESES":
            df = pd.read_sql_query("SELECT * FROM gastos", conn)
        else:
            df = pd.read_sql_query("SELECT * FROM gastos WHERE mes = ?", conn, params=(mes_focado,))
        
        if not df.empty:
            # Cálculos
            entradas = df[df['tipo'] == 'Entrada']['valor'].sum()
            saidas = df[df['tipo'] == 'Saída']['valor'].sum()
            saldo = entradas - saidas
            
            # Métricas
            m1, m2, m3 = st.columns(3)
            m1.metric("Entradas", formatar_real(entradas))
            m2.metric("Saídas", formatar_real(saidas), delta_color="inverse")
            m3.metric("Saldo Atual", formatar_real(saldo))

            st.divider()

            # TABELA (DETALHES)
            st.write("### 📑 Detalhes dos Lançamentos")
            df_temp = df.copy()
            df_temp['valor'] = df_temp['valor'].apply(formatar_real)
            
            cols = ['mes', 'tipo', 'categoria', 'descricao', 'valor'] if mes_focado == "TODOS OS MESES" else ['
