#!/usr/bin/env python3
"""
Script to visualize performance data from result files
Plots check time vs distance for cryptominisat, maxsat, and z3 solvers
"""

import re
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
from collections import defaultdict

def parse_cryptominisat_or_z3(filepath):
    """Parse result files in cryptominisat/z3 format"""
    data = []
    current_entry = {}
    
    with open(filepath, 'r') as f:
        for line in f:
            # Match "Testing distance X with bias Y errors"
            match = re.match(r'Testing distance (\d+) with bias (\d+) errors', line)
            if match:
                if current_entry:
                    data.append(current_entry)
                current_entry = {
                    'distance': int(match.group(1)),
                    'errors': int(match.group(2))
                }
            # Match "Check time: X seconds"
            match = re.search(r'Check time: ([\d.]+) seconds', line)
            if match:
                current_entry['check_time'] = float(match.group(1))
            # Match "can tolerate" or "can't tolerate"
            if 'can tolerate' in line:
                current_entry['can_tolerate'] = True
            elif "can't tolerate" in line:
                current_entry['can_tolerate'] = False
            # Check for timeout
            if '(not within' in line:
                current_entry['timeout'] = True
    
    if current_entry:
        data.append(current_entry)
    
    # For each distance, keep only the entry with larger check_time
    # Track both regular entries and timeouts
    distance_data = {}
    timeout_distances = set()
    
    for entry in data:
        dist = entry['distance']
        if 'timeout' in entry and entry['timeout']:
            timeout_distances.add(dist)
        elif 'check_time' in entry:
            if dist not in distance_data:
                distance_data[dist] = entry
            else:
                # Keep the one with larger check_time
                if entry['check_time'] > distance_data[dist]['check_time']:
                    distance_data[dist] = entry
    
    # Remove timeout distances from regular data
    regular_data = [(d, distance_data[d]['check_time']) for d in sorted(distance_data.keys()) if d not in timeout_distances]
    timeout_data = sorted(timeout_distances)
    
    return regular_data, timeout_data

def parse_maxsat(filepath):
    """Parse result file in maxsat format"""
    data = []
    current_entry = {}
    
    with open(filepath, 'r') as f:
        for line in f:
            # Match "Testing distance X"
            match = re.match(r'Testing distance (\d+)', line)
            if match:
                if current_entry:
                    data.append(current_entry)
                current_entry = {
                    'distance': int(match.group(1))
                }
            # Match "Solve time: X seconds"
            match = re.search(r'Solve time: ([\d.]+) seconds', line)
            if match:
                current_entry['check_time'] = float(match.group(1))
            # Match "Minimum errors needed to cause logical failure: X"
            match = re.search(r'Minimum errors needed to cause logical failure: (\d+)', line)
            if match:
                current_entry['errors'] = int(match.group(1))
            # Check for timeout
            if '(not within 6 hours)' in line:
                current_entry['timeout'] = True
    
    if current_entry:
        data.append(current_entry)
    
    # Separate regular entries and timeouts
    result = []
    timeout_distances = []
    for entry in data:
        if 'timeout' in entry and entry['timeout']:
            timeout_distances.append(entry['distance'])
        elif 'check_time' in entry:
            result.append((entry['distance'], entry['check_time']))
    
    return result, sorted(timeout_distances)

def plot_single_solver(data, timeout_distances, solver_name, output_filename, 
                       all_distances=None, y_min=None, y_max=None, timeout_y_shared=None):
    """Plot check time vs distance for a single solver, following plot_perf_filtered.py style"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 5))
    
    # Plot regular data points
    if data:
        distances, check_times = zip(*data)
        ax.plot(distances, check_times, 
               linewidth=4, 
               markersize=14,
               marker='s',
               color='#1f77b4',
               linestyle='-')
    
    # Calculate timeout_y if needed
    timeout_y = None
    if timeout_distances:
        # Use shared timeout_y if provided, otherwise calculate locally
        if timeout_y_shared is not None:
            timeout_y = timeout_y_shared
        elif data:
            max_time = max(check_times)
            # Place timeout markers at a high y-value (above the max, but visible on log scale)
            # Use a fixed high value that's clearly above the data
            timeout_y = max(max_time * 3, 100000)  # At least 100000 seconds (about 27 hours)
        else:
            timeout_y = 100000
        
        for dist in timeout_distances:
            ax.plot(dist, timeout_y, 
                   marker='x', 
                   markersize=16,
                   markeredgewidth=3,
                   color='red',
                   linestyle='None',
                   zorder=10)
            # Add annotation
            # Position annotation text above the marker, but within the plot bounds
            if y_max is not None:
                annotation_y = y_max * 0.85  # Place annotation at 85% of max
            else:
                annotation_y = timeout_y * 2
            ax.annotate('not within 6 hours', 
                       xy=(dist, timeout_y),
                       xytext=(dist, annotation_y),
                       ha='center',
                       fontsize=20,
                       color='red',
                       fontweight='bold',
                       arrowprops=dict(arrowstyle='->', color='red', lw=2))
    
    ax.set_xlabel('Distance', fontsize=28, fontweight='bold')
    ax.set_ylabel('Check Time (s)', fontsize=28, fontweight='bold')
    # Use two-line title to fit within boundaries
    ax.set_title(f'Check Time vs Distance\n{solver_name}', fontsize=30, fontweight='bold', pad=20)
    ax.set_yscale('log')
    
    # Set x-axis ticks - use provided all_distances if available, otherwise use local
    if all_distances is not None:
        distances_list = sorted(all_distances)
    else:
        local_distances = set()
        if data:
            local_distances.update(distances)
        if timeout_distances:
            local_distances.update(timeout_distances)
        distances_list = sorted(local_distances) if local_distances else []
    
    if distances_list:
        ax.set_xticks(distances_list)
        ax.set_xticklabels(distances_list, fontsize=26)
    
    # Format y-axis to show powers of 10
    def log_formatter(x, pos):
        if x <= 0:
            return ''
        exp = int(np.log10(x))
        return f'10$^{{{exp}}}$'
    
    ax.yaxis.set_major_formatter(FuncFormatter(log_formatter))
    ax.tick_params(axis='y', labelsize=26)
    
    # Set y-axis limits - use provided limits if available, otherwise calculate
    if y_min is not None and y_max is not None:
        ax.set_ylim(y_min, y_max)
    else:
        if data:
            min_time = min(check_times)
            max_time = max(check_times)
            if timeout_y:
                # If there are timeouts, extend the upper limit to show them
                ax.set_ylim(min_time * 0.5, timeout_y * 2)
            else:
                ax.set_ylim(min_time * 0.5, max_time * 2)
        elif timeout_y:
            # Only timeouts, no regular data
            ax.set_ylim(1, timeout_y * 2)
    
    ax.grid(True, linestyle='--', alpha=0.5, which='major')
    ax.grid(True, linestyle=':', alpha=0.3, which='minor')
    
    plt.tight_layout()
    plt.savefig(output_filename)
    print(f"Saved {solver_name} plot to {output_filename}")

def main():
    """Generate separate plots for each solver"""
    # Parse each result file
    cryptominisat_data, cryptominisat_timeouts = parse_cryptominisat_or_z3('result_cryptominisat.txt')
    maxsat_data, maxsat_timeouts = parse_maxsat('result_maxsat.txt')
    z3_data, z3_timeouts = parse_cryptominisat_or_z3('result_z3.txt')
    
    # Collect all distances and all check times to determine common configuration
    all_distances_set = set()
    all_check_times = []
    
    # Collect distances and check times
    if cryptominisat_data:
        all_distances_set.update([d for d, _ in cryptominisat_data])
        all_check_times.extend([t for _, t in cryptominisat_data])
    if cryptominisat_timeouts:
        all_distances_set.update(cryptominisat_timeouts)
    
    if maxsat_data:
        all_distances_set.update([d for d, _ in maxsat_data])
        all_check_times.extend([t for _, t in maxsat_data])
    if maxsat_timeouts:
        all_distances_set.update(maxsat_timeouts)
    
    if z3_data:
        all_distances_set.update([d for d, _ in z3_data])
        all_check_times.extend([t for _, t in z3_data])
    if z3_timeouts:
        all_distances_set.update(z3_timeouts)
    
    # Determine common y-axis limits and timeout_y
    all_distances_list = sorted(all_distances_set)
    
    # Calculate shared timeout_y based on max check_time across all solvers
    if all_check_times:
        max_check_time = max(all_check_times)
        timeout_y_shared = max(max_check_time * 3, 100000)  # At least 100000 seconds
        y_min = min(all_check_times) * 0.5
        y_max = timeout_y_shared * 2
    elif cryptominisat_timeouts or maxsat_timeouts or z3_timeouts:
        # Only timeouts, no regular data
        timeout_y_shared = 100000
        y_min = 1
        y_max = timeout_y_shared * 2
    else:
        timeout_y_shared = None
        y_min = None
        y_max = None
    
    # Generate separate plots with shared configuration
    plot_single_solver(cryptominisat_data, cryptominisat_timeouts, 'CryptoMiniSat', 
                      'cryptominisat_perf.pdf', all_distances_list, y_min, y_max, timeout_y_shared)
    plot_single_solver(maxsat_data, maxsat_timeouts, 'MaxSAT (RC2)', 
                      'maxsat_perf.pdf', all_distances_list, y_min, y_max, timeout_y_shared)
    plot_single_solver(z3_data, z3_timeouts, 'Z3', 
                      'z3_perf.pdf', all_distances_list, y_min, y_max, timeout_y_shared)
    
    # Print summary
    print("\nData summary:")
    if cryptominisat_data:
        print(f"CryptoMiniSat: {len(cryptominisat_data)} data points")
        for d, t in cryptominisat_data:
            print(f"  Distance {d}: {t:.4f} seconds")
    if cryptominisat_timeouts:
        print(f"CryptoMiniSat timeouts: {cryptominisat_timeouts}")
    if maxsat_data:
        print(f"MaxSAT: {len(maxsat_data)} data points")
        for d, t in maxsat_data:
            print(f"  Distance {d}: {t:.4f} seconds")
    if maxsat_timeouts:
        print(f"MaxSAT timeouts: {maxsat_timeouts}")
    if z3_data:
        print(f"Z3: {len(z3_data)} data points")
        for d, t in z3_data:
            print(f"  Distance {d}: {t:.4f} seconds")
    if z3_timeouts:
        print(f"Z3 timeouts: {z3_timeouts}")

if __name__ == '__main__':
    main()
    print("\nAll plots generated successfully!")
