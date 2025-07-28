import time
import os
import matplotlib.pyplot as plt
from typing import List
from server.file_search import linear_search, load_file


def generate_file(file_path: str, num_lines: int, match_line: str = "target_string") -> None:
    """Generate a file with random lines and one guaranteed match at the end."""
    with open(file_path, "w") as f:
        for i in range(num_lines - 1):
            f.write(f"random_line_{i}\n")
        f.write(f"{match_line}\n")


def benchmark(file_path: str, query: str) -> float:
    """Benchmark linear search on a given file."""
    lines: List[str] = list(load_file(file_path))
    start: float = time.perf_counter()
    linear_search(lines, query)
    return (time.perf_counter() - start) * 1000


def main() -> None:
    sizes: List[int] = [10_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]
    times: List[float] = []

    os.makedirs("temp_files", exist_ok=True)

    for size in sizes:
        file_path = f"temp_files/test_{size}.txt"
        generate_file(file_path, size)
        ms: float = benchmark(file_path, "target_string")
        print(f"{size} lines → {ms:.2f} ms")
        times.append(ms)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(sizes, times, marker="o")
    plt.xlabel("File Size (Lines)")
    plt.ylabel("Execution Time (ms)")
    plt.title("Performance vs File Size (Linear Scan)")
    plt.grid()
    os.makedirs("pdf", exist_ok=True)
    plt.savefig("pdf/file_size_vs_time.png")
    plt.close()


if __name__ == "__main__":
    main()
