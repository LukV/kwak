import asyncio
import json
from pathlib import Path

import duckdb
import typer
from rich.console import Console
from rich.progress import Progress

from kwak.schemas.dossier import DossierChunk, SubsidieDossier
from kwak.services.chunkers.semantic import SemanticChunker
from kwak.services.chunkers.word_count import WordCountChunker
from kwak.services.factories import (
    COMPLETION_REGISTRY,
    EMBEDDING_REGISTRY,
    GENERATOR_REGISTRY,
)
from kwak.services.rag.retrieval import search_chunks
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
    """Generate synthetic subsidiedossiers."""
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
        raise typer.Exit

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
        f"✅ [green]Chunked {len(selected)} dossiers into {len(all_chunks)} \
            chunks[/green]"
    )


@app.command()
def embed_chunks(
    provider: str = typer.Option("openai", help="Embedding provider: openai or ollama"),
    show: bool = typer.Option(False, help="Print embeddings to terminal"),  # noqa: FBT001, FBT003
) -> None:
    """Generate vector embeddings for each chunk and print or store them."""
    if provider not in EMBEDDING_REGISTRY:
        console.print(f"[red]❌ Unsupported embedding provider: {provider}[/red]")
        raise typer.Exit

    embedder = EMBEDDING_REGISTRY[provider]()

    chunks: list[DossierChunk] = load_jsonl(
        Path("data/chunks/subsidiedossierchunks.jsonl"), model=DossierChunk
    )
    texts = [chunk.content for chunk in chunks]

    console.print(f"🔢 Generating embeddings using {provider}...")
    embeddings = asyncio.run(embedder.embed(texts))

    if not embeddings or len(embeddings) != len(chunks):
        console.print("[red]❌ Embedding mismatch or failure[/red]")
        raise typer.Exit

    dim = len(embeddings[0])
    for i, vector in enumerate(embeddings):
        if len(vector) != dim:
            console.print(f"[red]❌ Inconsistent embedding length at index {i}[/red]")
            raise typer.Exit

    # Prepare table if not exists
    with Path("queries/create_chunk_embeddings.sql").open() as f:
        create_stmt = f.read()

    db_path = "data/kwak.db"
    with duckdb.connect(db_path) as con:
        con.execute(create_stmt)

        rows = [
            (
                chunk.dossier_id,
                chunk.origin,
                idx,
                chunk.content,
                vector,
            )
            for idx, (chunk, vector) in enumerate(zip(chunks, embeddings, strict=False))
        ]

        con.executemany(
            "INSERT INTO chunk_embeddings VALUES (?, ?, ?, ?, ?)",
            rows,
        )

    if show:
        for chunk, vector in zip(chunks, embeddings, strict=False):
            console.print("\n[bold]Chunk:[/bold]", chunk.content[:100])
            console.print(
                "[blue]Vector:[/blue]",
                json.dumps(vector[:5]) + f"... ({len(vector)} dims)",
            )

    # Optional: store in DuckDB later
    console.print(f"✅ [green]Generated {len(embeddings)} embeddings[/green]")


@app.command("ask")
def ask(
    query: str = typer.Argument(..., help="Your search query"),
    provider: str = typer.Option(
        "openai", help="Embedding provider (openai or ollama)"
    ),
    top_k: int = typer.Option(5, help="Number of top results to return"),
    show: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        help="Print the chunks returned from the vector store",
    ),
    model: str = typer.Option(
        "openai", help="LLM to use for answering (openai or ollama)"
    ),
) -> None:
    """Ask a question, retrieve relevant dossier chunks, and generate an answer."""
    console.print(f"[bold blue]🔍 Searching for:[/bold blue] {query}\n")

    try:
        results = search_chunks(query=query, provider=provider, top_k=top_k)
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]❌ Retrieval failed:[/red] {e}")
        raise typer.Exit from None

    if not results:
        console.print("[yellow]⚠️ No results found.[/yellow]")
        raise typer.Exit

    # Generate answer using an LLM
    context = "\n\n".join(c.content for c in results)

    prompt = f"""Beantwoord de volgende vraag zo goed mogelijk op basis van de
context uit subsidiedossiers hieronder.

Vraag: {query}

Context:
{context}

Antwoord:"""

    try:
        completion = COMPLETION_REGISTRY[model]()
        answer = completion.complete(prompt)
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]❌ LLM completion failed:[/red] {e}")
        raise typer.Exit(code=1)  # noqa: B904

    console.rule("[bold green]💡 Antwoord[/bold green]")
    console.print(answer)

    if show:
        for i, chunk in enumerate(results, 1):
            console.rule(f"[green]Result {i}[/green]")
            console.print(f"[bold]Dossier ID:[/bold] {chunk.dossier_id}")
            console.print(f"[bold]Title:[/bold] {chunk.title}")
            console.print(f"[bold]Origin:[/bold] {chunk.origin}")
            console.print("\n[italic]Chunk Content:[/italic]")
            console.print(chunk.content)
            console.print()
