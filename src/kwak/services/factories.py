from collections.abc import Callable

from kwak.services.generators.base import AbstractDossierGenerator
from kwak.services.generators.ollama import OllamaDossierGenerator
from kwak.services.generators.openai import OpenAIDossierGenerator

GENERATOR_REGISTRY: dict[str, Callable[[], AbstractDossierGenerator]] = {
    "gpt-4": lambda: OpenAIDossierGenerator("gpt-4"),
    "deepseek-r1": lambda: OllamaDossierGenerator(),
}
