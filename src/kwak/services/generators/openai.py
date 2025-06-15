import random
from datetime import date, timedelta

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from kwak.schemas.dossier import SubsidieDossier
from kwak.services.generators.base import AbstractDossierGenerator
from kwak.utils import idgen


class OpenAIDossierGenerator(AbstractDossierGenerator):
    """Generates subsidy dossiers using OpenAI's GPT model."""

    def __init__(self, model_name: str = "gpt-4") -> None:
        """Initialize the OpenAIDossierGenerator with a specific model."""
        provider = OpenAIProvider()
        model = OpenAIModel(model_name, provider=provider)
        self.agent = Agent(model, output_type=SubsidieDossier)

    async def generate(
        self, dossier_type: str, start_year: int, end_year: int
    ) -> SubsidieDossier:
        """Generate a SubsidieDossier for the given dossier type and year range."""
        id = idgen.generate_id("D")  # noqa: A001
        start_date = date(start_year, 1, 1) + timedelta(days=random.randint(0, 364))  # noqa: S311
        latest_end = date(end_year, 12, 31)
        min_end = date(start_date.year + 1, 1, 1)
        delta_days = (latest_end - min_end).days
        end_date = min_end + timedelta(days=random.randint(0, max(delta_days, 0)))  # noqa: S311
        budget = round(random.uniform(10_000, 1_000_000), 2)  # noqa: S311

        prompt = f"""
Je bent een AI die subsidieaanvragen genereert. Genereer een subsidieaanvraag met
volgende eigenschappen:
- id: {id}
- type: {dossier_type}
- startdatum: {start_date.isoformat()}
- einddatum: {end_date.isoformat()}
- goedgekeurd budget: {budget:.2f} EUR
- titel: een korte en duidelijke titel voor het dossier, maximaal 150 tekens
- omschrijving: een realistische aanvraag binnen het domein '{dossier_type}', van
  minstens 1000 en maximaal 10000 tekens
- advies: een gemotiveerd advies van minstens 1000 en maximaal 2000 tekens
"""
        result = await self.agent.run(prompt)
        return result.output
