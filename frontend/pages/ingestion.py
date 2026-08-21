import asyncio

import reflex as rx

from stock_predict.database.session import SessionLocal
from stock_predict.services.ingestion import ingest_movement_from_csv

from .nav import nav_bar

UPLOAD_ID = "movements_csv"


def _ingest_csv_sync(content: bytes) -> dict:
    db = SessionLocal()
    try:
        return ingest_movement_from_csv(content, db)
    finally:
        db.close()


class IngestionState(rx.State):
    is_uploading: bool = False
    error: str = ""

    has_summary: bool = False
    rows_received: int = 0
    rows_ingested: int = 0
    rows_rejected: int = 0
    items_created: int = 0
    row_errors: list[str] = []

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        if not files:
            self.error = "Selecione um arquivo CSV"
            return

        self.is_uploading = True
        self.error = ""
        self.has_summary = False
        yield

        file = files[0]
        content = await file.read()

        try:
            result = await asyncio.to_thread(_ingest_csv_sync, content)
        except Exception as exc:
            self.error = f"Erro ao processar o arquivo: {exc}"
            self.is_uploading = False
            return

        self.has_summary = True
        self.rows_received = result["rows_received"]
        self.rows_ingested = result["rows_ingested"]
        self.rows_rejected = result["rows_rejected"]
        self.items_created = result["items_created"]
        self.row_errors = result["errors"]
        self.is_uploading = False


def ingestion_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            nav_bar(),
            rx.heading("Carregar Movimentações"),
            rx.text(
                "Envie um CSV com as colunas Data, ID Item, Descrição Item, Quantidade e "
                "Tipo Movimento (Compra, Venda ou Consumo). Use o script "
                "scripts/generate_synthetic_data.py para gerar um arquivo de exemplo."
            ),
            rx.upload(
                rx.vstack(
                    rx.button("Selecionar arquivo CSV"),
                    rx.text("ou arraste o arquivo aqui"),
                ),
                id=UPLOAD_ID,
                accept={"text/csv": [".csv"]},
                multiple=False,
            ),
            rx.hstack(rx.foreach(rx.selected_files(UPLOAD_ID), rx.text)),
            rx.button(
                "Enviar",
                on_click=IngestionState.handle_upload(rx.upload_files(upload_id=UPLOAD_ID)),
                loading=IngestionState.is_uploading,
            ),
            rx.cond(
                IngestionState.error != "",
                rx.callout(IngestionState.error, color_scheme="red"),
            ),
            rx.cond(
                IngestionState.has_summary,
                rx.vstack(
                    rx.text(f"Linhas recebidas: {IngestionState.rows_received}"),
                    rx.text(f"Linhas ingeridas: {IngestionState.rows_ingested}"),
                    rx.text(f"Linhas rejeitadas: {IngestionState.rows_rejected}"),
                    rx.text(f"Itens novos criados: {IngestionState.items_created}"),
                    rx.cond(
                        IngestionState.row_errors.length() > 0,
                        rx.vstack(
                            rx.heading("Linhas rejeitadas", size="4"),
                            rx.foreach(IngestionState.row_errors, rx.text),
                        ),
                    ),
                    spacing="2",
                ),
            ),
            spacing="4",
            width="100%",
            max_width="900px",
        ),
    )
