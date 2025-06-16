from collections.abc import Iterable

from kwak.schemas.dossier import DossierChunk, SubsidieDossier
from kwak.services.chunkers.base import AbstractChunker


class WordCountChunker(AbstractChunker):
    """Chunker that splits text into fixed-size blocks based on word count."""

    def __init__(self, words_per_chunk: int = 200) -> None:
        """Initialize the WordCountChunker with a specific word count per chunk."""
        self.words_per_chunk = words_per_chunk

    def chunk(self, dossier: SubsidieDossier) -> Iterable[DossierChunk]:
        """Split de tekstvelden in vaste blokken van ongeveer N woorden."""
        for origin in ["omschrijving", "advies"]:
            text = getattr(dossier, origin)
            chunks = self._split_text(text)

            for chunk in chunks:
                yield DossierChunk(
                    dossier_id=dossier.id,
                    type=dossier.type,
                    title=dossier.titel,
                    startdatum=dossier.startdatum,
                    einddatum=dossier.einddatum,
                    goedgekeurd_budget=dossier.goedgekeurd_budget,
                    content=self._build_context(dossier, chunk),
                    origin=origin,  # type: ignore[arg-type]
                )

    def _split_text(self, text: str) -> list[str]:
        words = text.split()
        return [
            " ".join(words[i : i + self.words_per_chunk])
            for i in range(0, len(words), self.words_per_chunk)
        ]

    def _build_context(self, dossier: SubsidieDossier, chunk: str) -> str:
        return (
            f"Dossier: {dossier.titel}\n"
            f"Type: {dossier.type}\n"
            f"Periode: {dossier.startdatum} tot {dossier.einddatum}\n"
            f"Goedgekeurd budget: €{dossier.goedgekeurd_budget:,.2f}\n\n"
            f"{chunk}"
        )
