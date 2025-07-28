from typing import Set, Iterable,List

def linear_search(data: list[str], query: str) -> bool:
    """Return True if the query matches an entire line."""
    for line in data:
        if line.strip() == query:
            return True
    return False

# server/file_search.py

def load_file(path: str) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        raise SystemExit(f"❌ Failed to load file: {e}")

def search_string(data: Iterable[str], query: str) -> bool:
    """
    Searches for a query string in the provided dataset.
    """
    return query in data
