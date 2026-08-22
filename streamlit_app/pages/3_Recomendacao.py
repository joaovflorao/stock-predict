import streamlit as st

from stock_predict.schemas.config import Granularity
from stock_predict.schemas.recommendation import PurchaseRecommendationRequest
from stock_predict.services.recommendation import generate_purchase_recommendation

from common import MODEL_LABELS, get_db, item_selector


st.header(":material/shopping_cart: Recomendação de Compra")

item_id = item_selector(label="Item", key="recommendation_item")

col1, col2, col3, col4 = st.columns(4)
with col1:
    granularity_label = st.selectbox("Granularidade", options=[g.value for g in Granularity], index=1)
with col2:
    horizon = st.number_input("Horizonte", min_value=1, value=4, step=1)
with col3:
    lead_time_periods = st.number_input("Tempo de reposição (períodos)", min_value=1, value=2, step=1)
with col4:
    model_name = st.selectbox(
        "Modelo", options=list(MODEL_LABELS.keys()), format_func=lambda k: MODEL_LABELS[k]
    )

if "recommendation_result" not in st.session_state:
    st.session_state.recommendation_result = None
    st.session_state.recommendation_error = None

if st.button("Calcular", type="primary", disabled=item_id is None):
    try:
        request = PurchaseRecommendationRequest(
            item_id=item_id,
            granularity=Granularity(granularity_label),
            horizon=int(horizon),
            lead_time_periods=int(lead_time_periods),
            model_name=model_name,
        )
        with st.spinner("Calculando recomendação..."):
            with get_db() as db:
                recommendation = generate_purchase_recommendation(db, request)
        st.session_state.recommendation_result = recommendation
        st.session_state.recommendation_error = None
    except ValueError as exc:
        st.session_state.recommendation_result = None
        st.session_state.recommendation_error = str(exc)

if st.session_state.recommendation_error:
    st.error(st.session_state.recommendation_error)
elif st.session_state.recommendation_result:
    result = st.session_state.recommendation_result

    if not result.reliable:
        st.warning("Histórico curto: recomendação estimada pela demanda média histórica.")

    if result.should_reorder_now:
        st.error("Comprar agora", icon=":material/warning:")
    else:
        st.success("Estoque OK, sem necessidade de compra imediata", icon=":material/check_circle:")

    col1, col2, col3 = st.columns(3)
    col1.metric("Estoque atual", f"{result.current_stock:.0f}")
    col2.metric("Ponto de reposição", f"{result.reorder_point:.2f}")
    col3.metric("Quantidade sugerida", f"{result.recommended_order_quantity:.2f}")

    col4, col5 = st.columns(2)
    col4.metric(
        "Períodos até esgotar o estoque",
        result.periods_until_stockout if result.periods_until_stockout is not None else "-",
    )
    col5.metric(
        "Próxima reposição estimada",
        str(result.next_reorder_date) if result.next_reorder_date else "-",
    )
elif item_id is None:
    st.info("Selecione um item para começar.")
