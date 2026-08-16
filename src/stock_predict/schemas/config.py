from datetime import date
from enum import Enum
from pydantic import BaseModel, Field


class Granularity(str, Enum):
    """ Período da predição """
    DAILY   = "Diário"
    WEEKLY  = "Semanal"
    MONTHLY = "Mensal"
    ANNUAL  = "Anual"


class PredictionConfig(BaseModel):
    """ Configuração da predição analisada """
    granularity: Granularity
    horizon: int = Field(..., gt=0)
    item_id: int | None = None
    analysis_start_date: date | None = None
    analysis_end_date: date | None = None
