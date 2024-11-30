#!/usr/bin/env python3
import psutil
import time
import csv
import json
import argparse
import threading
from datetime import datetime
import GPUtil

class ResourceMonitor:
    def __init__(self, interval=1, duration=None, output_file=None, output_format='csv'):
        """
        Initialize the Resource Monitor

        :param interval: Seconds between each monitoring snapshot
        :param duration: Total duration to monitor (None for continuous)
        :param output_file: Path to save the output file
        :param output_format: Format to save data (csv or json)
        """
        self.interval = interval
        self.duration = duration
        self.output_file = output_file
        self.output_format = output_format
        if output_file and output_file.lower().endswith('.json'):
            self.output_format = 'json'
        self.monitoring = False
        self.data = []

    def _collect_resource_data(self):
        """
        Collect current system resource data

        :return: Dictionary with current system resource metrics
        """
        timestamp = datetime.now().isoformat()

        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=None)

        # Memory Usage
        memory = psutil.virtual_memory()

        # Network I/O
        net_io = psutil.net_io_counters()

        # GPU Usage
        gpu = GPUtil.getGPUs()[0]  # Assume only one GPU
        gpu_data = {
            'name': gpu.name,
            'load': gpu.load * 100,
            'memory_total': gpu.memoryTotal,
            'memory_used': gpu.memoryUsed,
            'memory_free': gpu.memoryFree,
            'memory_util': gpu.memoryUtil * 100,
            'temperature': gpu.temperature
        }

        return {
            'timestamp': timestamp,
            'cpu_percent': cpu_percent,
            'memory_total': memory.total,
            'memory_available': memory.available,
            'memory_used': memory.used,
            'memory_percent': memory.percent,
            'net_bytes_sent': net_io.bytes_sent,
            'net_bytes_recv': net_io.bytes_recv,
            'gpu_data': gpu_data
        }

    def start_monitoring(self):
        """
        Start monitoring system resources
        """
        self.monitoring = True
        start_time = time.time()

        print(f"Starting resource monitoring (Interval: {self.interval}s)")
        print("Press Ctrl+C to stop monitoring early.")

        try:
            while self.monitoring:
                # Collect data
                resource_data = self._collect_resource_data()
                self.data.append(resource_data)

                # Print current snapshot
                self._print_current_snapshot(resource_data)

                # Check duration if specified
                if self.duration and (time.time() - start_time) >= self.duration:
                    break

                # Wait for next interval
                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")

        finally:
            self.monitoring = False

            # Save data if output file is specified
            if self.output_file:
                self._save_data()

    def _print_current_snapshot(self, data):
        """
        Print current resource snapshot to console

        :param data: Current resource data dictionary
        """
        print(f"Timestamp: {data['timestamp']}")
        print(f"CPU Usage: {data['cpu_percent']}%")
        print(f"Memory Used: {data['memory_used'] / (1024*1024*1024):.2f} GB ({data['memory_percent']}%)")
        gpu = data['gpu_data']
        print(f"GPU ({gpu['name']}):")
        print(f"  Load: {gpu['load']}%")
        print(f"  Memory Used: {gpu['memory_used']} MB / {gpu['memory_total']} MB ({gpu['memory_util']}%)")
        print(f"  Temperature: {gpu['temperature']}°C")
        print("-" * 40)

    def _save_data(self):
        """
        Save collected resource data to file
        """
        if not self.data:
            print("No data collected.")
            return

        try:
            if self.output_format.lower() == 'csv':
                self._save_csv()
            elif self.output_format.lower() == 'json':
                self._save_json()
            else:
                print(f"Unsupported format: {self.output_format}. Use 'csv' or 'json'.")
                return

            print(f"Data saved to {self.output_file}")
        except Exception as e:
            print(f"Error saving data: {e}")

    def _save_csv(self):
        """
        Save data to CSV file
        """
        with open(self.output_file, 'w', newline='') as csvfile:
            # Use first data point's keys as fieldnames
            fieldnames = list(self.data[0].keys())
            fieldnames.remove('gpu_data')  # Remove gpu_data key
            # Add GPU-specific fields
            gpu_fieldnames = ['gpu_{}'.format(key) for key in self.data[0]['gpu_data'].keys()]
            fieldnames.extend(gpu_fieldnames)

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Write data rows
            for row in self.data:
                row_data = {key: row[key] for key in row if key != 'gpu_data'}
                for key, value in row['gpu_data'].items():
                    row_data['gpu_{}'.format(key)] = value
                writer.writerow(row_data)

    def _save_json(self):
        """
        Save data to JSON file
        """
        with open(self.output_file, 'w') as jsonfile:
            json.dump(self.data, jsonfile, indent=2)

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='System Resource Monitor')
    parser.add_argument('-i', '--interval', type=float, default=1,
                        help='Interval between monitoring snapshots in seconds (default: 1)')
    parser.add_argument('-d', '--duration', type=float,
                        help='Total duration of monitoring in seconds')
    parser.add_argument('-o', '--output',
                        help='Output file path to save monitoring data')

    # Parse arguments
    args = parser.parse_args()

    # Create and start resource monitor
    monitor = ResourceMonitor(
        interval=args.interval,
        duration=args.duration,
        output_file=args.output
    )

    # Start monitoring
    monitor.start_monitoring()

if __name__ == '__main__':
    main()
