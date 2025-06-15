from datetime import date

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
