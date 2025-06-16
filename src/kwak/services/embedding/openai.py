import openai

from kwak.services.embedding.base import AbstractEmbeddingProvider


class OpenAIEmbeddingProvider(AbstractEmbeddingProvider):
    """OpenAI embedding provider using the OpenAI API."""

    def __init__(self) -> None:
        """Initialize the OpenAI embedding provider."""
        self.client = openai.OpenAI()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into vector representations."""
        response = self.client.embeddings.create(
            input=texts, model="text-embedding-3-small"
        )

        return [embedding.embedding for embedding in response.data]
