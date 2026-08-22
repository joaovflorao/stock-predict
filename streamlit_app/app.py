import streamlit as st

st.set_page_config(page_title="Stock Predict", page_icon=":material/inventory_2:", layout="wide")

pages = [
    st.Page("Home.py", title="Início", icon=":material/home:", default=True),
    st.Page("pages/1_Carregar_Dados.py", title="Carregar Dados", icon=":material/upload_file:"),
    st.Page("pages/2_Previsao.py", title="Previsão", icon=":material/trending_up:"),
    st.Page("pages/3_Recomendacao.py", title="Recomendação de Compra", icon=":material/shopping_cart:"),
    st.Page("pages/4_Oportunidades.py", title="Oportunidades", icon=":material/lightbulb:"),
]

pg = st.navigation(pages)
pg.run()
