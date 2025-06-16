import asyncio
from pathlib import Path

import duckdb
import typer
from rich.console import Console
from rich.progress import Progress

from kwak.schemas.dossier import SubsidieDossier
from kwak.services.chunkers.semantic import SemanticChunker
from kwak.services.chunkers.word_count import WordCountChunker
from kwak.services.factories import GENERATOR_REGISTRY
from kwak.utils.files import append_jsonl, load_jsonl, overwrite_jsonl

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
    append_jsonl(output, dossiers)

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
        records = load_jsonl(
            Path("data/generated/subsidiedossiers.jsonl"), model=SubsidieDossier
        )

        # Convert dates from string to ISO for DuckDB
        rows = [
            (
                r.id,
                r.titel,
                r.type,
                r.startdatum,
                r.einddatum,
                r.goedgekeurd_budget,
                r.omschrijving,
                r.advies,
            )
            for r in records
        ]

        con.executemany(
            f"""INSERT INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",  # noqa: S608
            rows,
        )


@app.command()
def chunk_data(
    range: str = typer.Option(  # noqa: A002
        "all",
        help="Which jsonl objects to parse: 'all', 'first:N' of 'last:N'",
    ),
    strategy: str = typer.Option(
        "semantic",
        "--strategy",
        "-s",
        help="Chunking strategy: 'semantic' (LLM) of 'wordcount' (naïef)",
    ),
) -> None:
    """Split dossiers into semantic chunks and store them as JSONL."""
    chunker: SemanticChunker | WordCountChunker
    if strategy == "semantic":
        chunker = SemanticChunker()
    elif strategy == "wordcount":
        chunker = WordCountChunker()
    else:
        console.print(
            "[red]❌ Invalid strategy. Choose 'semantic' or 'wordcount'.[/red]"
        )
        raise typer.Exit(code=1)

    dossiers = load_jsonl(
        Path("data/generated/subsidiedossiers.jsonl"), model=SubsidieDossier
    )

    if range == "all":
        # If the user specified "all", include all dossiers
        selected = dossiers

    elif range.startswith("first:"):
        # If the range starts with "first:", extract the number after the colon
        # and select the first N dossiers from the list
        n = int(range.split(":")[1])
        selected = dossiers[:n]

    elif range.startswith("last:"):
        # If the range starts with "last:", extract the number after the colon
        # and select the last N dossiers from the list
        n = int(range.split(":")[1])
        selected = dossiers[-n:]
    else:
        console.print("[red]❌ Invalid range. Use 'all', 'first:N' of 'last:N'.[/red]")
        raise typer.Exit(code=1)

    all_chunks = []
    for dossier in selected:
        chunks = list(chunker.chunk(dossier))
        all_chunks.extend(chunks)

    overwrite_jsonl(Path("data/chunks/subsidiedossierchunks.jsonl"), all_chunks)
    console.print(
        f"✅ [green]Chunked {len(selected)} dossiers into {len(all_chunks)} chunks[/green]"  # noqa: E501
    )
