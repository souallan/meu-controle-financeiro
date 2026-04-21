import streamlit as st
import pandas as pd
import sqlite3

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Meu Controle Financeiro Pro", layout="wide")

# --- CONEXÃO COM BANCO DE DADOS ---
# No Streamlit Cloud, o banco .db será criado na pasta do projeto
conn = sqlite3.connect('financas.db', check_same_thread=False)
c = conn.cursor()

# Cria a tabela se não existir
c.execute('''CREATE TABLE IF NOT EXISTS gastos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              mes TEXT, categoria TEXT, descricao TEXT, valor REAL)''')
conn.commit()

st.title("🚀 Sistema de Gestão Financeira")

# --- ABA DE NAVEGAÇÃO ---
aba1, aba2 = st.tabs(["📊 Visualização e Cadastro", "📥 Importar Planilha Inicial"])

with aba2:
    st.subheader("Importação Única")
    arquivo_subido = st.file_uploader("Suba seu CSV para alimentar o banco de dados", type="csv")
    
    if arquivo_subido:
        try:
            # Tenta ler o arquivo
            df_temp = pd.read_csv(arquivo_subido, encoding='latin1', sep=None, engine='python')
            st.success("Arquivo lido com sucesso!")
            st.dataframe(df_temp.head())
            
            if st.button("Confirmar Carga de Dados"):
                st.info("Esta função será personalizada para o formato da sua planilha em breve.")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")
    else:
        st.info("Aguardando upload de arquivo CSV.")

with aba1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Novo Lançamento")
        with st.form("form_gasto", clear_on_submit=True):
            mes_input = st.selectbox("Mês", ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"])
            cat_input = st.text_input("Tipo de Gasto (Ex: Hotel, Voo)")
            desc_input = st.text_input("Descrição (Ex: Azul 1)")
            valor_input = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("Adicionar"):
                c.execute("INSERT INTO gastos (mes, categoria, descricao, valor) VALUES (?, ?, ?, ?)", 
                          (mes_input, cat_input, desc_input, valor_input))
                conn.commit()
                st.success("Lançado com sucesso!")

    with col2:
        st.subheader("Gastos Organizados")
        # Lê os dados do banco para mostrar na tela
        try:
            dados = pd.read_sql_query("SELECT mes, categoria, descricao, valor FROM gastos", conn)
            
            if not dados.empty:
                mes_filtro = st.multiselect("Filtrar Meses:", options=dados['mes'].unique(), default=dados['mes'].unique())
                dados_filtrados = dados[dados['mes'].isin(mes_filtro)]
                
                # Exibe a tabela organizada
                st.dataframe(dados_filtrados.sort_values(by='mes'), use_container_width=True)
                
                # Exibe o total
                total = dados_filtrados['valor'].sum()
                st.metric("Total no Período", f"R$ {total:,.2f}")
            else:
                st.warning("O banco de dados está vazio. Adicione um gasto ao lado.")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")

# Fechar conexão ao final (opcional no streamlit, mas boa prática)
conn.close()
