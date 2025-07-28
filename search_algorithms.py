import subprocess
import mmap
import bisect
import re
import os
from typing import Union

PathType = Union[str, os.PathLike[str]]


def linear_search_python(filepath: PathType, query: str) -> bool:
    """1. Pure Python line-by-line search."""
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() == query:
                return True
    return False


def set_lookup(filepath: PathType, query: str) -> bool:
    """2. Loads all lines into a set, then checks membership."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = {line.strip() for line in f}
    return query in lines


def grep_search(filepath: PathType, query: str) -> bool:
    """3. Uses `grep` command for exact full-line search."""
    result = subprocess.run(
        ["grep", "-Fxq", query, str(filepath)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def mmap_search(filepath: PathType, query: str) -> bool:
    """4. Uses memory-mapped file for fast binary search."""
    with open(filepath, "r", encoding="utf-8") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            return f"{query}\n".encode() in mm


def bisect_search(sorted_filepath: PathType, query: str) -> bool:
    """5. Binary search on pre-sorted files."""
    with open(sorted_filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f]
    index = bisect.bisect_left(lines, query)
    return index < len(lines) and lines[index] == query


def regex_search(filepath: PathType, query: str) -> bool:
    """6. Regex-based search for exact match."""
    pattern = re.compile(rf"^{re.escape(query)}$")
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if pattern.match(line.strip()):
                return True
    return False


def numpy_search(filepath: PathType, query: str) -> bool:
    """7. Uses NumPy for vectorized comparison (bonus method)."""
    try:
        import numpy as np
    except ImportError:
        raise ImportError("numpy is required for numpy_search")

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f]
    return query in np.array(lines)
