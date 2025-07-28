import time
import re
import bisect
from concurrent.futures import ThreadPoolExecutor
from typing import List, Callable, Dict, Optional
import matplotlib.pyplot as plt
import os


def load_file_lines(file_path: str) -> List[str]:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return [line.strip() for line in f if line.strip()]


def linear_search(lines: List[str], target: str) -> bool:
    return target in lines


def regex_search(lines: List[str], target: str) -> bool:
    pattern = re.compile(re.escape(target))
    return any(pattern.fullmatch(line) for line in lines)


def set_search(lines: List[str], target: str) -> bool:
    return target in set(lines)


def binary_search(lines: List[str], target: str) -> bool:
    sorted_lines = sorted(lines)
    index = bisect.bisect_left(sorted_lines, target)
    return index < len(sorted_lines) and sorted_lines[index] == target


def multithreaded_search(lines: List[str], target: str) -> bool:
    def chunk_search(chunk: List[str]) -> bool:
        return target in chunk

    chunks: List[List[str]] = [lines[i:i + 10000] for i in range(0, len(lines), 10000)]
    with ThreadPoolExecutor() as executor:
        results = executor.map(chunk_search, chunks)
    return any(results)


def generator_search(lines: List[str], target: str) -> bool:
    return any(line == target for line in lines)


def benchmark_algorithm(
    name: str,
    func: Callable[[List[str], str], bool],
    lines: List[str],
    target: str
) -> float:
    start: float = time.perf_counter()
    func(lines, target)
    end: float = time.perf_counter()
    return (end - start) * 1000  # milliseconds


def run_benchmarks(file_path: str, target: str) -> Dict[str, Optional[float]]:
    lines: List[str] = load_file_lines(file_path)
    algorithms: Dict[str, Callable[[List[str], str], bool]] = {
        "Linear Scan": linear_search,
        "Regex Match": regex_search,
        "Set Membership": set_search,
        "Binary Search": binary_search,
        "Multithreaded": multithreaded_search,
        "Generator Scan": generator_search,
    }

    results: Dict[str, Optional[float]] = {}
    for name, func in algorithms.items():
        try:
            duration: float = benchmark_algorithm(name, func, lines, target)
            results[name] = round(duration, 2)
        except Exception as e:
            results[name] = None
            print(f"{name} failed: {e}")
    return results


def plot_results(results: Dict[str, Optional[float]], output_path: str = "pdf/performance_chart.png") -> None:
    names: List[str] = list(results.keys())
    times: List[float] = [time_val if time_val is not None else 0.0 for time_val in results.values()]

    plt.figure(figsize=(10, 6))
    bars = plt.barh(names, times, color='skyblue')
    plt.xlabel("Time (ms)")
    plt.title("Performance of File Search Algorithms")
    plt.grid(axis='x')

    for bar, time_val in zip(bars, times):
        plt.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2, f"{time_val:.2f} ms", va='center')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


if __name__ == "__main__":
    file_path: str = "200k.txt"
    search_term: str = "5;0;6;28;0;20;3;0;"  # Pick a string that exists in your 200k.txt

    results: Dict[str, Optional[float]] = run_benchmarks(file_path, search_term)
    print("Benchmark results (in milliseconds):")
    for algo, time_taken in sorted(results.items(), key=lambda x: (x[1] is None, x[1])):
        print(f"{algo:<20}: {time_taken} ms")

    plot_results(results)
