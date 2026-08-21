from pydantic import BaseModel, Field


class IngestionResult(BaseModel):
    """ Resumo do processamento de um arquivo de movimentações """
    rows_received: int = Field(..., ge=0)
    rows_ingested: int = Field(..., ge=0)
    rows_rejected: int = Field(..., ge=0)
    items_created: int = Field(..., ge=0)
    errors: list[str] = []
