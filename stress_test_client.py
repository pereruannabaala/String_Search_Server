import socket
import ssl
import time
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Flowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# Configuration 
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 44445
USE_SSL = True

# Test parameters
FILE_SIZES = ["10k.txt", "100k.txt", "500k.txt", "1M.txt"]
QPS_STEPS = [1, 2, 5, 10, 20, 30, 40, 50, 75, 100]
FAIL_THRESHOLD = 0.1  # Stop execution if more than 10% of operations fail
BATCH_DURATION_SEC = 2  # Duration (in seconds) to run each QPS test step

# Paths for results and plots
RESULTS_CSV = os.path.join("pdf", "results.csv")
PLOT_PATH = os.path.join("pdf", "execution_time_plot.png")
PDF_PATH = os.path.join("pdf", "speed_report.pdf")

os.makedirs("pdf", exist_ok=True)

# Socket creation with self-signed SSL support 
def create_socket() -> socket.socket:
    sock = socket.create_connection((SERVER_HOST, SERVER_PORT), timeout=2)
    if USE_SSL:
        context = ssl._create_unverified_context()  # skip CA verification
        sock = context.wrap_socket(sock, server_hostname=SERVER_HOST)
    return sock

# Send a single query
def send_query(query: str) -> bool:
    """Send a query to the server and return True if successful, False otherwise."""
    try:
        with create_socket() as sock:
            sock.sendall(query.encode("utf-8"))
            sock.recv(4096)
        return True
    except Exception as e:
        print(f"[ERROR] ❌ {e}")
        return False

# Stress test 
def stress_test() -> None:
    with open(RESULTS_CSV, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["FileSize", "QPS", "TotalQueries", "Failures", "SuccessRate", "TotalTime"])

        for file_size in FILE_SIZES:
            print(f"\n📂 Testing with file size: {file_size}")
            for qps in QPS_STEPS:
                queries = qps * BATCH_DURATION_SEC
                failures = 0

                start_batch = time.time()
                for _ in range(queries):
                    if not send_query(f"search_term|{file_size}"):
                        failures += 1
                    time.sleep(1 / qps)
                total_time = time.time() - start_batch

                success_rate = (queries - failures) / queries if queries > 0 else 0
                print(f" QPS={qps:<3} | SuccessRate={success_rate:.2f} | Failures={failures} | TotalTime={total_time:.2f}s")
                writer.writerow([file_size, qps, queries, failures, success_rate, total_time])

                if success_rate < (1 - FAIL_THRESHOLD):
                    print("  ⚠ Server limit reached. Stopping test for this file size.")
                    break

# Generate PDF report
def get_stress_test_elements() -> list[Flowable]:
    if not os.path.exists(RESULTS_CSV):
        print("[INFO] No stress test results found, running stress test...")
        stress_test()  # This will create results.csv
    
    df = pd.read_csv(RESULTS_CSV)
    
    # Create plot
    plt.figure(figsize=(8, 6))
    for file_size in df["FileSize"].unique():
        subset = df[df["FileSize"] == file_size]
        plt.plot(subset["QPS"], subset["TotalTime"], marker="o", label=file_size)
    plt.xlabel("Queries per Second (QPS)")
    plt.ylabel("Total Time (seconds)")
    plt.title("Execution Time vs QPS")
    plt.legend()
    plt.grid(True)
    plt.savefig(PLOT_PATH)
    plt.close()

    styles = getSampleStyleSheet()
    elements = [
        Paragraph("String Search Server QPS Stress Test", styles["Heading2"]),
        Paragraph(
            "This chart shows how execution time changes with QPS for various file sizes. "
            "A sharp drop in success rate marks the server's capacity limit.",
            styles["Normal"]
        ),
        Spacer(1, 12),
        Image(PLOT_PATH, width=400, height=300)
    ]
    return elements


