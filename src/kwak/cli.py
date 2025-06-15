import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING

import duckdb
import typer
from rich.console import Console
from rich.progress import Progress

if TYPE_CHECKING:
    from kwak.schemas.dossier import SubsidieDossier
from kwak.services.factories import GENERATOR_REGISTRY

app = typer.Typer(help="🦆 kwak: A RAG-ready CLI for subsidiedossiers")
console = Console()


@app.command()
def say(word: str) -> None:
    """Echo a word back in a friendly way."""
    typer.echo(f"{word} you say?")


@app.command()
def generate_data(  # noqa: PLR0913
    model: str = typer.Option("gpt-4", help="Model to use: gpt-4 or deepseek-r1"),
    count: int = typer.Option(10, help="Number of dossiers to generate"),
    start_year: int = typer.Option(2018, help="Start year for subsidy"),
    end_year: int = typer.Option(2022, help="End year for subsidy"),
    type_: str = typer.Option("erfgoed", help="Type of subsidiedossier"),
    output: Path = typer.Option(  # noqa: B008
        Path("data/generated/subsidiedossiers.jsonl"), help="Output file path"
    ),
) -> None:
    """Genereer synthetische subsidiedossiers."""
    if model not in GENERATOR_REGISTRY:
        raise typer.BadParameter(f"Unsupported model: {model}")  # noqa: EM102, TRY003

    generator = GENERATOR_REGISTRY[model]()

    dossiers: list[SubsidieDossier] = []

    async def generate_all() -> None:
        with Progress() as progress:
            task = progress.add_task("Generating dossiers...", total=count)
            for _ in range(count):
                dossier = await generator.generate(type_, start_year, end_year)
                dossiers.append(dossier)
                progress.advance(task)

    asyncio.run(generate_all())

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as f:
        for dossier in dossiers:
            f.write(dossier.model_dump_json() + "\n")

    console.print(f"✅ [green]Successfully wrote {count} dossiers to {output}[/green]")


@app.command()
def updatedb() -> None:
    """Update the database with the latest data."""
    db_path = "data/kwak.db"
    jsonl_path = Path("data/generated/subsidiedossiers.jsonl")
    table_name = "dossiers"

    if not jsonl_path.exists():
        console.print(f"[red]❌ JSONL file not found at {jsonl_path}[/red]")
        raise typer.Exit(1)

    # Recreate table
    with Path("queries/create_dossiers.sql").open() as qf:
        create_stmt = qf.read().replace("$table_name", table_name)

    with duckdb.connect(db_path) as con:
        con.execute(create_stmt)
        console.print(f"📥 Inserting data from {jsonl_path.name}...")

        # Read JSONL
        records = [
            json.loads(line)
            for line in jsonl_path.read_text(encoding="utf-8").splitlines()
        ]

        # Convert dates from string to ISO for DuckDB
        rows = [
            (
                r["id"],
                r["titel"],
                r["type"],
                r["startdatum"],
                r["einddatum"],
                r["goedgekeurd_budget"],
                r["omschrijving"],
                r["advies"],
            )
            for r in records
        ]

        con.executemany(
            f"""INSERT INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",  # noqa: S608
            rows,
        )
