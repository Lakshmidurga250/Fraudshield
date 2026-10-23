"""Benchmark script measuring empirical inference latency over 100 consecutive predictions."""

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.data.synthetic import SyntheticDataGenerator
from ml.inference.predictor import FraudPredictor


def run_benchmark(n_iterations: int = 100):
    print(f"Executing {n_iterations} inference iterations on active model...")
    sample = SyntheticDataGenerator.get_sample_transaction("suspicious")

    # Warmup
    for _ in range(5):
        FraudPredictor.predict(sample)

    latencies_ms = []
    for _ in range(n_iterations):
        t0 = time.perf_counter()
        FraudPredictor.predict(sample)
        t1 = time.perf_counter()
        latencies_ms.append((t1 - t0) * 1000)

    mean_lat = statistics.mean(latencies_ms)
    median_lat = statistics.median(latencies_ms)
    p95_lat = sorted(latencies_ms)[int(n_iterations * 0.95)]
    min_lat = min(latencies_ms)
    max_lat = max(latencies_ms)

    print("\n" + "=" * 50)
    print("  FRAUDSHIELD INFERENCE LATENCY BENCHMARK REPORT")
    print("=" * 50)
    print(f"Iterations:     {n_iterations}")
    print(f"Mean Latency:   {mean_lat:.2f} ms")
    print(f"Median Latency: {median_lat:.2f} ms")
    print(f"95th %ile:      {p95_lat:.2f} ms")
    print(f"Min Latency:    {min_lat:.2f} ms")
    print(f"Max Latency:    {max_lat:.2f} ms")
    print("=" * 50)


if __name__ == "__main__":
    run_benchmark(100)
