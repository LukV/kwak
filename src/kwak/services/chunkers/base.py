from abc import ABC, abstractmethod
from collections.abc import Iterable

from kwak.schemas.dossier import DossierChunk, SubsidieDossier


class AbstractChunker(ABC):
    """Abstract base class for chunkers that split dossiers into semantic chunks."""

    @abstractmethod
    def chunk(self, dossier: SubsidieDossier) -> Iterable[DossierChunk]:
        """Chunk the text of a SourceDossier into semantic units."""
        ...
