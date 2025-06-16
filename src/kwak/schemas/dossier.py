from datetime import date
from typing import Literal

from pydantic import BaseModel


class SubsidieDossier(BaseModel):
    """Schema for a subsidy dossier."""

    id: str
    titel: str
    type: str
    startdatum: date
    einddatum: date
    goedgekeurd_budget: float
    omschrijving: str
    advies: str


class DossierChunk(BaseModel):
    """Schema for a semantically chunked section of a subsidy dossier."""

    dossier_id: str
    type: str
    title: str
    startdatum: date
    einddatum: date
    goedgekeurd_budget: float
    content: str
    origin: Literal["omschrijving", "advies"]
