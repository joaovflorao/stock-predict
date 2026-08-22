import streamlit as st

from stock_predict.services.ingestion import ingest_movement_from_csv

from common import get_db, load_item_options


st.header(":material/upload_file: Carregar Movimentações")
st.write(
    "Envie um CSV com as colunas **Data, ID Item, Descrição Item, Quantidade e "
    "Tipo Movimento** (Compra, Venda ou Consumo)."
)

uploaded_file = st.file_uploader("Arquivo CSV", type=["csv"])

if st.button("Enviar", type="primary", disabled=uploaded_file is None):
    with st.spinner("Processando arquivo..."):
        content = uploaded_file.read()
        with get_db() as db:
            result = ingest_movement_from_csv(content, db)
        load_item_options.clear()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Linhas recebidas", result["rows_received"])
    col2.metric("Linhas ingeridas", result["rows_ingested"])
    col3.metric("Linhas rejeitadas", result["rows_rejected"])
    col4.metric("Itens novos criados", result["items_created"])

    if result["rows_rejected"] == 0:
        st.success("Arquivo processado com sucesso.")
    else:
        st.warning("Algumas linhas foram rejeitadas. Veja os detalhes abaixo.")

    if result["errors"]:
        with st.expander(f"Linhas rejeitadas ({len(result['errors'])})", expanded=True):
            for error in result["errors"]:
                st.text(error)
