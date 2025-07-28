import os
from typing import List, Tuple
import matplotlib.pyplot as plt
from fpdf import FPDF


class PDF(FPDF): 
    def header(self) -> None:
        self.set_font("Arial", style="B", size=14)
        self.cell(0, 10, "File Search Benchmark Report", ln=True, align="C")
        self.ln(10)

    def chapter_title(self, title: str) -> None:
        self.set_font("Arial", style="B", size=12)
        self.cell(0, 10, title, ln=True)
        self.ln(5)

    def chapter_body(self, text: str) -> None:
        self.set_font("Arial", size=9)
        self.multi_cell(0, 10, text)
        self.ln()


def generate_pdf() -> None:
    pdf = PDF()
    pdf.add_page()

    # 1. Introduction
    pdf.chapter_title("1. Introduction")
    pdf.chapter_body(
        "This report benchmarks six distinct file search algorithms in the context of building "
        "a high-performance TCP string search server. The primary objective is to identify which "
        "approach delivers the fastest response times when querying whether a given string exists "
        "in a large text file of 200,000+ rows..."
    )

    # 2. Setup
    pdf.chapter_title("2. Setup")
    pdf.chapter_body(
        "- Operating System: Ubuntu 22.04 (Linux)\n"
        "- Python Version: 3.10+\n"
        "- Text File: 200k.txt\n"
        "- Query Used: '5;0;6;28;0;20;3;0;'\n"
        "- Configuration File: config.txt\n"
        "- reread_on_query: False (data is preloaded once into memory at server startup)\n"
        "- max_payload: 1024 bytes (maximum allowed payload size from client queries)\n"
        "- Benchmark Tool: Custom Python script (benchmark_algorithms.py)\n"
        "- Visualization Tool: matplotlib (to generate performance_chart.png)\n"
        "- Output Report: PDF generated using fpdf library\n"
    )

    # 3. Benchmark Results
    pdf.chapter_title("3.1 Benchmark Results (reread_on_query=True)")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(90, 10, "Algorithm", 1, 0, "C")
    pdf.cell(90, 10, "Time (ms)", 1, 1, "C")

    bench_true: List[Tuple[str, str]] = [
        ("Linear Scan", "0.03 ms"),
        ("Generator Scan", "0.13 ms"),
        ("Regex Match", "0.41 ms"),
        ("Set Membership", "14.34 ms"),
        ("Multithreaded", "30.54 ms"),
        ("Binary Search", "73.92 ms"),
    ]
    pdf.set_font("Arial", "", 9)
    for algo, time_str in bench_true:
        pdf.cell(90, 10, algo, 1, 0, "C")
        pdf.cell(90, 10, time_str, 1, 1, "C")

    # 3.2 Benchmark Results (reread_on_query=False)
    pdf.add_page()
    pdf.chapter_title("3.2 Benchmark Results (reread_on_query=False)")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(90, 10, "Algorithm", 1, 0, "C")
    pdf.cell(90, 10, "Time (ms)", 1, 1, "C")

    bench_false: List[Tuple[str, str]] = [
        ("Linear Scan", "0.02 ms"),
        ("Generator Scan", "0.06 ms"),
        ("Regex Match", "0.32 ms"),
        ("Set Membership", "11.67 ms"),
        ("Multithreaded", "17.27 ms"),
        ("Binary Search", "62.22 ms"),
    ]
    pdf.set_font("Arial", "", 9)
    for algo, time_str in bench_false:
        pdf.cell(90, 10, algo, 1, 0, "C")
        pdf.cell(90, 10, time_str, 1, 1, "C")

    pdf.ln(20)

    # 4. Chart
    pdf.chapter_title("4. Performance Chart (reread_on_query=False)")
    pdf.image("pdf/performance_chart.png", w=160)

    # 6. File Size vs Execution Time Table
    pdf.add_page()
    pdf.chapter_title("6. File Size vs Execution Time")
    file_sizes_data: List[Tuple[str, str]] = [
        ("10,000 lines", "0.402 ms"),
        ("50,000 lines", "1.501 ms"),
        ("100,000 lines", "7.433 ms"),
        ("250,000 lines", "45.368 ms"),
        ("500,000 lines", "113.225 ms"),
        ("1,000,000 lines", "237.959 ms"),
    ]
    pdf.set_font("Arial", size=11)
    pdf.cell(90, 10, "File Size", border=1)
    pdf.cell(40, 10, "Time (ms)", border=1, ln=True)
    for size, duration in file_sizes_data:
        pdf.cell(90, 10, size, border=1)
        pdf.cell(40, 10, duration, border=1, ln=True)

    # Plot batch performance chart
    batches: List[str] = ["1-5", "6-10", "11-15", "16-20", "21-25", "26-30", "31-35", "36-40"]
    times: List[float] = [0.89, 0.88, 0.88, 0.89, 0.89, 0.88, 0.86, 0.87]
    plt.figure(figsize=(8, 4))
    plt.bar(batches, times, color="skyblue", edgecolor="black")
    plt.title("Average Time per Batch (250 Queries)")
    plt.xlabel("Batch Range")
    plt.ylabel("Time (seconds)")
    plt.ylim(0.8, 1.0)
    for i, t in enumerate(times):
        plt.text(i, t + 0.005, f"{t:.2f}s", ha="center", fontsize=9)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    os.makedirs("pdf", exist_ok=True)
    plt.savefig("pdf/load_test_batches.png")
    pdf.image("pdf/load_test_batches.png", w=160)

    # 8. Conclusion
    pdf.chapter_title("8. Conclusion")
    pdf.chapter_body(
        "The benchmarking results clearly demonstrate that Linear Scan is the most efficient algorithm..."
    )

    pdf.output("pdf/speed_report.pdf")
    print("speed_report.pdf generated in /pdf/")


if __name__ == "__main__":
    generate_pdf()
