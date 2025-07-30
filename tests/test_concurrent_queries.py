from pathlib import Path
from typing import List, cast
import pytest
import socket
import ssl
import threading
import time
from server.server import StringSearchServer

CERT_PATH = "ssl/cert.pem"  # Path to the trusted self-signed cert


def get_free_port() -> int:
    """Get a free port dynamically."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        host, port = s.getsockname()
        return cast(int, port)


def get_test_ssl_context() -> ssl.SSLContext:
    """Return an SSL context that trusts the self-signed certificate."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(CERT_PATH)  # Load the self-signed cert
    return context


def wait_for_server(host: str, port: int, timeout: float = 2.0) -> None:
    """Wait until the server is listening and supports the SSL handshake."""
    start = time.time()
    context = get_test_ssl_context()

    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.2) as sock:
                with context.wrap_socket(sock, server_hostname=host):
                    return
        except (OSError, ssl.SSLError):
            time.sleep(0.05)
    raise RuntimeError(f"Server did not start on {host}:{port} in time.")


def test_concurrent_queries(tmp_path_factory: pytest.TempPathFactory) -> None:
    """
    Test that the server can handle multiple concurrent queries with SSL enabled.
    """
    tmp_path: Path = tmp_path_factory.mktemp("data")
    data_file: Path = tmp_path / "strings.txt"
    data_file.write_text("apple\nbanana\ncherry\n")

    config_file: Path = tmp_path / "config.txt"
    config_file.write_text(
        f"linuxpath={data_file}\n"
        "max_payload=1024\n"
        "use_ssl=True\n"
    )

    port: int = get_free_port()
    server: StringSearchServer = StringSearchServer(port=port, config_path=str(config_file))
    server_thread: threading.Thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()

    wait_for_server("127.0.0.1", port)

    queries: List[str] = ["apple", "banana", "grape", "cherry"]
    responses: List[str] = []

    def send_query(q: str) -> None:
        try:
            context = get_test_ssl_context()
            with socket.create_connection(("127.0.0.1", port)) as sock:
                with context.wrap_socket(sock, server_hostname="127.0.0.1") as ssock:
                    ssock.sendall(q.encode("utf-8"))
                    response: str = ssock.recv(1024).decode("utf-8").strip()
                    responses.append(response)
        except (ConnectionResetError, ssl.SSLError):
            responses.append("")

    threads: List[threading.Thread] = [threading.Thread(target=send_query, args=(q,)) for q in queries]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    server.stop()
    if server.sock is not None:
        server.sock.close()
    server_thread.join(timeout=1)

    assert any("STRING EXISTS" in r for r in responses if r), f"Responses: {responses}"
