import socket
from pathlib import Path
from typing import List
import pytest
from server.server import StringSearchServer


def create_temp_config(tmp_path: Path, content: str) -> Path:
    """Create a temporary configuration file to test logging."""
    config_file = tmp_path / "config.txt"
    config_file.write_text(content)
    return config_file


def test_server_start_logging(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Check that launching the server produces the expected message."""
    data_file = tmp_path / "test_data.txt"
    data_file.write_text("apple\nbanana\n")
    config_path = create_temp_config(tmp_path, f"linuxpath={data_file}\n")

    server = StringSearchServer(port=0, config_path=str(config_path))
def test_handle_client_logs_query(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that handle_client logs a query message."""
    data_file = tmp_path / "test_data.txt"
    data_file.write_text("apple\nbanana\n")
    config_path = create_temp_config(tmp_path, f"linuxpath={data_file}\n")

    server = StringSearchServer(config_path=str(config_path))

def test_handle_client_logs_error(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that handle_client logs an error when a broken connection occurs."""
    # Create the data file
    data_file = tmp_path / "test_data.txt"
    data_file.write_text("apple\nbanana\n")

    # Use absolute path in config
    config_path = create_temp_config(tmp_path, f"linuxpath={data_file}\n")

    server = StringSearchServer(config_path=str(config_path))
    caplog.set_level("ERROR")

    sock1, sock2 = socket.socketpair()
    with sock1, sock2:
        # Simulate abrupt close
        sock1.close()
        server.handle_client(sock2, ("127.0.0.1", 0))

    logs: List[str] = [rec.getMessage() for rec in caplog.records]
    assert any("Connection with" in log for log in logs)