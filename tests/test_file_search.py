import os
import pytest
from server.file_search import load_file, search_string, linear_search
from pathlib import Path

def test_load_file_creates_list(tmp_path: Path) -> None:
    """Test that load_file reads a file and returns a list of strings."""
    file_path = tmp_path / "data.txt"
    file_path.write_text("apple\nbanana\ncherry\n")

    lines = load_file(str(file_path))
    assert isinstance(lines, list)
    assert "apple" in lines
    assert len(lines) == 3

def test_load_file_empty_file(tmp_path: Path) -> None:
    """Test that load_file returns an empty list for an empty file."""
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")
    lines = load_file(str(file_path))
    assert lines == []

def test_load_file_raises_for_nonexistent_file(tmp_path: Path) -> None:
    """Test that load_file raises SystemExit for missing files."""
    fake_path = tmp_path / "no_file.txt"
    with pytest.raises(SystemExit) as exc:
        load_file(str(fake_path))
    assert "Failed to load file" in str(exc.value)

    
def test_load_file_strips_newlines(tmp_path: Path) -> None:
    """Test that load_file strips newlines from file lines."""
    file_path = tmp_path / "data.txt"
    file_path.write_text("apple \n banana\ncherry\n")

    lines = load_file(str(file_path))
    assert all(isinstance(line, str) for line in lines)
    assert "apple" in lines
    assert "banana" in lines
    assert "cherry" in lines

def test_search_string_finds_existing() -> None:
    """Test that search_string returns true if string exists in data."""
    data = ["apple", "banana", "cherry"]
    assert search_string(data, "banana") is True

def test_search_string_returns_false_for_missing() -> None:
    """Test that search_string returns false if string is missing."""
    data = ["apple", "banana", "cherry"]
    assert search_string(data, "mango") is False

def test_search_string_with_empty_data() -> None:
    """Test that search_string returns false for empty data."""
    data: list[str] = []
    assert search_string(data, "apple") is False

def test_search_string_case_sensitive() -> None:
    """Test that search_string is case-sensitive."""
    data = ["apple", "banana", "cherry"]
    assert search_string(data, "Apple") is False  # Different case

def test_linear_search_exact_match() -> None:
    """Test that linear_search returns true when the exact line matches the query."""
    data = ["apple", "banana", "cherry"]
    assert linear_search(data, "banana") is True

def test_linear_search_no_match() -> None:
    """Test that linear_search returns false when the query is not found in the data."""
    data = ["apple", "banana", "cherry"]
    assert linear_search(data, "mango") is False

def test_linear_search_strips_whitespace() -> None:
    """Test that linear_search ignores leading/trailing whitespace in lines during match."""
    data = ["  apple  ", "\tbanana\n", "  cherry "]
    assert linear_search(data, "banana") is True
