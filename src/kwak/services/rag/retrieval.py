import asyncio
from typing import Any, Literal

import duckdb

from kwak.schemas.dossier import DossierChunk
from kwak.services.factories import EMBEDDING_REGISTRY


def _parse_chunk_row(row: tuple[Any, ...]) -> DossierChunk:
    """Convert a DuckDB result row into a DossierChunk instance."""
    dossier_id = str(row[0])
    origin_raw = str(row[1])
    content = str(row[2])
    type_ = str(row[3])
    title = str(row[4])
    startdatum = row[5]  # Assumed already a datetime.date
    einddatum = row[6]
    budget = float(row[7])  # Might be Decimal

    if origin_raw not in ("omschrijving", "advies"):
        msg = f"Invalid origin value: {origin_raw}"
        raise ValueError(msg)
    from typing import cast

    origin: Literal["omschrijving", "advies"] = cast(
        "Literal['omschrijving', 'advies']", origin_raw
    )

    return DossierChunk(
        dossier_id=dossier_id,
        origin=origin,
        content=content,
        type=type_,
        title=title,
        startdatum=startdatum,
        einddatum=einddatum,
        goedgekeurd_budget=budget,
    )


def search_chunks(
    query: str,
    provider: str = "openai",
    top_k: int = 5,
) -> list[DossierChunk]:
    """Embed a user query and return the top_k most relevant chunks
    from the DuckDB database based on cosine similarity.
    """
    if provider not in EMBEDDING_REGISTRY:
        msg = f"Unsupported embedding provider: {provider}"
        raise ValueError(msg)

    # Generate query embedding (e.g., 1536-dim OpenAI vector)
    embedder = EMBEDDING_REGISTRY[provider]()
    embedding = asyncio.run(embedder.embed([query]))[0]

    # Convert Python list to DuckDB-compatible FLOAT[1536] array literal
    duck_array = "CAST([" + ", ".join(str(v) for v in embedding) + "] AS FLOAT[1536])"

    # Search for top_k most similar chunks using array_cosine_similarity
    con = duckdb.connect("data/kwak.db")
    results = con.execute(
        f"""
        SELECT
            dossier_id,
            origin,
            content,
            type,
            titel,
            startdatum,
            einddatum,
            goedgekeurd_budget,
            array_cosine_similarity(embedding, {duck_array}) AS score
        FROM chunk_embeddings e
        INNER JOIN dossiers d ON e.dossier_id = d.id
        WHERE e.embedding IS NOT NULL
        ORDER BY score DESC
        LIMIT {top_k}
        """  # noqa: S608
    ).fetchall()

    return [_parse_chunk_row(row) for row in results]
