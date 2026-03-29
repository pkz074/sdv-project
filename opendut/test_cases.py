import time
from metrics import get_latency, measure_throughput
from monitor import get_cpu_usage

def run_baseline():
    print("Running Baseline Test...")

    latencies = []

    for _ in range(20):
        latency = get_latency()
        if latency:
            latencies.append(latency)
        time.sleep(0.2)

    if len(latencies) == 0:
        print("No latency data collected!")
        avg_latency = 0
    else:
        avg_latency = sum(latencies)/len(latencies)
    throughput = measure_throughput()
    cpu = get_cpu_usage()

    return ["Baseline", avg_latency*1000, throughput, cpu]


def run_stress():
    print("Running Stress Test...")

    latencies = []

    for _ in range(20):
        time.sleep(0.1)  # simulate stress
        latency = get_latency()
        if latency:
            latencies.append(latency)

    avg_latency = sum(latencies)/len(latencies)
    throughput = measure_throughput()
    cpu = get_cpu_usage()

    return ["Stress", avg_latency*1000, throughput, cpu]