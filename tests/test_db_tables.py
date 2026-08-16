from sqlalchemy import inspect
from stock_predict.database.session import engine


DB_TABLES = [
    "stock_item",
    "stock_movement",
]


def test_database_tables():
    with engine.connect() as connection:
        inspector = inspect(connection)
        tables = inspector.get_table_names()

    for tb_name in DB_TABLES:
        assert tb_name in tables
