import os
from typing import List, Any
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from benchmark_algorithms import get_benchmark_elements
from stress_test_client import get_stress_test_elements

styles = getSampleStyleSheet()


def section_heading(text: str) -> Paragraph:
    """Return a heading Paragraph for the report."""
    return Paragraph(text, styles["Heading1"])


def get_intro_section() -> List[Any]:
    return [
        section_heading("Introduction"),
        Paragraph(
            "This report presents the results of benchmarking multiple string search algorithms "
            "and stress testing a string search server. The benchmarking evaluates algorithm "
            "efficiency across datasets of different sizes, while the stress test assesses server "
            "performance under increasing query loads. Together, these results provide insights "
            "into the most efficient algorithms and the server's scalability limits.",
            styles["Normal"]
        ),
        Spacer(1, 12)
    ]


def get_setup_section() -> List[Any]:
    return [
        section_heading("Setup"),
        Paragraph(
            "The evaluation was conducted on datasets containing 10,000; 100,000; 500,000; "
            "and 1,000,000 lines of randomly generated text. Six algorithms were benchmarked: "
            "Linear Scan, Generator Scan, Regex Match, Set Membership, Multithreaded Scan, and Binary Search. "
            "Each algorithm was tested in two modes: re-reading the file for each query and using a cached dataset. "
            "The stress test measured the server's query throughput (QPS) for different file sizes, "
            "stopping when the failure rate exceeded 10%.",
            styles["Normal"]
        ),
        Spacer(1, 12)
    ]


def get_algorithms_overview_section() -> List[Any]:
    return [
        section_heading("Search Algorithms Overview"),
        Paragraph(
            "The benchmarked algorithms included:\n"
            "- Linear Scan: Sequentially scans the file for the query string.\n"
            "- Generator Scan: Uses a generator to yield lines for checking.\n"
            "- Regex Match: Uses compiled regular expressions for matching.\n"
            "- Set Membership: Loads lines into a set for O(1) membership checks.\n"
            "- Multithreaded Scan: Splits the file into chunks and scans in parallel.\n"
            "- Binary Search: Operates on sorted lines for logarithmic search time.\n",
            styles["Normal"]
        ),
        Spacer(1, 12)
    ]


def get_performance_analysis_section() -> List[Any]:
    elements: List[Any] = [
        section_heading("Performance Analysis"),
        Paragraph(
            "Benchmark results show that with caching (reread_on_query=False), Linear Scan and "
            "Generator Scan achieved the fastest times for large datasets, while Regex Match was "
            "slower due to pattern compilation overhead. Set Membership excelled when using cache, "
            "but required significant time when re-reading due to repeated set construction. "
            "Multithreaded Scan provided benefits for large datasets, and Binary Search was efficient "
            "for cached sorted data but slow when re-reading unsorted files.\n\n"
            "The stress test revealed that as QPS increased, total execution time grew linearly "
            "until the server's capacity limit was reached, at which point failure rates rose sharply.",
            styles["Normal"]
        ),
        Spacer(1, 12)
    ]
    elements.extend(get_benchmark_elements())  # Tables + benchmark chart
    elements.extend(get_stress_test_elements())  # Stress test chart
    return elements


def get_conclusions_section() -> List[Any]:
    return [
        section_heading("Conclusions"),
        Paragraph(
            "The tests demonstrate that caching dramatically improves search performance for most algorithms. "
            "For large datasets, Linear Scan, Generator Scan, and Set Membership (cached) provide the best balance "
            "of speed and simplicity. Regex Match is most useful when pattern flexibility is required. "
            "The server stress test highlights the importance of optimizing for QPS handling and monitoring "
            "failure rates to avoid performance degradation under load.",
            styles["Normal"]
        ),
        Spacer(1, 12)
    ]


# Build PDF
os.makedirs("pdf", exist_ok=True)
pdf_path: str = os.path.join("pdf", "speed_report.pdf")
doc = SimpleDocTemplate(pdf_path)

elements: List[Any] = []
elements.extend(get_intro_section())
elements.extend(get_setup_section())
elements.extend(get_algorithms_overview_section())
elements.extend(get_performance_analysis_section())
elements.extend(get_conclusions_section())

doc.build(elements)
print(f"Structured report saved to {pdf_path}")
