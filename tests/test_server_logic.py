import socket
import ssl
import threading
import time
import pytest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from typing import Tuple, Generator, Any
from server.server import StringSearchServer
from server.file_search import load_file
from _pytest.monkeypatch import MonkeyPatch


HOST = "127.0.0.1"

def get_free_port() -> int:
    """Find and return a free TCP port from the OS."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        _, port = s.getsockname()
        return int(port)

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


@pytest.fixture(scope="function", autouse=True)
def start_test_server(tmp_path_factory: pytest.TempPathFactory) -> Generator[Tuple[StringSearchServer, int], None, None]:
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

# ------------------------- Query Tests -------------------------

def test_valid_query_response(start_test_server: Tuple[StringSearchServer, int]) -> None:
    server, port = start_test_server
    response: str = send_query("apple", port, use_ssl=server.use_ssl)
    assert response in ["STRING EXISTS", "STRING NOT FOUND"]

def test_invalid_query_response(start_test_server: Tuple[StringSearchServer, int]) -> None:
    server, port = start_test_server
    response = send_query("nonexistentqueryxyz", port, use_ssl=server.use_ssl)
    assert response == "STRING NOT FOUND"

def test_empty_query_response(start_test_server: Tuple[StringSearchServer, int]) -> None:
    server, port = start_test_server
    response = send_query("\n", port, use_ssl=server.use_ssl)
    assert response == "STRING NOT FOUND"

def test_oversized_query_response(start_test_server: Tuple[StringSearchServer, int]) -> None:
    server, port = start_test_server
    oversized = "a" * 2048
    response = send_query(oversized, port, use_ssl=server.use_ssl)
    assert response == "QUERY TOO LARGE"

def test_invalid_encoding_response(start_test_server: Tuple[StringSearchServer, int]) -> None:
    server, port = start_test_server
    sock = socket.create_connection((HOST, port))
    sock.sendall(b'\xff\xfe\xfd')
    response = sock.recv(4096).decode("utf-8").strip()
    assert response == "INVALID ENCODING"
    sock.close()

# ------------------------- SSL Test -------------------------

def test_ssl_query_response(tmp_path_factory: pytest.TempPathFactory) -> None:
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

    port = get_free_port()
    server = StringSearchServer(port=port, config_path=str(config_file))
    server.use_ssl = True

    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()

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

# ------------------------- Startup and Config Tests -------------------------

def test_server_fails_on_missing_data_file(tmp_path_factory: pytest.TempPathFactory) -> None:
    tmp_path = tmp_path_factory.mktemp("missing_data")
    config_file = tmp_path / "config.txt"
    config_file.write_text(
        f"linuxpath={tmp_path}/nonexistent.txt\n"
        "max_payload=1024\n"
    )
    with pytest.raises(SystemExit):
        _ = StringSearchServer(config_path=str(config_file))

def test_server_fails_on_missing_config_file() -> None:
    with pytest.raises(SystemExit):
        _ = StringSearchServer(config_path="nonexistent_config.txt")

# ------------------------- File Load Exception Handling -------------------------

def test_init_raises_system_exit_when_file_path_not_found(tmp_path: Path) -> None:
    config_path = tmp_path / "config.txt"
    config_path.write_text("linuxpath=nonexistent_file.txt\nreread_on_query=False")

    with pytest.raises(SystemExit) as excinfo:
        StringSearchServer(config_path=str(config_path))

    msg = str(excinfo.value)
    assert "Failed to load file" in msg

def test_init_raises_system_exit_on_unexpected_load_file_error(tmp_path: Path) -> None:
    config_path = tmp_path / "config.txt"
    config_path.write_text("linuxpath=somefile.txt\nreread_on_query=False")

    with patch("server.server.load_file", side_effect=RuntimeError("Unexpected error")):
        with pytest.raises(SystemExit) as excinfo:
            StringSearchServer(config_path=str(config_path))
        assert "❌ Failed to load file: Unexpected error" in str(excinfo.value)

def test_load_file_failure_triggers_sysexit(monkeypatch: MonkeyPatch) -> None:
    def mock_open(*args: Any, **kwargs: Any) -> Any:
        raise IOError("simulated open failure")

    monkeypatch.setattr("builtins.open", mock_open)

    with pytest.raises(SystemExit) as excinfo:
        load_file("fake.txt")

    assert "❌ Failed to load file" in str(excinfo.value)

def test_query_too_large(tmp_path: Path) -> None:
    file_path = tmp_path / "data.txt"
    file_path.write_text("example\n")

    config_path = tmp_path / "config.txt"
    config_path.write_text(f"""linuxpath={file_path}
reread_on_query=False
max_payload=10
use_ssl=True
""")

    port = get_free_port()
    server = StringSearchServer(host="127.0.0.1", port=port, config_path=str(config_path))

    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    time.sleep(0.1)

    oversized_query = "x" * 100
    context = ssl._create_unverified_context()
    with context.wrap_socket(socket.socket(socket.AF_INET), server_hostname="127.0.0.1") as client:
        client.connect(("127.0.0.1", port))
        client.sendall(oversized_query.encode())
        response = client.recv(1024).decode()

def test_missing_file_path(tmp_path: Path) -> None:
    config_path = tmp_path / "config.txt"
    config_path.write_text("linuxpath=/nonexistent/path.txt\nuse_ssl=False\n")

    with pytest.raises(SystemExit) as e:
        StringSearchServer(host="127.0.0.1", port=get_free_port(), config_path=str(config_path))

    assert "Failed to load file" in str(e.value)



def test_file_not_found_explicit(tmp_path: Path) -> None:
    # Create a config with a path to a clearly nonexistent file
    missing_file = tmp_path / "does_not_exist.txt"
    config_path = tmp_path / "config.txt"
    config_path.write_text(f"linuxpath={missing_file}\nreread_on_query=False\n")

    with pytest.raises(SystemExit) as e:
        StringSearchServer(host="127.0.0.1", port=get_free_port(), config_path=str(config_path))

    assert "Failed to load file" in str(e.value)


def test_load_file_raises_for_nonexistent_file(tmp_path: Path) -> None:
    """Test that load_file raises SystemExit for missing files."""
    fake_path = tmp_path / "no_file.txt"
    with pytest.raises(SystemExit) as exc:
        load_file(str(fake_path))
    assert "Failed to load file" in str(exc.value)


def create_temp_config(tmp_path: Path, content: str) -> str:
    config_path = tmp_path / "config.txt"
    config_path.write_text(content)
    return str(config_path)


def test_file_not_found(tmp_path: Path) -> None:
    """Test SystemExit when the data file does not exist."""
    config_path: str = create_temp_config(tmp_path, "linuxpath=nonexistent.txt\n")
    with pytest.raises(SystemExit) as exc:
        StringSearchServer(config_path=config_path)
    assert "Failed to load file" in str(exc.value)
