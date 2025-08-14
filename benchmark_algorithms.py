import os
import time
import random
import string
import re
from typing import Callable, Any, Sequence, List, Optional, Set, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


# Caches for algorithms

_linear_scan_cache: Optional[List[str]] = None
_generator_scan_cache: Optional[List[str]] = None
_regex_match_cache: Optional[List[str]] = None
_set_membership_cache: Optional[Set[str]] = None
_multithreaded_scan_cache: Optional[List[str]] = None
_binary_search_cache: Optional[List[str]] = None


# Benchmark Algorithms

def linear_scan(file_path: str, query: str, reread_on_query: bool) -> bool:
    global _linear_scan_cache
    if reread_on_query or _linear_scan_cache is None:
        with open(file_path, 'r', encoding='utf-8') as f:
            _linear_scan_cache = f.readlines()
    return any(query in line for line in _linear_scan_cache)


def generator_scan(file_path: str, query: str, reread_on_query: bool) -> bool:
    global _generator_scan_cache
    if reread_on_query or _generator_scan_cache is None:
        with open(file_path, 'r', encoding='utf-8') as f:
            _generator_scan_cache = list(f)
    return any(query in line for line in _generator_scan_cache)


def regex_match(file_path: str, query: str, reread_on_query: bool) -> bool:
    global _regex_match_cache
    pattern = re.compile(query)
    if reread_on_query or _regex_match_cache is None:
        with open(file_path, 'r', encoding='utf-8') as f:
            _regex_match_cache = f.readlines()
    return any(pattern.search(line) for line in _regex_match_cache)


def set_membership(file_path: str, query: str, reread_on_query: bool) -> bool:
    global _set_membership_cache
    if reread_on_query or _set_membership_cache is None:
        with open(file_path, 'r', encoding='utf-8') as f:
            _set_membership_cache = set(f)
    return query in _set_membership_cache


def multithreaded_scan(file_path: str, query: str, reread_on_query: bool) -> bool:
    global _multithreaded_scan_cache

    def search_chunk(chunk: List[str]) -> bool:
        return any(query in line for line in chunk)

    if reread_on_query or _multithreaded_scan_cache is None:
        with open(file_path, 'r', encoding='utf-8') as f:
            _multithreaded_scan_cache = f.readlines()

    lines = _multithreaded_scan_cache
    chunks = [lines[i:i + 1000] for i in range(0, len(lines), 1000)]
    with ThreadPoolExecutor() as executor:
        results = executor.map(search_chunk, chunks)
    return any(results)


def binary_search(file_path: str, query: str, reread_on_query: bool) -> bool:
    global _binary_search_cache
    if reread_on_query or _binary_search_cache is None:
        with open(file_path, 'r', encoding='utf-8') as f:
            _binary_search_cache = sorted(f.readlines())

    lines = _binary_search_cache
    left, right = 0, len(lines) - 1
    while left <= right:
        mid = (left + right) // 2
        if query == lines[mid]:
            return True
        elif query < lines[mid]:
            right = mid - 1
        else:
            left = mid + 1
    return False

# -----------------------------
# Algorithms dict
# -----------------------------
algorithms: Dict[str, Callable[[str, str, bool], bool]] = {
    "Linear Scan": linear_scan,
    "Generator Scan": generator_scan,
    "Regex Match": regex_match,
    "Set Membership": set_membership,
    "Multithreaded Scan": multithreaded_scan,
    "Binary Search": binary_search
}

# -----------------------------
# Benchmark Runner
# -----------------------------
TEST_FILES_DIR = "benchmark_data"
os.makedirs(TEST_FILES_DIR, exist_ok=True)

def generate_test_file(file_path: str, num_lines: int) -> None:
    with open(file_path, 'w', encoding='utf-8') as f:
        for _ in range(num_lines):
            f.write(''.join(random.choices(string.ascii_letters + " ", k=50)) + "\n")


def benchmark_algorithm(
    algorithm: Callable[[str, str, bool], bool],
    file_sizes: Sequence[int],
    reread_values: Sequence[bool]
) -> List[Tuple[int, bool, float]]:
    results: List[Tuple[int, bool, float]] = []
    for reread_on_query in reread_values:
        for size in file_sizes:
            file_path = os.path.join(TEST_FILES_DIR, f"test_{size}.txt")
            if not os.path.exists(file_path):
                generate_test_file(file_path, size)
            query = "apple"
            start_time = time.perf_counter()
            algorithm(file_path, query, reread_on_query)
            elapsed = (time.perf_counter() - start_time) * 1000
            results.append((size, reread_on_query, elapsed))
    return results



# Run Benchmarks and generate report
file_sizes: List[int] = [10_000, 100_000, 500_000, 1_000_000]
reread_values: List[bool] = [True, False]
all_results: List[Dict[str, Any]] = []

for algo_name, algo_func in algorithms.items():
    results = benchmark_algorithm(algo_func, file_sizes, reread_values)
    for size, reread, elapsed in results:
        all_results.append({
            "Algorithm": algo_name,
            "File Size": size,
            "Reread On Query": reread,
            "Time (ms)": elapsed
        })

df = pd.DataFrame(all_results)

# Plot chart
os.makedirs("pdf", exist_ok=True)
plt.figure(figsize=(10, 6))
for algo_name in algorithms.keys():
    subset = df[(df["Algorithm"] == algo_name) & (df["Reread On Query"] == False)]
    plt.plot(subset["File Size"], subset["Time (ms)"], marker='o', label=algo_name)
plt.title("Algorithm Performance Comparison (reread_on_query=False)")
plt.xlabel("File Size (lines)")
plt.ylabel("Time (ms)")
plt.legend()
plt.grid(True)
chart_path = os.path.join("pdf", "comparison_chart.png")
plt.savefig(chart_path)
plt.close()

# Save PDF
pdf_path = os.path.join("pdf", "speed_report.pdf")
styles = getSampleStyleSheet()
doc = SimpleDocTemplate(pdf_path, pagesize=A4)
elements: List[Any] = [Paragraph("Speed Test Report", styles['Title']), Spacer(1, 12)]

for algo_name in algorithms.keys():
    elements.append(Paragraph(algo_name, styles['Heading2']))
    algo_df = df[df["Algorithm"] == algo_name].pivot(index="File Size", columns="Reread On Query", values="Time (ms)")
    data: List[List[str]] = [["File Size", "True (ms)", "False (ms)"]]
    for fs in file_sizes:
        true_val: float = float(pd.to_numeric(algo_df.loc[fs, True]))
        false_val: float = float(pd.to_numeric(algo_df.loc[fs, False]))
        data.append([str(fs), f"{true_val:.2f}", f"{false_val:.2f}"])
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

elements.append(Paragraph("Overall Comparison Chart (reread_on_query=False)", styles['Heading2']))
elements.append(Image(chart_path, width=400, height=300))
doc.build(elements)

print(f"Report saved to {pdf_path}")

# Add this at the bottom of benchmark_algorithms.py

def get_benchmark_elements() -> List[Any]:
    """Return the list of PDF elements for the benchmark report."""
    styles = getSampleStyleSheet()
    elements: List[Any] = [Paragraph("Speed Test Report", styles['Title']), Spacer(1, 12)]

    # Add tables for each algorithm
    for algo_name in algorithms.keys():
        elements.append(Paragraph(algo_name, styles['Heading2']))
        algo_df = df[df["Algorithm"] == algo_name].pivot(index="File Size", columns="Reread On Query", values="Time (ms)")

        data: List[List[str]] = [["File Size", "True (ms)", "False (ms)"]]
        for fs in file_sizes:
            true_val: float = float(pd.to_numeric(algo_df.loc[fs, True]))
            false_val: float = float(pd.to_numeric(algo_df.loc[fs, False]))
            data.append([str(fs), f"{true_val:.2f}", f"{false_val:.2f}"])

        table = Table(data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black)
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

    # Add comparison chart
    chart_path_local = os.path.join("pdf", "comparison_chart.png")
    elements.append(Paragraph("Overall Comparison Chart (reread_on_query=False)", styles['Heading2']))
    elements.append(Image(chart_path_local, width=400, height=300))

    return elements
