import socket
import ssl
import time
from typing import Any, Dict
from server.config import read_config


def send_query(query: str, use_ssl: bool, host: str, port: int) -> bool:
    """
    Send a single query to the server and returns true if the response is valid.
    """
    try:
        sock: socket.socket = socket.create_connection((host, port), timeout=2)
        if use_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED
            sock = context.wrap_socket(sock, server_hostname=host)

        sock.sendall(query.encode("utf-8"))
        response: str = sock.recv(1024).decode("utf-8")
        sock.close()
        return "STRING EXISTS" in response or "STRING NOT FOUND" in response
    except Exception:
        return False


def stress_test() -> None:
    """
    Perform a stress test by sending multiple batches of queries to the server.
    """
    config: Dict[str, Any] = read_config("config.txt")
    host: str = config.get("host", "127.0.0.1")
    port: int = int(config.get("port", 44445))
    use_ssl: bool = bool(config.get("use_ssl", False))
    query: str = config.get("test_query", "5;0;6;28;0;20;3;0;")

    batch_size: int = 50
    max_batches: int = 40  # up to 2000 queries
    total_sent: int = 0
    failures: int = 0

    for batch in range(1, max_batches + 1):
        start: float = time.time()
        success: int = 0

        for _ in range(batch_size):
            if send_query(query, use_ssl, host, port):
                success += 1
            else:
                failures += 1

        end: float = time.time()
        total_sent += batch_size
        elapsed: float = end - start
        print(
            f"Batch {batch}: {batch_size} queries in {elapsed:.2f}s — "
            f"success: {success}, failed: {batch_size - success}"
        )

        if success < batch_size:
            print("❌ Server started dropping or failing queries, likely reached limit.")
            break

    print(f"\nTotal Queries Sent: {total_sent}")
    print(f"Total Failures: {failures}")


if __name__ == "__main__":
    stress_test()