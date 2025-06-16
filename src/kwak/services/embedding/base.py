from abc import ABC, abstractmethod


class AbstractEmbeddingProvider(ABC):
    """Abstract base class for dossier generators."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into vector representations."""
        ...
