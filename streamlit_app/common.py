from contextlib import contextmanager

import streamlit as st

from stock_predict.database.session import SessionLocal
from stock_predict.repositories.item_repository import ItemRepository

MODEL_LABELS = {
    "baseline": "Baseline",
    "xgboost": "XGBoost",
    "lstm": "LSTM",
}

DATE_COLUMN_FORMAT = "DD/MM/YYYY"

PT_BR_TIME_FORMAT_LOCALE = {
    "dateTime": "%A, %e de %B de %Y. %X",
    "date": "%d/%m/%Y",
    "time": "%H:%M:%S",
    "periods": ["AM", "PM"],
    "days": ["domingo", "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado"],
    "shortDays": ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"],
    "months": [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    ],
    "shortMonths": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
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
