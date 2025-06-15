from abc import ABC, abstractmethod

from kwak.schemas.dossier import SubsidieDossier


class AbstractDossierGenerator(ABC):
    """Abstract base class for dossier generators."""

    @abstractmethod
    async def generate(
        self, dossier_type: str, start_year: int, end_year: int
    ) -> SubsidieDossier:
        """Generate a SubsidieDossier for the given dossier type and year range."""
        ...
