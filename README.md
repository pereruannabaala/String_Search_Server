# String Search Server

This is a high-performance TCP server designed to search for strings within large text files. In this context, we used the file 200k.txt. The server supports SSL connections, configurable parameters, and can benchmark multiple file-search algorithms when reread_on_query is True or False. It includes a full testing suite (pytest) and benchmarking scripts that generate performance reports in PDF format.

# Features

- **String Search Server**: Responds to client queries with ``STRING EXISTS`` or ``STRING NOT FOUND``.
- **Configurable SSL**: Enable or disable SSL via ``config.txt``.
- **Configurable Reread Mode**: Toggle ``reread_on_query`` for reloading the file on each query.
- **Benchmarking Suite**: Compare algorithms (Linear, Regex, Binary, etc.) with detailed PDF reports.
- **Unit Tests**: Full test coverage using pytest.
- **Linux Service (Daemon) Support**: Run the server as a background service.

# Getting Started

### **Prerequisites**
Make sure you have the following installed:
- Python 3.10+
- ``pip`` (Python package installer)
- ``openssl`` (for generating SSL certificates)

### **Configure the System**
```
host=127.0.0.1
port=44445
linuxpath=200k.txt
reread_on_query=False
max_payload=1024
use_ssl=True
certfile=ssl/cert.pem
keyfile=ssl/key.pem
```

# Project Folders
```
.
├── 200k.txt
├── README.md
├── benchmark_algorithms.py
├── client.py
├── config.txt
├── main.py
├── pdf/
│ ├── execution_time_plot.png 
│ ├── comparison_chart.png
│ ├── results.csv   
│ └── speed_report.pdf
├── requirements.txt
├── run_server.sh
├── server/
│ ├── init.py
│ ├── config.py
│ ├── file_search.py
│ └── server.py
├── ssl/
│ ├── cert.pem
│ └── key.pem
├── stress_test_client.py
├── string_search.service
├── temp_config.txt
└── tests/
├── test_client_queries.py
├── test_concurrent_queries.py
├── test_config.py
├── test_file_search.py
├── test_logging_output.py
├── test_server_expectations.py
└── test_server_logic.py
```

# Input Format and Edge Case Handling

The server accepts UTF-8 encoded strings over a TCP (or optionally SSL) connection and checks for their existence in a predefined dataset (text file).

### **Valid Input Format**
- **Type:** Plain text string
- **Encoding:** UTF-8
- **Max Length:** Defined by max_payload in config.txt (e.g., 1024 characters)
- **Line endings:** Trailing newlines are stripped automatically

### **Examples of Input**
| Input                 | Description            | Expected Response  |
| --------------------- | ---------------------- | ------------------ |
| `apple`               | Exists in file         | `STRING EXISTS`    |
| `nonexistentword`     | Not in file            | `STRING NOT FOUND` |
| *empty string* (`\n`) | Blank input            | `STRING NOT FOUND` |
| `"a" * 2048`          | Exceeds max\_payload   | `QUERY TOO LARGE`  |
| `b'\xff\xfe\xfd'`     | Invalid UTF-8 encoding | `INVALID ENCODING` |

### **Edge Case Handling**
| Case                              | Behavior                         |
| --------------------------------- | -------------------------------- |
| Empty query or only whitespace    | Rejected with `STRING NOT FOUND` |
| Query longer than `max_payload`   | Rejected with `QUERY TOO LARGE`  |
| Invalid UTF-8 bytes sent          | Rejected with `INVALID ENCODING` |
| Missing data file                 | Server exits with an error       |
| Missing or malformed `config.txt` | Server exits with an error       |
| SSL enabled but cert/key missing  | Server fails to start            |

### **Config File ``(config.txt)`` Format**

The configuration file uses key-value pairs:

```
host=127.0.0.1
port=44445
linuxpath=200k.txt
reread_on_query=False
max_payload=1024
use_ssl=True
certfile=ssl/cert.pem
keyfile=ssl/key.pem
```
- ``host=127.0.0.1``: Specifies the IP address where the server will listen for connections. 127.0.0.1 means the server will only accept local connections (localhost).
- ``port=44445``: The port number on which the server will listen. Clients must connect to this port to send search queries.
- ``linuxpath=200k.txt``:
Path to the file in which string searches will be performed. This file should exist in the root directory or the specified relative path.
- `` reread_on_query=False``: 
If ``True``, the server reads the target file from disk every time a query is made. If ``False``, the file is loaded once into memory, improving performance for repeated queries.
- ``max_payload=1024``: Defines the maximum size (in bytes) of incoming client queries. Prevents buffer overflow and excessive memory usage.
- ``use_ssl=True``: Enables SSL/TLS encryption for secure communication. If ``True``, the server will require certificate and key files.
- ``certfile=ssl/cert.pem``:Path to the SSL certificate file used to establish encrypted connections.
- ``keyfile=ssl/key.pem``:Path to the SSL private key corresponding to the certificate above.

# Running the Server

You can run the server in two ways;

**Option 1: Direct Execution**
```
python3 -m server.server
```
or

```
python3 main.py
```

Test with client

```
python3 client.py "5;0;1;26;0;8;4;0;"
```

Results should be;
```
STRING EXISTS
```

**Option 2: Run as a Linux daemon**

Follow the Linux Daemon Setup instructions below.

# Linux Daemon Setup (Systemd Service)

**1. Create the Service File using your terminal**
```bash
sudo nano /etc/systemd/system/string_search.service
```

Paste the code below in the nano terminal
```
[Unit]
Description=String Search TCP Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/<username>/Introductory_Task
ExecStart=/usr/bin/env python3 -m server.server
Restart=always
User=<username>

[Install]
WantedBy=multi-user.target
```
Replace ```<username>``` with your Linux username.

**2. Enable and Start the Service**
```
sudo systemctl daemon-reload
sudo systemctl enable string_search.service
sudo systemctl start string_search.service
```

**3. Test with Client**
```
python3 client.py "5;0;1;26;0;8;4;0;"
```

**4. Manage the Service**
- Check Status
```
sudo systemctl status string_search.service
```
- View logs
```
sudo journalctl -u string_search.service -f
```
- Stop
```
sudo systemctl stop string_search.service
```
- Restart
```
sudo systemctl restart string_search.service
```

# Running Tests
Run all tests with 
```
PYTHONPATH=. pytest --maxfail=1 --disable-warnings -q
```

# Stress Testing
To test the server's performance and measure queries per second (QPS), we use the ``stress_test_client.py`` script.
This script sends a large number of queries to the server in batches and records response times and any failures.

Run the stress test with:
```
python3 stress_test_client.py
``` 

# Benchmarking Different Algorithms 
Run the benchmarked algorithms with;

```
python3 benchmark_algorithms.py
```

# Speed Report Running
How to run:

```
python3 benchmark_algorithms.py
python3 stress_test_client.py
python3 generate_speed_report.py
```

# Configuration
The ``config.txt`` file defines key parameters:
```
linuxpath=200k.txt
max_payload=1024
reread_on_query=False
use_ssl=True
```

- **reread_on_query**

``True`` → Reloads the file on every query (slower, but ensures fresh data).  
``False`` → Preloads data once at server startup (faster).

#  Enabling SSL Authentication
To securely transmit data between the client and server, this project supports SSL/TLS encryption. You’ll need to generate a self-signed SSL certificate and configure your ``config.txt`` accordingly.

### **Files Required**
- ``cert.perm`` - the SSL certificate file
- `` key.perm`` -  the private key file

These will be used by the server to establish encrypted connections with clients.

### **Steps to Generate SSL Certificate and Key**

**1. Generate private key**
```
openssl genrsa -out key.pem 2048
```

**2. Create a certificate signing request(CSR)**
```
openssl req -new -key key.pem -out cert.csr
```
- When prompted for ``Common Name (CN)``, enter:
```
localhost
```

**3. Generate a self-signed certificate**
```
openssl x509 -req -days 365 -in cert.csr -signkey key.pem -out cert.pem
```

**4. Organize the SSL files:**
Move your generated files to the ``ssl/`` folder in the root directory of the project:
```
Introductory-Task/
├── ssl/
│   ├── cert.pem
│   └── key.pem
```

5. Update your ``config.txt`` file to enable SSL:
```
use_ssl=True
certfile=ssl/cert.pem
keyfile=ssl/key.pem
```

### **Running the Server with SSL**
When ``use_ssl=True`` is set in ``config.txt``, the server will wrap the socket using the provided certificate and key, enabling encrypted communication with clients.

# Tasked assigned by
Algorithmic Sciences

# Author
Pereruan Nabaala




