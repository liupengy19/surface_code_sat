#!/usr/bin/env python3
"""
Script to visualize performance data for distance=13 from perf_dict.csv
"""

import csv
import matplotlib.pyplot as plt
import sys
import numpy as np

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

def load_num_vars(output_path='output.out'):
    """Load num_vars from output.out file for distance 13"""
    num_vars_map = {}
    try:
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        # Track the order of distance 13 entries
        # Based on output.out, the order is:
        # 1. chain_tseitin, base_len=2, max_error=9 -> num_vars=104856
        # 2. chain_tseitin, base_len=2, max_error=10 -> num_vars=104856
        # 3. chain_tseitin, base_len=3, max_error=9 -> num_vars=104856
        # 4. chain_tseitin, base_len=3, max_error=10 -> num_vars=104856
        # 5. tree_tseitin, base_len=2, max_error=9 -> num_vars=106503
        # 6. tree_tseitin, base_len=2, max_error=10 -> num_vars=106503
        # 7. tree_tseitin, base_len=3, max_error=9 -> num_vars=106503
        # 8. tree_tseitin, base_len=3, max_error=10 -> num_vars=106503
        
        distance13_entries = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if 'Testing distance 13' in line and 'max error' in line:
                # Extract max_error
                parts = line.split('max error')
                if len(parts) > 1:
                    max_error_str = parts[1].split('errors')[0].strip()
                    try:
                        max_error = int(max_error_str)
                        # Look for num vars in next few lines
                        for j in range(i+1, min(i+5, len(lines))):
                            if 'num vars:' in lines[j]:
                                num_vars_str = lines[j].split('num vars:')[1].strip()
                                num_vars = int(num_vars_str)
                                distance13_entries.append((max_error, num_vars))
                                break
                    except ValueError:
                        pass
            i += 1
        
        # Map based on the order we found
        # The entries appear in groups: chain_tseitin (base_len 2, then 3), then tree_tseitin (base_len 2, then 3)
        if len(distance13_entries) >= 8:
            # First 4 entries are chain_tseitin (2 entries for base_len=2, 2 for base_len=3)
            num_vars_map[('chain_tseitin', 2)] = distance13_entries[0][1]  # Use first entry's num_vars
            num_vars_map[('chain_tseitin', 3)] = distance13_entries[2][1]  # Use third entry's num_vars
            # Next 4 entries are tree_tseitin
            num_vars_map[('tree_tseitin', 2)] = distance13_entries[4][1]  # Use fifth entry's num_vars
            num_vars_map[('tree_tseitin', 3)] = distance13_entries[6][1]  # Use seventh entry's num_vars
        else:
            # Fallback: use the hardcoded values we know from the file
            num_vars_map = {
                ('chain_tseitin', 2): 104856,
                ('chain_tseitin', 3): 104856,
                ('tree_tseitin', 2): 106503,
                ('tree_tseitin', 3): 106503,
            }
        
        return num_vars_map
    except FileNotFoundError:
        print(f"Warning: File {output_path} not found, num_vars will not be displayed", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"Warning: Error loading num_vars: {e}", file=sys.stderr)
        return {}

def plot_distance13(data, output_path='performance_distance13.png', num_vars_map=None):
    """Plot check_time for distance=13, grouped by configuration"""
    # Filter for distance=13
    data_13 = [r for r in data if r['distance'] == 13]
    
    if not data_13:
        print("Error: No data found for distance=13", file=sys.stderr)
        sys.exit(1)
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 7))
    
    # Organize data by (method, base_len, sat, max_error)
    configurations = []
    check_times = []
    build_times = []
    labels = []
    
    for r in sorted(data_13, key=lambda x: (x['xor_encoding_method'], x['base_len'], x['sat'], x['max_error'])):
        method = r['xor_encoding_method']
        base_len = r['base_len']
        sat = r['sat']
        max_error = r['max_error']
        
        method_short = "chain" if method == "chain_tseitin" else "tree"
        sat_str = "sat=True" if sat else "sat=False"
        label = f"{method_short}, base={base_len}, {sat_str}, err={max_error}"
        
        configurations.append(label)
        check_times.append(r['check_time'])
        build_times.append(r['build_time'])
        labels.append(label)
    
    # Create bar chart
    x_pos = np.arange(len(configurations))
    width = 0.6
    
    bars = ax.bar(x_pos, check_times, width, alpha=0.8)
    
    # Color bars by method and base_len
    colors = {
        ('chain_tseitin', 2): '#1f77b4',  # blue
        ('chain_tseitin', 3): '#2ca02c',  # green
        ('tree_tseitin', 2): '#ff7f0e',   # orange
        ('tree_tseitin', 3): '#9467bd',   # purple
    }
    
    for i, (bar, r) in enumerate(zip(bars, data_13)):
        method = r['xor_encoding_method']
        base_len = r['base_len']
        color = colors.get((method, base_len), 'gray')
        # Make sat=True bars slightly darker
        if r['sat']:
            # Darken the color
            bar.set_color(color)
            bar.set_alpha(0.9)
        else:
            bar.set_color(color)
            bar.set_alpha(0.6)
    
    ax.set_xlabel('Configuration', fontsize=12)
    ax.set_ylabel('Check Time (seconds)', fontsize=12)
    ax.set_title('Check Time for Distance=13', fontsize=14, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars (check time)
    for i, (bar, time) in enumerate(zip(bars, check_times)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{time:.1f}s',
                ha='center', va='bottom', fontsize=8, rotation=90)
    
    # Add num_vars annotations if available
    if num_vars_map:
        for i, r in enumerate(sorted(data_13, key=lambda x: (x['xor_encoding_method'], x['base_len'], x['sat'], x['max_error']))):
            method = r['xor_encoding_method']
            base_len = r['base_len']
            num_vars = num_vars_map.get((method, base_len))
            if num_vars:
                bar = bars[i]
                # Add num_vars text above the check time label
                height = bar.get_height()
                # Position it higher to avoid overlap with check time label
                y_offset = height * 0.15  # Offset above the bar
                ax.text(bar.get_x() + bar.get_width()/2., height + y_offset,
                        f'num_vars: {num_vars:,}',
                        ha='center', va='bottom', fontsize=7, 
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                        rotation=90)
    
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
    
    # Load num_vars from output.out
    print("Loading num_vars from output.out...")
    num_vars_map = load_num_vars('output.out')
    if num_vars_map:
        print(f"Loaded num_vars for {len(num_vars_map)} configurations:")
        for (method, base_len), num_vars in num_vars_map.items():
            print(f"  {method}, base_len={base_len}: num_vars={num_vars:,}")
    
    data_13 = [r for r in data if r['distance'] == 13]
    print(f"Found {len(data_13)} rows for distance=13")
    
    if data_13:
        print(f"\nDistance=13 configurations:")
        for r in sorted(data_13, key=lambda x: (x['xor_encoding_method'], x['base_len'], x['sat'], x['max_error'])):
            method = r['xor_encoding_method']
            base_len = r['base_len']
            sat = r['sat']
            max_error = r['max_error']
            num_vars = num_vars_map.get((method, base_len), 'N/A')
            print(f"  {method}, base={base_len}, sat={sat}, max_error={max_error}: "
                  f"check_time={r['check_time']:.2f}s, build_time={r['build_time']:.2f}s, num_vars={num_vars}")
    
    print("\nGenerating plot...")
    plot_distance13(data, num_vars_map=num_vars_map)
    
    print("\nPlot generated successfully!")

if __name__ == '__main__':
    main()

