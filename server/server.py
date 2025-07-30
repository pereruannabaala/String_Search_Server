import socket
import ssl
import threading
import time
from ssl import SSLSocket
from typing import Set, Optional, Mapping, Union
from server.config import read_config
from server.file_search import load_file, search_string
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)

class StringSearchServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 44445, config_path: Optional[str] = "config.txt") -> None:
        try:
            self.config: Mapping[str, Union[str, bool, int]] = read_config(config_path or "config.txt")
        except FileNotFoundError:
            raise SystemExit("❌ Config file not found. Please ensure config.txt exists.")

        self.host: str = host
        self.port: int = port
        self.file_path: str = str(self.config.get("linuxpath", ""))

        if not self.file_path:
            raise SystemExit("❌ Missing 'linuxpath' in config.txt.")

        self.reread_on_query: bool = str(self.config.get("reread_on_query", "False")).lower() == "true"
        self.max_payload: int = int(self.config.get("max_payload", 1024))
        self.use_ssl: bool = bool(self.config.get("use_ssl", False))

        try:
            self.data: Set[str] = set() if self.reread_on_query else set(load_file(self.file_path))
        except FileNotFoundError:
            raise SystemExit(f"❌ File {self.file_path} not found.")
        except Exception as e:
            raise SystemExit(f"❌ Failed to load file: {e}")
        
        self.running: bool = False

    def handle_client(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        start_time: float = time.time()
        try:
            raw_bytes = conn.recv(self.max_payload + 1)  # Read max_payload + 1 bytes.

            if not raw_bytes:
                conn.sendall(b"STRING NOT FOUND\n")
                return

            if len(raw_bytes) > self.max_payload:
                conn.sendall(b"QUERY TOO LARGE\n")
                return

            if not raw_bytes:
                conn.sendall(b"STRING NOT FOUND\n")
                return
            try:
                query: str = raw_bytes.decode("utf-8").strip()
            except UnicodeDecodeError:
                conn.sendall(b"INVALID ENCODING\n")
                return

            if len(query) == 0:
                conn.sendall(b"STRING NOT FOUND\n")
                return

            if len(query) > self.max_payload:
                conn.sendall(b"QUERY TOO LARGE\n")
                return

            data: Set[str] = set(load_file(self.file_path)) if self.reread_on_query else self.data
            exists: bool = search_string(data, query)
            response: str = "STRING EXISTS\n" if exists else "STRING NOT FOUND\n"
            conn.sendall(response.encode("utf-8"))

            elapsed: float = (time.time() - start_time) * 1000
            logging.info(f"Query: '{query}' | IP: {addr[0]} | Time: {elapsed:.2f}ms")

        except (ConnectionResetError, BrokenPipeError):
            logging.error(f"Connection with {addr} was reset.")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            try:
                conn.shutdown(socket.SHUT_WR)
            except Exception:
                pass
            conn.close()

    def start(self) -> None:
        logging.info(f"Server starting on {self.host}:{self.port} (SSL: {self.use_ssl})")
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.sock.bind((self.host, self.port))
            if self.port == 0:
                self.port = self.sock.getsockname()[1]
                logging.info(f"Server dynamically bound to port {self.port}")

            self.sock.listen()
            self.sock.settimeout(1.0)  # Allow a clean shutdown

            if self.use_ssl:
                try:
                    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                    context.load_cert_chain(certfile="ssl/cert.pem", keyfile="ssl/key.pem")
                    self.sock = context.wrap_socket(self.sock, server_side=True)
                except ssl.SSLError as e:
                    raise SystemExit(f"❌ SSL setup failed: {e}")

            logging.info("Server is listening for incoming connections...")
            while self.running:
                try:
                    conn, addr = self.sock.accept()
                    thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                    thread.start()
                except socket.timeout:
                    continue
                except ssl.SSLError as e:
                    logging.error(f"❌ SSL handshake failed: {e}")
                    continue
                except OSError as e:
                    if self.running:
                        logging.error(f"Accept failed: {e}")
                    break
        except OSError as e:
            raise SystemExit(f"❌ Could not start server: {e}")
        finally:
            self.sock.close()

    
    def stop(self) -> None:
        """Stop the server gracefully."""
        self.running = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        finally:
            self.sock.close()


if __name__ == "__main__":
    server = StringSearchServer()
    server.start()
