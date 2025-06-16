from abc import ABC, abstractmethod


class AbstractCompletion(ABC):
    """Abstract base class for LLM completion."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Generate a completion for the given prompt."""
        ...
