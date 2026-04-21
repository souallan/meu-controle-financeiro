import streamlit as st
import pandas as pd
import sqlite3

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Meu Controle Financeiro Pro", layout="wide")

# --- CONEXÃO COM BANCO DE DADOS ---
# O check_same_thread=False é necessário para o Streamlit rodar bem com SQLite
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
    st.info("Utilize esta aba para carregar o seu histórico antigo via CSV.")
    arquivo_subido = st.file_uploader("Suba seu CSV aqui", type="csv")
    
    if arquivo_subido:
        try:
            # Tenta ler o arquivo com encodings comuns no Brasil/Portugal
            df_temp = pd.read_csv(arquivo_subido, encoding='latin1', sep=None, engine='python')
            st.success("Arquivo lido com sucesso!")
            st.write("Pré-visualização dos dados:")
            st.dataframe(df_temp.head())
            
            if st.button("Confirmar Carga de Dados"):
                st.warning("Função de migração automática em desenvolvimento. Por agora, utilize o formulário ao lado.")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

with aba1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Novo Lançamento")
        with st.form("form_gasto", clear_on_submit=True):
            mes_input = st.selectbox("Mês de Referência", 
                                    ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                                     "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"])
            cat_input = st.text_input("Tipo de Gasto (Ex: Hotel, Voo, Mercado)")
            desc_input = st.text_input("Descrição Detalhada")
            
            # CAMPO FORMATADO PARA REAL
            valor_input = st.number_input(
                "Valor (R$)", 
                min_value=0.0, 
                step=0.01, 
                format="%.2f"
            )
            
            if st.form_submit_button("Salvar no Sistema"):
                if desc_input and valor_input > 0:
                    c.execute("INSERT INTO gastos (mes, categoria, descricao, valor) VALUES (?, ?, ?, ?)", 
                              (mes_input, cat_input, desc_input, valor_input))
                    conn.commit()
                    st.success(f"Lançado: R$ {valor_input:,.2f} com sucesso!")
                    st.rerun() # Atualiza a tela para mostrar o novo gasto
                else:
                    st.error("Por favor, preencha a descrição e um valor válido.")

    with col2:
        st.subheader("Gastos Organizados")
        
        try:
            # Busca dados do banco
            dados = pd.read_sql_query("SELECT mes, categoria, descricao, valor FROM gastos", conn)
            
            if not dados.empty:
                # Filtros amigáveis
                meses_disponiveis = dados['mes'].unique()
                mes_filtro = st.multiselect("Filtrar por Meses:", options=meses_disponiveis, default=meses_disponiveis)
                
                dados_filtrados = dados[dados['mes'].isin(mes_filtro)].copy()
                
                # FORMATAÇÃO VISUAL PARA REAL NA TABELA
                # Criamos uma versão para exibição para não estragar os cálculos
                dados_exibicao = dados_filtrados.copy()
                dados_exibicao['valor'] = dados_exibicao['valor'].apply(lambda x: f"R$ {x:,.2f}")
                
                # Exibe a tabela
                st.dataframe(dados_exibicao.sort_values(by='mes'), use_container_width=True)
                
                # Métrica de Total
                total_soma = dados_filtrados['valor'].sum()
                st.divider()
                st.metric("Soma Total Selecionada", f"R$ {total_soma:,.2f}")
                
            else:
                st.info("O banco de dados ainda está vazio. Comece adicionando um gasto no formulário à esquerda.")
        except Exception as e:
            st.error(f"Erro ao carregar a visualização: {e}")

# Fechamento seguro da conexão
conn.close()
