import streamlit as st
import pandas as pd
import sqlite3
from babel.numbers import format_currency

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa Pessoal", layout="wide")

# --- CONEXÃO COM BANCO DE DADOS ---
conn = sqlite3.connect('financas.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS gastos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              mes TEXT, categoria TEXT, descricao TEXT, valor REAL, tipo TEXT)''')
conn.commit()

def formatar_real(valor):
    return format_currency(valor, 'BRL', locale='pt_BR')

st.title("💰 Fluxo de Caixa Pessoal")

aba1, aba2 = st.tabs(["📊 Lançamentos e Gestão", "📥 Configurações"])

mes_list = ["TODOS OS MESES", "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
            "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]

with aba1:
    col_form, col_view = st.columns([1, 3])
    
    with col_form:
        st.subheader("➕ Novo Registro")
        with st.form("form_fluxo", clear_on_submit=True):
            tipo_i = st.radio("Tipo", ["Saída", "Entrada"], horizontal=True)
            mes_i = st.selectbox("Mês de Referência", mes_list[1:])
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
        st.subheader("🔎 Gestão de Lançamentos")
        mes_focado = st.selectbox("Período exibido:", mes_list)
        
        # BUSCA DE DADOS
        query = "SELECT * FROM gastos" if mes_focado == "TODOS OS MESES" else "SELECT * FROM gastos WHERE mes = ?"
        params = () if mes_focado == "TODOS OS MESES" else (mes_focado,)
        df = pd.read_sql_query(query, conn, params=params)
        
        if not df.empty:
            # Painel de Métricas Rápidas
            total_e = df[df['tipo'] == 'Entrada']['valor'].sum()
            total_s = df[df['tipo'] == 'Saída']['valor'].sum()
            st.info(f"**Resumo:** Entradas: {formatar_real(total_e)} | Saídas: {formatar_real(total_s)} | Saldo: {formatar_real(total_e - total_s)}")

            st.write("---")
            st.caption("💡 **Dica:** Clique duas vezes em qualquer célula para editar. Selecione a linha e aperte 'Delete' para marcar como excluída.")

            # --- EDITOR DE DADOS (A CANETINHA) ---
            # Configuramos o editor para permitir deletar linhas e editar colunas específicas
            df_editado = st.data_editor(
                df,
                column_config={
                    "id": None, # Esconde o ID
                    "tipo": st.column_config.SelectboxColumn("Tipo", options=["Entrada", "Saída"], required=True),
                    "mes": st.column_config.SelectboxColumn("Mês", options=mes_list[1:], required=True),
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f"),
                },
                num_rows="dynamic", # Permite excluir linhas
                use_container_width=True,
                hide_index=True,
                key="editor_financeiro"
            )

            # Botão para salvar alterações (Streamlit detecta mudanças no st.session_state)
            if st.button("💾 Salvar Alterações na Tabela"):
                # Para simplificar e garantir que não haja erro de sincronia:
                # 1. Deletamos os IDs que estavam no período filtrado
                ids_originais = df['id'].tolist()
                placeholder = ', '.join(['?'] * len(ids_originais))
                c.execute(f"DELETE FROM gastos WHERE id IN ({placeholder})", ids_originais)
                
                # 2. Inserimos os dados que sobraram no editor
                for _, row in df_editado.iterrows():
                    c.execute("INSERT INTO gastos (mes, categoria, descricao, valor, tipo) VALUES (?, ?, ?, ?, ?)",
                              (row['mes'], row['categoria'], row['descricao'], row['valor'], row['tipo']))
                
                conn.commit()
                st.success("✅ Banco de dados atualizado com sucesso!")
                st.rerun()

        else:
            st.info(f"Nenhum dado encontrado para: {mes_focado}")

conn.close()
