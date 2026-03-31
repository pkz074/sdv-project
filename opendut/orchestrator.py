
import time
import csv
from test_cases import run_baseline, run_stress

RESULT_FILE = "openDuT/results/results.csv"

def save_results(results):

    with open(RESULT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Scenario", "Latency(ms)", "Throughput", "CPU(%)"])

        for r in results:
            writer.writerow(r)

def main():

    results = []

    print("Running openDuT experiments...\n")

    results.append(run_baseline())
    results.append(run_stress())

    save_results(results)

    print("\nAll experiments complete.")

if __name__ == "__main__":
    main()