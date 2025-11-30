import csv
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

def process_data_and_plot(sat_value, output_filename, color, title_suffix=""):
    """Process data for a given sat value and generate a plot."""
    data = []
    
    # Read and filter data
    with open("perf_dict_buggy.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["sat"] == sat_value:
                distance = int(row["distance"])
                max_error = int(row["max_error"])
                check_time = float(row["check_time"])
                xor_method = row["xor_encoding_method"]
                base_len = row["base_len"]
                data.append((distance, max_error, check_time, xor_method, base_len))
    
    # For each distance, find the row with largest max_error,
    # and among those with max max_error, pick the one with lowest check_time
    distance_data = {}
    for distance, max_error, check_time, xor_method, base_len in data:
        if distance not in distance_data:
            distance_data[distance] = (max_error, check_time, xor_method, base_len)
        else:
            current_max_error, current_check_time, _, _ = distance_data[distance]
            # If this has larger max_error, replace
            if max_error > current_max_error:
                distance_data[distance] = (max_error, check_time, xor_method, base_len)
            # If same max_error, keep the one with lower check_time
            elif max_error == current_max_error and check_time < current_check_time:
                distance_data[distance] = (max_error, check_time, xor_method, base_len)
    
    # Sort by distance and extract values for plotting
    sorted_data = sorted(distance_data.items())
    distances = [d for d, _ in sorted_data]
    check_times = [ct for _, (_, ct, _, _) in sorted_data]
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    
    plt.plot(
        distances,
        check_times,
        marker="s",
        color=color,
        linewidth=4,
        markersize=14,
    )
    
    plt.xlabel("Distance", fontsize=28, fontweight='bold')
    plt.ylabel("Check Time (s)", fontsize=28, fontweight='bold')
    title = "SAT solving time" + title_suffix
    plt.title(title, fontsize=30, fontweight='bold', pad=15)
    plt.grid(True, linestyle="--", alpha=0.5, which='major')
    plt.grid(True, linestyle=":", alpha=0.3, which='minor')
    plt.yscale("log")
    plt.xticks(distances, fontsize=26)
    
    # Format y-axis to show powers of 10
    def log_formatter(x, pos):
        if x <= 0:
            return ''
        exp = int(np.log10(x))
        return f'10$^{{{exp}}}$'
    
    plt.gca().yaxis.set_major_formatter(FuncFormatter(log_formatter))
    plt.tick_params(axis='y', labelsize=26)
    
    # Set y-axis limits with some padding
    if check_times:
        min_time = min(check_times)
        max_time = max(check_times)
        plt.ylim(min_time * 0.5, max_time * 2)
    
    plt.tight_layout()
    plt.savefig(output_filename)
    print(f"Plot saved to {output_filename}")
    print(f"Data points: {len(distances)}")
    for d, (me, ct, xm, bl) in sorted_data:
        print(f"  Distance {d}: check_time = {ct:.6f}s, max_error = {me}, config = {xm}, base_len = {bl}")

def process_data(sat_value):
    """Process data for a given sat value and return sorted distance data."""
    data = []
    
    # Read and filter data
    with open("perf_dict_buggy.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["sat"] == sat_value:
                distance = int(row["distance"])
                max_error = int(row["max_error"])
                check_time = float(row["check_time"])
                xor_method = row["xor_encoding_method"]
                base_len = row["base_len"]
                data.append((distance, max_error, check_time, xor_method, base_len))
    
    # For each distance, find the row with largest max_error,
    # and among those with max max_error, pick the one with lowest check_time
    distance_data = {}
    for distance, max_error, check_time, xor_method, base_len in data:
        if distance not in distance_data:
            distance_data[distance] = (max_error, check_time, xor_method, base_len)
        else:
            current_max_error, current_check_time, _, _ = distance_data[distance]
            # If this has larger max_error, replace
            if max_error > current_max_error:
                distance_data[distance] = (max_error, check_time, xor_method, base_len)
            # If same max_error, keep the one with lower check_time
            elif max_error == current_max_error and check_time < current_check_time:
                distance_data[distance] = (max_error, check_time, xor_method, base_len)
    
    # Sort by distance
    sorted_data = sorted(distance_data.items())
    distances = [d for d, _ in sorted_data]
    check_times = [ct for _, (_, ct, _, _) in sorted_data]
    return distances, check_times, sorted_data

def plot_combined_sat_unsat():
    """Create a combined plot showing both SAT and UNSAT results."""
    # Process both SAT and UNSAT data
    sat_distances, sat_times, sat_sorted = process_data("True")
    unsat_distances, unsat_times, unsat_sorted = process_data("False")
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    
    # Plot UNSAT line
    plt.plot(
        unsat_distances,
        unsat_times,
        marker="s",
        color="red",
        linewidth=4,
        markersize=14,
        label="UNSAT",
    )
    
    # Plot SAT line
    plt.plot(
        sat_distances,
        sat_times,
        marker="o",
        color="deepskyblue",
        linewidth=4,
        markersize=14,
        label="SAT",
    )
    
    plt.xlabel("Distance", fontsize=28, fontweight='bold')
    plt.ylabel("Check Time (s)", fontsize=28, fontweight='bold')
    plt.title("SAT solving time (UNSAT vs SAT)", fontsize=30, fontweight='bold', pad=15)
    plt.grid(True, linestyle="--", alpha=0.5, which='major')
    plt.grid(True, linestyle=":", alpha=0.3, which='minor')
    plt.yscale("log")
    
    # Combine all distances for x-axis ticks
    all_distances = sorted(set(sat_distances + unsat_distances))
    plt.xticks(all_distances, fontsize=26)
    
    # Format y-axis to show powers of 10
    def log_formatter(x, pos):
        if x <= 0:
            return ''
        exp = int(np.log10(x))
        return f'10$^{{{exp}}}$'
    
    plt.gca().yaxis.set_major_formatter(FuncFormatter(log_formatter))
    plt.tick_params(axis='y', labelsize=26)
    
    # Set y-axis limits with some padding (use min/max from both datasets)
    all_times = sat_times + unsat_times
    if all_times:
        min_time = min(all_times)
        max_time = max(all_times)
        plt.ylim(min_time * 0.5, max_time * 2)
    
    # Add legend
    plt.legend(fontsize=24, loc='upper left')
    
    plt.tight_layout()
    plt.savefig("perf_filtered_plot_unsat.pdf")
    print(f"Plot saved to perf_filtered_plot_unsat.pdf")
    print(f"SAT data points: {len(sat_distances)}")
    print(f"UNSAT data points: {len(unsat_distances)}")

# Generate plot for sat=True (standalone)
print("Generating plot for sat=True...")
process_data_and_plot("True", "perf_filtered_plot.pdf", "deepskyblue", " (SAT)")

# Generate combined plot for SAT vs UNSAT
print("\nGenerating combined plot for SAT vs UNSAT...")
plot_combined_sat_unsat()

