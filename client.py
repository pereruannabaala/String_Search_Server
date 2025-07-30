import socket
import ssl
import sys
from typing import Union, Optional
from server.config import read_config


def create_connection(host: str, port: int, use_ssl: bool) -> Union[socket.socket, ssl.SSLSocket]:
    """
    Create a TCP or SSL-wrapped connection to the given host and port.
    Trusts a self-signed certificate located in the 'ssl/cert.pem' path.
    """
    try:
        sock: socket.socket = socket.create_connection((host, port), timeout=5)
        if use_ssl:
            context: ssl.SSLContext = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

            # Load and trust the self-signed certificate manually
            context.load_verify_locations("ssl/cert.pem")
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED

            ssl_sock: ssl.SSLSocket = context.wrap_socket(sock, server_hostname=host)
            return ssl_sock
        return sock
    except (socket.timeout, ConnectionRefusedError):
        raise SystemExit("❌ Connection failed: Server is unreachable.")
    except ssl.SSLError as e:
        raise SystemExit(f"❌ SSL Error: {e}")


def main() -> None:
    """
    Entry point for the client script.
    Reads configuration and sends a search query to the server.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 client.py <search_string>")
        return

    query: str = sys.argv[1]
    config: dict[str, str] = read_config("config.txt")

    host: str = str(config.get("host", "127.0.0.1"))
    port: int = int(config.get("port", 44445))
    use_ssl: bool = bool(config.get("use_ssl", False))

    try:
        sock: Union[socket.socket, ssl.SSLSocket]
        with create_connection(host, port, use_ssl) as sock:
            sock.sendall(query.encode("utf-8"))
            response: bytes = sock.recv(1024)
            print("Server response:", response.decode("utf-8").strip())
    except Exception as e:
        print(f"❌ {e}")


if __name__ == "__main__":
    main()
