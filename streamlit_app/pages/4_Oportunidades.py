import pandas as pd
import streamlit as st

from stock_predict.schemas.config import Granularity
from stock_predict.schemas.opportunity import OpportunityRequest
from stock_predict.services.opportunity import generate_opportunities

from common import MODEL_LABELS, get_db


st.header(":material/lightbulb: Oportunidades de Venda")
st.caption("Ranking de itens por tendência e volume de demanda prevista")

col1, col2, col3, col4 = st.columns(4)
with col1:
    granularity_label = st.selectbox("Granularidade", options=[g.value for g in Granularity], index=1)
with col2:
    horizon = st.number_input("Horizonte", min_value=1, value=4, step=1)
with col3:
    model_name = st.selectbox(
        "Modelo", options=list(MODEL_LABELS.keys()), format_func=lambda k: MODEL_LABELS[k]
    )
with col4:
    trend_threshold_pct = st.number_input("Limiar de variação (%)", min_value=0.0, value=5.0, step=0.5)

if "opportunities_result" not in st.session_state:
    st.session_state.opportunities_result = None
    st.session_state.opportunities_error = None

if st.button("Calcular", type="primary"):
    try:
        request = OpportunityRequest(
            granularity=Granularity(granularity_label),
            horizon=int(horizon),
            model_name=model_name,
            trend_threshold_pct=float(trend_threshold_pct),
        )
        with st.spinner("Calculando oportunidades para todos os itens... isso pode levar um tempo."):
            with get_db() as db:
                opportunities = generate_opportunities(db, request)
        st.session_state.opportunities_result = opportunities
        st.session_state.opportunities_error = None
    except ValueError as exc:
        st.session_state.opportunities_result = None
        st.session_state.opportunities_error = str(exc)

if st.session_state.opportunities_error:
    st.error(st.session_state.opportunities_error)
elif st.session_state.opportunities_result is not None:
    opportunities = st.session_state.opportunities_result

    if not opportunities:
        st.info("Nenhuma oportunidade encontrada com os parâmetros selecionados.")
    else:
        df = pd.DataFrame(
            [
                {
                    "Item": o.item_description or "(sem descrição)",
                    "Tendência": o.trend,
                    "Var. %": round(o.trend_pct, 2),
                    "Média Histórica": round(o.historical_average_demand, 2),
                    "Média Prevista": round(o.forecasted_average_demand, 2),
                    "Total Previsto": round(o.total_forecasted_demand, 2),
                    "Confiável": "Sim" if o.reliable else "Não",
                }
                for o in opportunities
            ]
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Itens analisados", len(df))
        c2.metric("Em crescimento", int((df["Tendência"] == "crescimento").sum()))
        c3.metric("Em queda", int((df["Tendência"] == "queda").sum()))

        trend_filter = st.multiselect(
            "Filtrar por tendência",
            options=["crescimento", "estavel", "queda"],
            default=["crescimento", "estavel", "queda"],
        )
        filtered_df = df[df["Tendência"].isin(trend_filter)]

        st.dataframe(filtered_df, hide_index=True, width="stretch")
