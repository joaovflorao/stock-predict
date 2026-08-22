import pandas as pd
import streamlit as st

from stock_predict.schemas.config import Granularity
from stock_predict.schemas.recommendation import PurchaseRecommendationBulkRequest
from stock_predict.services.recommendation import generate_purchase_recommendations

from common import MODEL_LABELS, get_db


st.header(":material/shopping_cart: Recomendação de Compra")
st.caption("Situação de estoque e reposição sugerida para todos os itens")

col1, col2, col3, col4 = st.columns(4)
with col1:
    granularity_label = st.selectbox("Granularidade", options=[g.value for g in Granularity], index=1)
with col2:
    horizon = st.number_input(
        "Períodos a prever",
        min_value=1,
        value=4,
        step=1,
        help="Quantos períodos à frente prever, na granularidade escolhida.",
    )
with col3:
    lead_time_periods = st.number_input(
        "Prazo de entrega",
        min_value=1,
        value=2,
        step=1,
        help="Tempo entre fazer o pedido e a mercadoria chegar, em períodos da granularidade escolhida.",
    )
with col4:
    model_name = st.selectbox(
        "Modelo", options=list(MODEL_LABELS.keys()), format_func=lambda k: MODEL_LABELS[k]
    )

if "recommendation_result" not in st.session_state:
    st.session_state.recommendation_result = None
    st.session_state.recommendation_error = None

if st.button("Calcular", type="primary"):
    try:
        request = PurchaseRecommendationBulkRequest(
            granularity=Granularity(granularity_label),
            horizon=int(horizon),
            lead_time_periods=int(lead_time_periods),
            model_name=model_name,
        )
        with st.spinner("Calculando recomendações para todos os itens... isso pode levar um tempo."):
            with get_db() as db:
                recommendations = generate_purchase_recommendations(db, request)
        st.session_state.recommendation_result = recommendations
        st.session_state.recommendation_error = None
    except ValueError as exc:
        st.session_state.recommendation_result = None
        st.session_state.recommendation_error = str(exc)

if st.session_state.recommendation_error:
    st.error(st.session_state.recommendation_error)
elif st.session_state.recommendation_result is not None:
    recommendations = st.session_state.recommendation_result

    if not recommendations:
        st.info("Nenhum item com histórico suficiente para calcular recomendações.")
    else:
        df = pd.DataFrame(
            [
                {
                    "Item": item.description or "(sem descrição)",
                    "Estoque atual": float(rec.current_stock),
                    "Ponto de reposição": round(rec.reorder_point, 2),
                    "Comprar agora": "Sim" if rec.should_reorder_now else "Não",
                    "Quantidade sugerida": round(rec.recommended_order_quantity, 2),
                    "Períodos até esgotar": (
                        rec.periods_until_stockout if rec.periods_until_stockout is not None else None
                    ),
                    "Próxima reposição": str(rec.next_reorder_date) if rec.next_reorder_date else "-",
                    "Confiável": "Sim" if rec.reliable else "Não",
                }
                for item, rec in recommendations
            ]
        )

        c1, c2 = st.columns(2)
        c1.metric("Itens analisados", len(df))
        c2.metric("Precisam repor agora", int((df["Comprar agora"] == "Sim").sum()))

        only_reorder = st.checkbox("Mostrar somente itens que precisam repor agora")
        filtered_df = df[df["Comprar agora"] == "Sim"] if only_reorder else df

        st.dataframe(filtered_df, hide_index=True, width="stretch")
