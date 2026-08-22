import altair as alt
import pandas as pd
import streamlit as st

from stock_predict.schemas.config import Granularity
from stock_predict.services.prediction import run_full_analysis

from common import MODEL_LABELS, get_db, item_selector


st.header(":material/trending_up: Previsão de Demanda")

item_id = item_selector(label="Item", key="prediction_item")

col1, col2, col3 = st.columns(3)
with col1:
    granularity_label = st.selectbox("Granularidade", options=[g.value for g in Granularity], index=1)
with col2:
    horizon = st.number_input("Horizonte (períodos à frente)", min_value=1, value=4, step=1)
with col3:
    model_name = st.selectbox(
        "Modelo", options=list(MODEL_LABELS.keys()), format_func=lambda k: MODEL_LABELS[k]
    )

if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None
    st.session_state.prediction_error = None

if st.button("Consultar", type="primary", disabled=item_id is None):
    granularity = Granularity(granularity_label)
    try:
        with st.spinner("Calculando previsão..."):
            with get_db() as db:
                result = run_full_analysis(db, item_id, granularity, int(horizon), model_name=model_name)
        st.session_state.prediction_result = result
        st.session_state.prediction_error = None
    except ValueError as exc:
        st.session_state.prediction_result = None
        st.session_state.prediction_error = str(exc)

if st.session_state.prediction_error:
    st.error(st.session_state.prediction_error)
elif st.session_state.prediction_result:
    result = st.session_state.prediction_result
    predictions = result["predictions"]
    comparison = result["comparison"]
    history = result["history"]

    if predictions and not predictions[0].reliable:
        st.warning("Histórico curto: previsão estimada pela demanda média histórica.")

    if history or predictions:
        hist_df = pd.DataFrame(
            [{"period": h["period"], "value": h["demand"]} for h in history]
        )
        forecast_df = pd.DataFrame(
            [
                {
                    "period": str(p.period),
                    "value": float(p.predicted_quantity),
                    "lower": float(p.lower_bound),
                    "upper": float(p.upper_bound),
                }
                for p in predictions
            ]
        )

        layers = []
        if not hist_df.empty:
            layers.append(
                alt.Chart(hist_df)
                .mark_line(color="#2b8a3e", point=True)
                .encode(x=alt.X("period:T", title="Período"), y=alt.Y("value:Q", title="Quantidade"))
            )
        if not forecast_df.empty:
            layers.append(
                alt.Chart(forecast_df)
                .mark_area(opacity=0.2, color="#4263eb")
                .encode(x="period:T", y=alt.Y("lower:Q", title="Quantidade"), y2="upper:Q")
            )
            layers.append(
                alt.Chart(forecast_df)
                .mark_line(color="#1c7ed6", point=True, strokeDash=[5, 3])
                .encode(x="period:T", y="value:Q")
            )

        chart = alt.layer(*layers).properties(height=380).interactive()
        st.altair_chart(chart, width="stretch")

    if comparison:
        st.subheader("Comparação de modelos")
        comparison_df = pd.DataFrame([c.model_dump() for c in comparison]).rename(
            columns={"model_name": "Modelo", "wape": "WAPE", "mae": "MAE", "rmse": "RMSE"}
        )
        comparison_df["Modelo"] = comparison_df["Modelo"].map(lambda m: MODEL_LABELS.get(m, m))
        st.dataframe(comparison_df, hide_index=True, width="stretch")

    if predictions:
        st.subheader("Previsão detalhada")
        predictions_df = pd.DataFrame(
            [
                {
                    "Período": p.period,
                    "Previsto": round(float(p.predicted_quantity), 2),
                    "Mínimo": round(float(p.lower_bound), 2),
                    "Máximo": round(float(p.upper_bound), 2),
                }
                for p in predictions
            ]
        )
        st.dataframe(predictions_df, hide_index=True, width="stretch")
elif item_id is None:
    st.info("Selecione um item para começar.")
