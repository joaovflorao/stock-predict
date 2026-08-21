from stock_predict.database.session import SessionLocal
from stock_predict.repositories.item_repository import ItemRepository

MODEL_LABELS = {
    "baseline": "Baseline",
    "xgboost": "XGBoost",
    "lstm": "LSTM",
}


def load_items_sync() -> list[str]:
    db = SessionLocal()
    try:
        db_items = ItemRepository(db).list_all()
        return [
            f"{item.id} - {item.external_id} - {item.description}"
            for item in db_items
        ]
    finally:
        db.close()


def parse_item_id(selected_item: str) -> int:
    return int(selected_item.split(" - ")[0])
