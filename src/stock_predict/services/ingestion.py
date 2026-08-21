import csv
import io

from pydantic import ValidationError
from sqlalchemy.orm import Session

from stock_predict.repositories.item_repository import ItemRepository
from stock_predict.repositories.movement_repository import MovementRepository
from stock_predict.schemas.item import ItemCreate
from stock_predict.schemas.movement import StockMovementRow, MovementCreate


def validate_no_duplicate_movements(raw_rows: list[StockMovementRow]) -> None:
    """
        Garante que o lote de ingestão não tem a mesma movimentação repetida

        Duas linhas são consideradas a mesma movimentação quando item, data, quantidade
        e tipo coincidem, o que normalmente indica um erro de digitação ou duplicidade
        no arquivo de origem, e contaminaria o saldo de estoque e a série de demanda
    """
    seen = set()
    duplicates = set()
    for row in raw_rows:
        key = (row.item_id, row.movement_date, row.quantity, row.movement_type)
        if key in seen:
            duplicates.add(key)
        seen.add(key)

    if duplicates:
        raise ValueError(
            f"Movimentações duplicadas encontradas no lote de ingestão: {sorted(duplicates)}"
        )


def ingest_movement(raw_rows: list[StockMovementRow], db: Session) -> dict:
    """ Persiste um lote de movimentações já validado, criando os itens que ainda não existem """
    validate_no_duplicate_movements(raw_rows)

    item_repo = ItemRepository(db)
    movement_repo = MovementRepository(db)

    unique_items = {}
    for row in raw_rows:
        unique_items.setdefault(row.item_id, row.description)

    external_ids = list(unique_items.keys())
    existing_items = item_repo.get_by_external_ids(external_ids)

    items_by_external_ids = {item.external_id: item.id for item in existing_items}
    missing_external_ids = [
        ext_id for ext_id in external_ids
        if ext_id not in items_by_external_ids
    ]
    if missing_external_ids:
        new_items = [
            ItemCreate(external_id=ext_id, description=unique_items[ext_id])
            for ext_id in missing_external_ids
        ]
        created_items = item_repo.bulk_create(new_items)
        items_by_external_ids.update(
            {item.external_id: item.id for item in created_items}
        )

    movements_list = [
        MovementCreate(
            item_id=items_by_external_ids[row.item_id],
            movement_date=row.movement_date,
            quantity=row.quantity,
            movement_type=row.movement_type,
        )
        for row in raw_rows
    ]
    movement_repo.bulk_create(movements_list)

    return {
        "items_created": len(missing_external_ids),
        "movements_created": len(movements_list),
    }


def parse_csv_rows(content: bytes) -> tuple[list[StockMovementRow], list[str]]:
    """
        Interpreta um CSV de movimentações (colunas: Data, ID Item, Descrição Item,
        Quantidade, Tipo Movimento)

        Linhas com dados ausentes ou inválidos não derrubam o carregamento inteiro: elas são
        reportadas separadamente, para tratar a inconsistência sem descartar o restante do
        arquivo (requisito de validação dos dados antes de gerar previsões)
    """
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    valid_rows = []
    row_errors = []
    for line_number, raw_row in enumerate(reader, start=2):  # linha 1 é o cabeçalho
        try:
            valid_rows.append(StockMovementRow.model_validate(raw_row))
        except ValidationError as exc:
            first_error = exc.errors()[0]
            field_name = ".".join(str(part) for part in first_error["loc"])
            row_errors.append(f"Linha {line_number} ({field_name}): {first_error['msg']}")

    return valid_rows, row_errors


def ingest_movement_from_csv(content: bytes, db: Session) -> dict:
    """ Processa um arquivo CSV de movimentações, ingerindo as linhas válidas e reportando o restante """
    valid_rows, row_errors = parse_csv_rows(content)
    total_rows = len(valid_rows) + len(row_errors)

    batch_errors = []
    items_created = 0
    movements_created = 0

    if valid_rows:
        try:
            summary = ingest_movement(valid_rows, db)
            items_created = summary["items_created"]
            movements_created = summary["movements_created"]
        except ValueError as exc:
            batch_errors.append(str(exc))

    return {
        "rows_received": total_rows,
        "rows_ingested": movements_created,
        "rows_rejected": total_rows - movements_created,
        "items_created": items_created,
        "errors": row_errors + batch_errors,
    }
