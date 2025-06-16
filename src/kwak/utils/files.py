from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_jsonl(path: Path, model: type[T]) -> list[T]:
    """Load a JSON Lines file and parse each line into a Pydantic model instance."""
    return [
        model.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def append_jsonl(path: Path, data: list[T]) -> None:
    """Append a list of Pydantic model instances to a JSON Lines file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for item in data:
            f.write(item.model_dump_json() + "\n")


def overwrite_jsonl(path: Path, data: list[T]) -> None:
    """Overwrite a JSON Lines file with a list of Pydantic model instances."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in data:
            f.write(item.model_dump_json() + "\n")
