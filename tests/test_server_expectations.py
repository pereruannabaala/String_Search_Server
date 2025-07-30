import socket
import os
import ssl
import pytest
from pathlib import Path
from typing import Tuple
from server.server import StringSearchServer

def create_temp_config(tmp_path: Path, content: str) -> str:
    """
    Create a temporary config file in tmp_path.
    Automatically convert relative linuxpath entries to absolute paths.
    """
    lines = []
    for line in content.strip().splitlines():
        if line.startswith("linuxpath="):
            _, value = line.split("=", 1)
            value = value.strip()
            if not os.path.isabs(value):
                value = str(tmp_path / value)
            line = f"linuxpath={value}"
        lines.append(line)
    config_path = tmp_path / "config.txt"
    config_path.write_text("\n".join(lines))
    return str(config_path)


def test_missing_config(tmp_path: Path) -> None:
    """Test SystemExit when config.txt is missing."""
    config_path: Path = tmp_path / "nonexistent_config.txt"
    with pytest.raises(SystemExit) as exc:
        StringSearchServer(config_path=str(config_path))
    assert "Config file not found" in str(exc.value)


def test_missing_linuxpath(tmp_path: Path) -> None:
    """Test SystemExit when linuxpath key is missing."""
    config_path: str = create_temp_config(tmp_path, "max_payload=1024\n")
    with pytest.raises(SystemExit) as exc:
        StringSearchServer(config_path=config_path)
    assert "Missing 'linuxpath'" in str(exc.value)

def test_file_not_found(tmp_path: Path) -> None:
    """Test SystemExit when the data file does not exist."""
    config_path: str = create_temp_config(tmp_path, "linuxpath=nonexistent.txt\n")
    with pytest.raises(SystemExit) as exc:
        StringSearchServer(config_path=config_path)
    assert "Failed to load file" in str(exc.value)


def test_empty_query(tmp_path: Path) -> None:
    """Test sending an empty query."""
    data_file: Path = tmp_path / "test_data.txt"
    data_file.write_text("apple\nbanana\n")
    config_path: str = create_temp_config(tmp_path, f"linuxpath={data_file}\n")

    data_file.write_text("apple\nbanana\n")

    server = StringSearchServer(config_path=config_path)
    sock1, sock2 = socket.socketpair()
    with sock1, sock2:
        sock1.shutdown(socket.SHUT_WR)  # Ensure recv() returns EOF
        server.handle_client(sock2, ("127.0.0.1", 0))
        response: str = sock1.recv(1024).decode("utf-8")
        assert "STRING NOT FOUND" in response


def test_query_too_large(tmp_path: Path) -> None:
    """Test sending a query larger than max_payload."""
    data_file: Path = tmp_path / "test_data.txt"
    data_file.write_text("apple\nbanana\n")
    config_path: str = create_temp_config(tmp_path, f"linuxpath={data_file}\nmax_payload=10\n")


    server = StringSearchServer(config_path=config_path)
    sock1, sock2 = socket.socketpair()
    with sock1, sock2:
        large_query: bytes = b"a" * 50
        sock1.sendall(large_query)
        sock1.shutdown(socket.SHUT_WR)
        server.handle_client(sock2, ("127.0.0.1", 0))
        response: str = sock1.recv(1024).decode("utf-8")
        assert "QUERY TOO LARGE" in response


def test_invalid_encoding(tmp_path: Path) -> None:
    """Test query with invalid UTF-8 encoding."""
    data_file: Path = tmp_path / "test_data.txt"
    data_file.write_text("apple\nbanana\n")
    config_path: str = create_temp_config(tmp_path, f"linuxpath={data_file}\n")


    server = StringSearchServer(config_path=config_path)
    sock1, sock2 = socket.socketpair()
    with sock1, sock2:
        sock1.sendall(b"\xff\xfe")  # Invalid UTF-8
        sock1.shutdown(socket.SHUT_WR)
        server.handle_client(sock2, ("127.0.0.1", 0))
        response: str = sock1.recv(1024).decode("utf-8")
        assert "INVALID ENCODING" in response


def test_ssl_setup_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test SSL setup failure."""
    config_path: str = create_temp_config(tmp_path, "linuxpath=test_data.txt\nuse_ssl=True\n")
    data_file: Path = tmp_path / "test_data.txt"
    data_file.write_text("apple\nbanana\n")

    # Patch SSL context to raise an error
    monkeypatch.setattr(
        ssl.SSLContext,
        "load_cert_chain",
        lambda *a, **k: (_ for _ in ()).throw(ssl.SSLError("bad cert")),
    )
    with pytest.raises(SystemExit) as exc:
        server = StringSearchServer(port=0, config_path=config_path)
        server.start()
    assert "SSL setup failed" in str(exc.value)
