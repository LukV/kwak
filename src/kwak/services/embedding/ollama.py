from kwak.services.embedding.base import AbstractEmbeddingProvider


class OllamaEmbeddingProvider(AbstractEmbeddingProvider):
    """Placeholder for future Ollama embedding support."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into vector representations using Ollama."""
        raise NotImplementedError("Ollama embedding not yet implemented")
