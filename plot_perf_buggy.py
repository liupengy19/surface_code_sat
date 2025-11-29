import csv
import matplotlib.pyplot as plt

data = {}

with open("perf_dict_buggy.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        distance = int(row["distance"])
        check_time = float(row["check_time"])
        xor_method = row["xor_encoding_method"]
        base_len = row["base_len"]
        sat = row["sat"]

        key = (xor_method, base_len, sat)
        if key not in data:
            data[key] = []
        data[key].append((distance, check_time))

colors = {
    ("chain_tseitin", "2", "False"): "blue",
    ("chain_tseitin", "2", "True"): "deepskyblue",
    ("chain_tseitin", "3", "False"): "green",
    ("chain_tseitin", "3", "True"): "limegreen",
    ("tree_tseitin", "2", "False"): "red",
    ("tree_tseitin", "2", "True"): "orange",
    ("tree_tseitin", "3", "False"): "purple",
    ("tree_tseitin", "3", "True"): "magenta",
}

markers = {
    "False": "o",
    "True": "s",
}

plt.figure(figsize=(12, 7))

for key, values in sorted(data.items()):
    xor_method, base_len, sat = key
    values.sort()
    distances = [v[0] for v in values]
    check_times = [v[1] for v in values]

    sat_label = "SAT" if sat == "True" else "UNSAT"
    label = f"{xor_method}, base_len={base_len}, {sat_label}"

    plt.plot(
        distances,
        check_times,
        marker=markers[sat],
        color=colors[key],
        label=label,
        linewidth=2,
        markersize=6,
    )

plt.xlabel("Distance", fontsize=12)
plt.ylabel("Check Time (s)", fontsize=12)
plt.title("Check Time vs Distance for Different Settings", fontsize=14)
plt.legend(fontsize=9, loc="upper left")
plt.grid(True, linestyle="--", alpha=0.7)
plt.yscale("log")
plt.xticks(sorted(set(d for vals in data.values() for d, _ in vals)))

plt.tight_layout()
plt.savefig("perf_buggy_plot.pdf")
