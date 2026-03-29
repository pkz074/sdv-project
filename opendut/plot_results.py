import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("openDuT/results/results.csv")

df.plot(x="Scenario", y=["Latency(ms)", "Throughput", "CPU(%)"], kind="bar")
plt.title("System Performance Comparison")
plt.savefig("openDuT/results/chart.png")

print("Chart generated.")