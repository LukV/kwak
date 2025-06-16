import os
from collections.abc import Iterable

from openai import OpenAI
from pydantic import BaseModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from kwak.schemas.dossier import DossierChunk, SubsidieDossier
from kwak.services.chunkers.base import AbstractChunker


class ChunkResponse(BaseModel):
    """Response model for chunking text into semantic units."""

    chunks: list[str]


client = OpenAI(api_key="ollama", base_url=os.getenv("OLLAMA_API_URL"))


class SemanticChunker(AbstractChunker):
    """Chunker that uses an LLM (via OpenAI-compatible API) to
    split text into semantic chunks.
    """

    def __init__(self, model_name: str = "deepseek-r1") -> None:
        """Initialize the chunker with an OpenAI-compatible model."""
        self.client = OpenAI(api_key="ollama", base_url=os.getenv("OLLAMA_API_URL"))
        provider = OpenAIProvider(base_url=os.getenv("OLLAMA_API_URL"))
        self.model = OpenAIModel(model_name, provider=provider)
        self.model_name = model_name

    def chunk(self, dossier: SubsidieDossier) -> Iterable[DossierChunk]:
        """Chunk the text of a SubsidieDossier into semantic units,
        embedding structured context.
        """
        for origin in ["omschrijving", "advies"]:
            raw_text = getattr(dossier, origin)
            chunks = self._chunk_text(raw_text)

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

    def _chunk_text(self, text: str) -> list[str]:
        """Use Ollama via OpenAI-compatible API to split text into semantic chunks."""
        system_prompt = (
            "Split the provided text into coherent and meaningful sections "
            "(semantic chunks). Each chunk should be a short, self-contained "
            "unit of meaning (between 50 and 300 words), suitable for "
            "embedding and semantic search. "
            "Return ONLY valid JSON matching this schema:\n\nList[str]"
        )

        completion = client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            response_format=ChunkResponse,
        )

        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise ValueError("LLM failed to return valid JSON list of chunks.")  # noqa: TRY003

        return parsed.chunks

    def _build_context(self, dossier: SubsidieDossier, chunk: str) -> str:
        """Add structured dossier metadata to the chunk for better embeddings."""
        return (
            f"Dossier: {dossier.titel}\n"
            f"Type: {dossier.type}\n"
            f"Periode: {dossier.startdatum} tot {dossier.einddatum}\n"
            f"Goedgekeurd budget: €{dossier.goedgekeurd_budget:,.2f}\n\n"
            f"{chunk}"
        )
