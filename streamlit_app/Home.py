import streamlit as st

from stock_predict.models.movement import Movement
from stock_predict.repositories.item_repository import ItemRepository

from common import get_db

st.header(":material/inventory_2: Stock Predict")
st.caption("Sistema de predição inteligente no controle de estoque")

with get_db() as db:
    total_items = len(ItemRepository(db).list_all())
    total_movements = db.query(Movement).count()

col1, col2 = st.columns(2)
col1.metric("Itens cadastrados", f"{total_items:,}".replace(",", "."))
col2.metric("Movimentações registradas", f"{total_movements:,}".replace(",", "."))

st.divider()

st.subheader("Onde ir")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.page_link("pages/1_Carregar_Dados.py", label="Carregar Dados", icon=":material/upload_file:")
    st.caption("Envie um CSV de movimentações de estoque")
with c2:
    st.page_link("pages/2_Previsao.py", label="Previsão", icon=":material/trending_up:")
    st.caption("Preveja a demanda futura de um item")
with c3:
    st.page_link("pages/3_Recomendacao.py", label="Recomendação de Compra", icon=":material/shopping_cart:")
    st.caption("Saiba quando e quanto comprar")
with c4:
    st.page_link("pages/4_Oportunidades.py", label="Oportunidades", icon=":material/lightbulb:")
    st.caption("Ranking de itens por tendência de demanda")
