import socket
import ssl
import threading
import time
import pytest
from pathlib import Path
from typing import Tuple, Generator
from server.server import StringSearchServer
from server.file_search import load_file

HOST = "127.0.0.1"

def get_free_port() -> int:
    """Find and return a free TCP port from the OS."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        addr, port = s.getsockname()
        return int(port)

@pytest.fixture(scope="function", autouse=True)
def start_test_server(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[Tuple[StringSearchServer, int], None, None]:
    """Start a test server in a background thread for client tests."""
    tmp_path: Path = tmp_path_factory.mktemp("config")
    data_file: Path = tmp_path / "test_data.txt"
    data_file.write_text("apple\nbanana\n")

    config_file: Path = tmp_path / "config.txt"
    config_file.write_text(
        f"linuxpath={data_file}\n"
        "max_payload=1024\n"
        "reread_on_query=True\n"
        "use_ssl=True\n"
    )

    port: int = get_free_port()
    server: StringSearchServer = StringSearchServer(port=port, config_path=str(config_file))
    server.use_ssl = False
    server_thread: threading.Thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()

    # Wait for the server to start
    for _ in range(10):
        try:
            with socket.create_connection((HOST, port), timeout=0.1):
                break
        except (ConnectionRefusedError, OSError):
            time.sleep(0.1)
    else:
        raise RuntimeError("Server failed to start in time")

    yield server, port
    server.stop()
    server_thread.join(timeout=1)

def send_query(message: str, port: int, use_ssl: bool = True) -> str:
    """Send a query to the test server with optional SSL."""
    sock = socket.create_connection((HOST, port))

    if use_ssl:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        sock = context.wrap_socket(sock, server_hostname=HOST)

    sock.sendall(message.encode("utf-8"))
    response = sock.recv(4096).decode("utf-8").strip()
    sock.close()
    return response


def test_valid_query_response(start_test_server: Tuple[StringSearchServer, int]) -> None:
    server, port = start_test_server
    response: str = send_query("apple", port, use_ssl=server.use_ssl)
    assert response in ["STRING EXISTS", "STRING NOT FOUND"]

def test_invalid_query_response(start_test_server: Tuple[StringSearchServer, int]) -> None:
    """Ensure invalid query returns 'STRING NOT FOUND'."""
    server, port = start_test_server
    response = send_query("nonexistentqueryxyz", port, use_ssl=server.use_ssl)
    assert response == "STRING NOT FOUND"

def test_empty_query_response(start_test_server: Tuple[StringSearchServer, int]) -> None:
    """Test that an empty query returns 'STRING NOT FOUND'."""
    server, port = start_test_server
    response = send_query("\n", port, use_ssl=server.use_ssl)
    assert response == "STRING NOT FOUND"


def test_oversized_query_response(start_test_server: Tuple[StringSearchServer, int]) -> None:
    """Test that an oversized query is rejected with 'QUERY TOO LARGE'."""
    server, port = start_test_server
    oversized = "a" * 2048  # well over 1024 max_payload
    response = send_query(oversized, port, use_ssl=server.use_ssl)
    assert response == "QUERY TOO LARGE"


def test_invalid_encoding_response(start_test_server: Tuple[StringSearchServer, int]) -> None:
    """Send bytes that are not valid UTF-8 and expect 'INVALID ENCODING'."""
    server, port = start_test_server
    sock = socket.create_connection((HOST, port))
    sock.sendall(b'\xff\xfe\xfd')  # Invalid UTF-8 bytes
    response = sock.recv(4096).decode("utf-8").strip()
    assert response == "INVALID ENCODING"
    sock.close()


def test_ssl_query_response(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Ensure server supports SSL if configured."""
    tmp_path = tmp_path_factory.mktemp("ssl_config")
    data_file = tmp_path / "test_data.txt"
    data_file.write_text("securedata\n")

    config_file = tmp_path / "config.txt"
    config_file.write_text(
        f"linuxpath={data_file}\n"
        "max_payload=1024\n"
        "reread_on_query=False\n"
        "use_ssl=True\n"
    )

    # You must generate your own cert.pem and key.pem beforehand in ssl/ folder
    port = get_free_port()
    server = StringSearchServer(port=port, config_path=str(config_file))
    server.use_ssl = True

    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()

    # Wait for server
    for _ in range(10):
        try:
            with socket.create_connection((HOST, port), timeout=0.1):
                break
        except (ConnectionRefusedError, OSError):
            time.sleep(0.1)
    else:
        raise RuntimeError("SSL Server did not start in time")

    response = send_query("securedata", port, use_ssl=True)
    assert response in ["STRING EXISTS", "STRING NOT FOUND"]

    server.stop()
    server_thread.join(timeout=1)


def test_server_fails_on_missing_data_file(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Ensure server exits if the data file is missing."""
    tmp_path = tmp_path_factory.mktemp("missing_data")
    config_file = tmp_path / "config.txt"
    config_file.write_text(
        f"linuxpath={tmp_path}/nonexistent.txt\n"
        "max_payload=1024\n"
    )
    with pytest.raises(SystemExit):
        _ = StringSearchServer(config_path=str(config_file))


def test_server_fails_on_missing_config_file() -> None:
    """Ensure server exits if config file is missing."""
    with pytest.raises(SystemExit):
        _ = StringSearchServer(config_path="nonexistent_config.txt")

def test_load_file_failure_triggers_sysexit(monkeypatch):
    """Simulate file open failure and ensure SystemExit is raised."""

    def mock_open(*args, **kwargs):
        raise IOError("simulated open failure")

    # Patch the built-in open used in load_file
    monkeypatch.setattr("builtins.open", mock_open)

    with pytest.raises(SystemExit) as excinfo:
        load_file("fake.txt")

    assert "❌ Failed to load file" in str(excinfo.value)



