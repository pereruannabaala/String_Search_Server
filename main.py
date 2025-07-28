# Import the main TCP server class responsible for handling incoming string queries
from server.server import StringSearchServer

if __name__ == "__main__":
    server = StringSearchServer()
    server.start()