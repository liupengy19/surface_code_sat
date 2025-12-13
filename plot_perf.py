#!/usr/bin/env python3
"""
Script to visualize performance data from perf_dict.csv
"""

import csv
import matplotlib.pyplot as plt
from collections import defaultdict
import sys

def load_data(csv_path):
    """Load the CSV file into a list of dictionaries"""
    try:
        data = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                row['distance'] = int(row['distance'])
                row['max_error'] = int(row['max_error'])
                row['base_len'] = int(row['base_len'])
                row['build_time'] = float(row['build_time'])
                row['check_time'] = float(row['check_time'])
                # Convert sat to boolean
                row['sat'] = row['sat'].strip().lower() == 'true'
                data.append(row)
        return data
    except FileNotFoundError:
        print(f"Error: File {csv_path} not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error loading CSV: {e}", file=sys.stderr)
        sys.exit(1)

def get_unique_values(data, key):
    """Get unique values for a key"""
    return sorted(set(r[key] for r in data))

def plot_performance(data, output_path='performance.png'):
    """Plot check_time vs distance, grouped by xor_encoding_method, base_len, and sat"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    # Group data by (xor_encoding_method, base_len, sat, distance)
    # Then average over max_error
    grouped = defaultdict(list)
    for r in data:
        key = (r['xor_encoding_method'], r['base_len'], r['sat'], r['distance'])
        grouped[key].append(r['check_time'])
    
    # Calculate averages for each configuration
    averages = {}
    for (method, base_len, sat, distance), check_times in grouped.items():
        key = (method, base_len, sat)
        if key not in averages:
            averages[key] = {}
        averages[key][distance] = sum(check_times) / len(check_times)
    
    # Define line styles and colors for better comparison
    # Color: distinct for each (method, base_len) combination
    # Similar colors for sat=True and sat=False (same base color, different markers)
    # Line style: base_len (solid=base=2, dashed=base=3)
    # Marker: sat (circle=False, square=True)
    line_styles = {
        ('chain_tseitin', 2, False): {'color': '#1f77b4', 'linestyle': '-', 'marker': 'o'},   # blue solid, circle (sat=False)
        ('chain_tseitin', 2, True): {'color': '#1f77b4', 'linestyle': '-', 'marker': 's'},    # blue solid, square (sat=True)
        ('chain_tseitin', 3, False): {'color': '#2ca02c', 'linestyle': '--', 'marker': 'o'},   # green dashed, circle (sat=False)
        ('chain_tseitin', 3, True): {'color': '#2ca02c', 'linestyle': '--', 'marker': 's'},    # green dashed, square (sat=True)
        ('tree_tseitin', 2, False): {'color': '#ff7f0e', 'linestyle': '-', 'marker': 'o'},     # orange solid, circle (sat=False)
        ('tree_tseitin', 2, True): {'color': '#ff7f0e', 'linestyle': '-', 'marker': 's'},     # orange solid, square (sat=True)
        ('tree_tseitin', 3, False): {'color': '#9467bd', 'linestyle': '--', 'marker': 'o'},    # purple dashed, circle (sat=False)
        ('tree_tseitin', 3, True): {'color': '#9467bd', 'linestyle': '--', 'marker': 's'},     # purple dashed, square (sat=True)
    }
    
    # Plot each of the 8 configurations
    for method in sorted(get_unique_values(data, 'xor_encoding_method')):
        for base_len in sorted(get_unique_values(data, 'base_len')):
            for sat in sorted(get_unique_values(data, 'sat')):
                key = (method, base_len, sat)
                if key in averages:
                    distances = sorted(averages[key].keys())
                    check_times = [averages[key][d] for d in distances]
                    sat_str = "True" if sat else "False"
                    method_short = "chain" if method == "chain_tseitin" else "tree"
                    label = f"{method_short}, base={base_len}, sat={sat_str}"
                    
                    style = line_styles.get(key, {'color': 'black', 'linestyle': '-', 'marker': 'o'})
                    ax.plot(distances, check_times, 
                           label=label, 
                           linewidth=1.0, 
                           markersize=4,
                           **style)
    
    ax.set_xlabel('Distance', fontsize=12)
    ax.set_ylabel('Check Time (seconds)', fontsize=12)
    ax.set_title('Check Time vs Distance (averaged over max_error)', fontsize=14, fontweight='bold')
    ax.set_yscale('log')
    # Set x-axis ticks to only show the actual distance values (3, 5, 7, 9)
    distances_in_data = sorted(get_unique_values(data, 'distance'))
    ax.set_xticks(distances_in_data)
    ax.set_xticklabels(distances_in_data)
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved performance plot to {output_path}")

def main():
    csv_path = 'perf_dict.csv'
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    
    print(f"Loading data from {csv_path}...")
    data = load_data(csv_path)
    print(f"Loaded {len(data)} rows")
    
    if data:
        print(f"\nColumns: {list(data[0].keys())}")
        print(f"\nUnique values:")
        print(f"  Distance: {get_unique_values(data, 'distance')}")
        print(f"  Max Error: {get_unique_values(data, 'max_error')}")
        print(f"  Methods: {get_unique_values(data, 'xor_encoding_method')}")
        print(f"  Base Length: {get_unique_values(data, 'base_len')}")
        print(f"  Sat: {get_unique_values(data, 'sat')}")
    
    print("\nGenerating plot...")
    plot_performance(data)
    
    print("\nPlot generated successfully!")

if __name__ == '__main__':
    main()
