import streamlit as st
import pandas as pd
import sqlite3
from babel.numbers import format_currency # Nova biblioteca para formatar moeda

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Meu Controle Financeiro Pro", layout="wide")

# --- CONEXÃO COM BANCO DE DADOS ---
conn = sqlite3.connect('financas.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS gastos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              mes TEXT, categoria TEXT, descricao TEXT, valor REAL)''')
conn.commit()

# FUNÇÃO AUXILIAR PARA FORMATAR MOEDA BRASILEIRA
def formatar_real(valor):
    return format_currency(valor, 'BRL', locale='pt_BR')

st.title("🚀 Sistema de Gestão Financeira")

aba1, aba2 = st.tabs(["📊 Visualização e Cadastro", "📥 Importar Planilha Inicial"])

with aba2:
    st.subheader("Importação Única")
    arquivo_subido = st.file_uploader("Suba seu CSV aqui", type="csv")
    if arquivo_subido:
        st.info("Arquivo carregado. Use o formulário para novos lançamentos.")

with aba1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Novo Lançamento")
        with st.form("form_gasto", clear_on_submit=True):
            mes_input = st.selectbox("Mês de Referência", 
                                    ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                                     "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"])
            cat_input = st.text_input("Tipo de Gasto")
            desc_input = st.text_input("Descrição Detalhada")
            
            # O campo de entrada ainda usará o ponto para centavos (padrão do navegador),
            # mas o resultado final será brasileiro.
            valor_input = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
            
            if st.form_submit_button("Salvar no Sistema"):
                if desc_input and valor_input > 0:
                    c.execute("INSERT INTO gastos (mes, categoria, descricao, valor) VALUES (?, ?, ?, ?)", 
                              (mes_input, cat_input, desc_input, valor_input))
                    conn.commit()
                    st.success(f"Salvo: {formatar_real(valor_input)}")
                    st.rerun()

    with col2:
        st.subheader("Gastos Organizados")
        try:
            dados = pd.read_sql_query("SELECT mes, categoria, descricao, valor FROM gastos", conn)
            
            if not dados.empty:
                meses_disponiveis = dados['mes'].unique()
                mes_filtro = st.multiselect("Filtrar por Meses:", options=meses_disponiveis, default=meses_disponiveis)
                dados_filtrados = dados[dados['mes'].isin(mes_filtro)].copy()
                
                # AQUI A MÁGICA ACONTECE: Formata para o padrão R$ 1.000,00
                dados_exibicao = dados_filtrados.copy()
                dados_exibicao['valor'] = dados_exibicao['valor'].apply(formatar_real)
                
                st.dataframe(dados_exibicao.sort_values(by='mes'), use_container_width=True)
                
                total_soma = dados_filtrados['valor'].sum()
                st.divider()
                # Mostra o total também formatado
                st.metric("Soma Total Selecionada", formatar_real(total_soma))
            else:
                st.info("Nenhum gasto cadastrado.")
        except Exception as e:
            st.error(f"Erro: {e}")

conn.close()
