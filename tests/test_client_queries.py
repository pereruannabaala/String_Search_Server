import socket
import ssl
import threading
import time
import pytest
from server.server import StringSearchServer
from typing import cast


HOST = "127.0.0.1"
CERT_PATH = "ssl/cert.pem"  # Path to the trusted self-signed certificate.


def get_free_port() -> int:
    """Return an available port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return cast(int, s.getsockname()[1])


def start_test_server(port: int) -> StringSearchServer:
    """Start the StringSearchServer in a background thread."""
    server = StringSearchServer(host=HOST, port=port)
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    time.sleep(1)  # Allow the server to start.
    return server


def get_test_ssl_context() -> ssl.SSLContext:
    """Return an SSL context that trusts the self-signed cert."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(CERT_PATH)
    return context

def send_query(query: str, port: int, use_ssl: bool = False) -> str:
    """Send a query to the server and return the response."""
    sock = socket.create_connection((HOST, port), timeout=2)

    if use_ssl:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(CERT_PATH) # Load the trusted cert
        sock = context.wrap_socket(sock, server_hostname=HOST)

    sock.sendall(query.encode())
    response = sock.recv(4096).decode()
    sock.close()
    return response


def test_valid_query_response() -> None:
    """Ensure that a legitimate query provides the right response."""
    port = get_free_port()
    start_test_server(port)
    response = send_query("apple", port=port, use_ssl=True)
    assert response.strip() in ["STRING EXISTS", "STRING NOT FOUND"]


def test_invalid_query_response() -> None:
    """Ensure invalid query returns 'STRING NOT FOUND'."""
    port = get_free_port()
    start_test_server(port)
    response = send_query("nonexistentqueryxyz", port=port, use_ssl=True)
    assert response.strip() == "STRING NOT FOUND"

