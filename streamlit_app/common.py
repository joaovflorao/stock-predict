from contextlib import contextmanager

import streamlit as st

from stock_predict.database.session import SessionLocal
from stock_predict.repositories.item_repository import ItemRepository

MODEL_LABELS = {
    "baseline": "Baseline",
    "xgboost": "XGBoost",
    "lstm": "LSTM",
}


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def item_label(item) -> str:
    description = item.description or "(sem descrição)"
    return f"{item.id} - {item.external_id} - {description}"


def parse_item_id(label: str) -> int:
    return int(label.split(" - ")[0])


@st.cache_data(ttl=60, show_spinner=False)
def load_item_options() -> list[str]:
    with get_db() as db:
        items = ItemRepository(db).list_all()
        return [item_label(item) for item in items]


def item_selector(label: str = "Item", key: str = "item") -> int | None:
    """ Selectbox de item com busca embutida (react-select já filtra pelo texto digitado) """
    col_select, col_refresh = st.columns([5, 1])
    with col_refresh:
        st.write("")
        if st.button(
            "",
            icon=":material/refresh:",
            key=f"{key}_refresh",
            help="Recarregar lista de itens",
        ):
            load_item_options.clear()

    options = load_item_options()
    with col_select:
        selected = st.selectbox(
            label,
            options=options,
            index=None,
            placeholder="Digite para buscar por código ou descrição...",
            key=key,
        )
    return parse_item_id(selected) if selected else None
