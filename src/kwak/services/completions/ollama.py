import os

from openai import OpenAI
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from kwak.services.completions.base import AbstractCompletion


class OllamaCompletion(AbstractCompletion):
    """Ollama completion service using a locally running Ollama instance."""

    def __init__(self, model_name: str = "deepseek-r1") -> None:
        """Initialize the OllamaDossierGenerator with a specific model."""
        provider = OpenAIProvider(base_url=os.getenv("OLLAMA_API_URL"))
        self.model = OpenAIModel(model_name, provider=provider)
        self.client = OpenAI(api_key="ollama", base_url=os.getenv("OLLAMA_API_URL"))
        self.model_name = model_name

    def complete(self, prompt: str) -> str:
        """Generate a completion for the given prompt using OpenAI API."""
        completion = self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "Je bent een behulpzame expert in subsidiedossiers.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )

        return completion.choices[0].message.parsed or ""
