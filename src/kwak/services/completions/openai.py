from openai import OpenAI

from kwak.services.completions.base import AbstractCompletion


class OpenAICompletion(AbstractCompletion):
    """OpenAI completion service using the OpenAI API."""

    def __init__(self, model: str = "gpt-4") -> None:
        """Initialize the OpenAI completion service."""
        self.client = OpenAI()
        self.model = model

    def complete(self, prompt: str) -> str:
        """Generate a completion for the given prompt using OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Je bent een behulpzame expert in subsidiedossiers.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content or ""
