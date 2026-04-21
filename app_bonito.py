import streamlit as st
import pandas as pd
import sqlite3
from babel.numbers import format_currency

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Controle Financeiro Pro", layout="wide")

# --- CONEXÃO COM BANCO DE DADOS ---
conn = sqlite3.connect('financas.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS gastos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              mes TEXT, categoria TEXT, descricao TEXT, valor REAL)''')
conn.commit()

def formatar_real(valor):
    return format_currency(valor, 'BRL', locale='pt_BR')

st.title("🚀 Sistema de Gestão Financeira")

aba1, aba2 = st.tabs(["📊 Painel de Controle", "📥 Importação"])

with aba2:
    st.subheader("Importar Dados")
    st.info("Espaço destinado à importação de arquivos CSV antigos.")

with aba1:
    col1, col2 = st.columns([1, 2])
    
    # --- COLUNA 1: NOVO CADASTRO ---
    with col1:
        st.subheader("🆕 Novo Lançamento")
        with st.form("form_gasto", clear_on_submit=True):
            mes_list = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                        "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
            mes_i = st.selectbox("Mês", mes_list)
            cat_i = st.text_input("Categoria")
            desc_i = st.text_input("Descrição")
            val_i = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
            
            if st.form_submit_button("Salvar Novo"):
                if desc_i and val_i > 0:
                    c.execute("INSERT INTO gastos (mes, categoria, descricao, valor) VALUES (?, ?, ?, ?)", 
                              (mes_i, cat_i, desc_i, val_i))
                    conn.commit()
                    st.success("Lançado com sucesso!")
                    st.rerun()

    # --- COLUNA 2: VISUALIZAÇÃO E EDIÇÃO ---
    with col2:
        st.subheader("📑 Registros")
        dados = pd.read_sql_query("SELECT * FROM gastos", conn)
        
        if not dados.empty:
            # Filtro de exibição
            meses_disp = dados['mes'].unique()
            filtro = st.multiselect("Filtrar por Mês:", meses_disp, default=meses_disp)
            df_filtrado = dados[dados['mes'].isin(filtro)].copy()
            
            # Exibição formatada
            df_view = df_filtrado.copy()
            df_view['valor'] = df_view['valor'].apply(formatar_real)
            st.dataframe(df_view.drop(columns=['id']), use_container_width=True, hide_index=True)
            
            st.divider()

            # --- ÁREA DE GESTÃO (EDITAR / APAGAR) ---
            st.subheader("🛠️ Gerenciar Lançamento")
            
            # Mapeia descrição para o ID para facilitar a seleção
            opcoes = {f"ID {row['id']} | {row['descricao']} ({formatar_real(row['valor'])})": row for _, row in df_filtrado.iterrows()}
            selecao = st.selectbox("Selecione um item para modificar ou excluir:", options=list(opcoes.keys()))
            
            if selecao:
                item = opcoes[selecao]
                
                # Usamos um expander para não poluir a tela
                with st.expander(f"📝 Editar/Remover: {item['descricao']}"):
                    with st.form("form_edit"):
                        # Preenche os campos com os valores atuais do banco
                        ed_mes = st.selectbox("Mês", mes_list, index=mes_list.index(item['mes']))
                        ed_cat = st.text_input("Categoria", value=item['categoria'])
                        ed_desc = st.text_input("Descrição", value=item['descricao'])
                        ed_val = st.number_input("Valor", value=float(item['valor']), step=0.01, format="%.2f")
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.form_submit_button("✅ Confirmar Alteração", use_container_width=True):
                                c.execute("UPDATE gastos SET mes=?, categoria=?, descricao=?, valor=? WHERE id=?", 
                                          (ed_mes, ed_cat, ed_desc, ed_val, item['id']))
                                conn.commit()
                                st.success("Alterado!")
                                st.rerun()
                        with c2:
                            if st.form_submit_button("🗑️ Excluir Registro", type="primary", use_container_width=True):
                                c.execute("DELETE FROM gastos WHERE id=?", (item['id'],))
                                conn.commit()
                                st.warning("Excluído!")
                                st.rerun()

            total = df_filtrado['valor'].sum()
            st.metric("Total dos itens filtrados", formatar_real(total))
        else:
            st.info("Nenhum dado encontrado.")

conn.close()
