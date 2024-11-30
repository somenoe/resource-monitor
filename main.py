#!/usr/bin/env python3
import os
import argparse
from datetime import datetime
from monitor import ResourceMonitor
from utils import DATA_DIRECTORY, DEFAULT_INTERVAL

def ensure_data_directory():
    """Create data directory if it doesn't exist"""
    os.makedirs(DATA_DIRECTORY, exist_ok=True)

def create_output_filepath():
    """Create a default output filepath with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    return os.path.join(DATA_DIRECTORY, f'resource-monitor-{timestamp}.csv')

def parse_arguments():
    """Parse and validate command line arguments"""
    parser = argparse.ArgumentParser(description='System Resource Monitor')
    parser.add_argument('-i', '--interval', type=float, default=DEFAULT_INTERVAL,
                      help=f'Interval between monitoring snapshots in seconds (default: {DEFAULT_INTERVAL})')
    parser.add_argument('-d', '--duration', type=float,
                      help='Total duration of monitoring in seconds')
    parser.add_argument('-o', '--output',
                      help='Output file path to save monitoring data')

    args = parser.parse_args()

    if not args.output:
        ensure_data_directory()
        args.output = create_output_filepath()

    return args

def main():
    args = parse_arguments()
    monitor = ResourceMonitor(
        interval=args.interval,
        duration=args.duration,
        output_file=args.output
    )
    monitor.start_monitoring()

if __name__ == '__main__':
    main()
