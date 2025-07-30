from pathlib import Path
from typing import Dict
import pytest

from server.config import read_config


def create_temp_config(tmp_path: Path, content: str) -> Path:
    """
    Create a temporary configuration file with the specified content and return its path.
    """
    config_file = tmp_path / "config.txt"
    config_file.write_text(content)
    return config_file


def test_valid_config(tmp_path: Path) -> None:
    """
    Check that a valid configuration file is read appropriately.
    """
    content = "host=127.0.0.1\nport=44445\nuse_ssl=True\n"
    config_path = create_temp_config(tmp_path, content)

    config: Dict[str, str] = read_config(str(config_path))
    assert config["host"] == "127.0.0.1"
    assert config["port"] == "44445"
    assert config["use_ssl"] == "True"


def test_config_with_extra_spaces(tmp_path: Path) -> None:
    """
    Test configuration lines that contain additional spaces and newlines.
    """
    content = " host =  127.0.0.1 \n port = 44445 \n\nuse_ssl= False  "
    config_path = create_temp_config(tmp_path, content)

    config: Dict[str, str] = read_config(str(config_path))
    assert config["host"] == "127.0.0.1"
    assert config["port"] == "44445"
    assert config["use_ssl"] == "False"


def test_config_with_comments_and_blank_lines(tmp_path: Path) -> None:
    """
    Test that comments and blank lines are ignored.
    """
    content = """
# This is a comment
host=localhost

# Another comment
port=44445
"""
    config_path = create_temp_config(tmp_path, content)

    config: Dict[str, str] = read_config(str(config_path))
    assert config["host"] == "localhost"
    assert config["port"] == "44445"

def test_invalid_config_line(tmp_path: Path) -> None:
    """
    Check that invalid configuration lines (missing '=') are skipped.
    """
    content = "host=localhost\ninvalid_line\nport=44445\n"
    config_path = create_temp_config(tmp_path, content)

    config: Dict[str, str] = read_config(str(config_path))
    assert "host" in config
    assert "port" in config
    assert "invalid_line" not in config


def test_missing_file_raises(tmp_path: Path) -> None:
    """
    Test that a missing file raises a FileNotFoundError.
    """
    missing_path = tmp_path / "nonexistent_config.txt"
    with pytest.raises(FileNotFoundError):
        read_config(str(missing_path))
