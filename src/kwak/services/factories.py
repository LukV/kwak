from collections.abc import Callable

from kwak.services.completions.ollama import OllamaCompletion
from kwak.services.completions.openai import OpenAICompletion
from kwak.services.embedding.base import AbstractEmbeddingProvider
from kwak.services.embedding.ollama import OllamaEmbeddingProvider
from kwak.services.embedding.openai import OpenAIEmbeddingProvider
from kwak.services.generators.base import AbstractDossierGenerator
from kwak.services.generators.ollama import OllamaDossierGenerator
from kwak.services.generators.openai import OpenAIDossierGenerator

COMPLETION_REGISTRY = {
    "openai": OpenAICompletion,
    "ollama": OllamaCompletion,
}
GENERATOR_REGISTRY: dict[str, Callable[[], AbstractDossierGenerator]] = {
    "gpt-4": lambda: OpenAIDossierGenerator("gpt-4"),
    "deepseek-r1": lambda: OllamaDossierGenerator(),
}

EMBEDDING_REGISTRY: dict[str, Callable[[], AbstractEmbeddingProvider]] = {
    "openai": lambda: OpenAIEmbeddingProvider(),
    "ollama": lambda: OllamaEmbeddingProvider(),
}
