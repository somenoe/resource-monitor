import os
import sys
import time
import psutil
import msvcrt
import csv
from datetime import datetime
from collectors.cpu_memory import collect_memory_data
from collectors.disk import DiskCollector
from collectors.gpu import GPUCollector
from collectors.network import NetworkCollector
from utils.display import ScreenManager
from utils.csv_export import DataExporter
from utils.formatters import *

class ResourceMonitor:
    def __init__(self, interval=DEFAULT_INTERVAL, duration=None, output_file=None):
        self.interval = interval
        self.duration = duration
        self.output_file = output_file
        self.monitoring = False
        self.data = []
        self.last_line_count = 0
        self.should_stop = False

        # Initialize collectors
        self.disk_collector = DiskCollector()
        self.gpu_collector = GPUCollector()
        self.network_collector = NetworkCollector()
        self.screen_manager = ScreenManager()

    def _collect_resource_data(self):
        timestamp = datetime.now().isoformat()
        return {
            'timestamp': timestamp,
            'cpu_percent': psutil.cpu_percent(interval=None),
            **collect_memory_data(),
            'disks': self.disk_collector.collect_data(),
            'gpu_data': self.gpu_collector.collect_data()
        }

    def _clear_screen(self):
        """Clear the terminal screen"""
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/MacOS
            os.system('clear')

    def _clear_last_output(self):
        """Clear previous output lines"""
        if os.name == 'nt':
            self._clear_screen()
        else:
            # Move cursor up and clear lines
            for _ in range(self.last_line_count):
                sys.stdout.write('\033[F')  # Move cursor up
                sys.stdout.write('\033[K')  # Clear line

    def _print_current_snapshot(self, data):
        """Print current resource snapshot"""
        self._clear_last_output()

        lines = []
        lines.append(f"Timestamp: {format_timestamp(data['timestamp'])}")
        lines.append(f"CPU Usage: {data['cpu_percent']:,}%")
        lines.append(f"Memory Used: {format_number(data['memory_used'] / BYTES_TO_GB)} GB ({data['memory_percent']:,}%)")
        lines.append("")
        lines.append("Disk Usage:")

        for device, disk in data['disks'].items():
            lines.append(f"{device} ({disk['mountpoint']}, {disk['fstype']}):")
            lines.append(f"  Usage: {format_number(disk['used'] / BYTES_TO_GB)} GB / {format_number(disk['total'] / BYTES_TO_GB)} GB ({disk['percent']:,}%)")
            lines.append(f"  I/O: Read: {format_speed(disk['read_speed'])}, Write: {format_speed(disk['write_speed'])}")
            lines.append("")

        if data['gpu_data']:
            lines.append("GPUs:")
            for gpu in data['gpu_data']:
                lines.append(f"  GPU {gpu['index']} ({gpu['name']}):")
                lines.append(f"    Load: {int(gpu['load']):,}%")
                lines.append(f"    Memory Used: {int(gpu['memory_used']):,} MB / {int(gpu['memory_total']):,} MB ({int(gpu['memory_util']):,}%)")
                lines.append(f"    Temperature: {int(gpu['temperature']):,}°C")

        print('\n'.join(lines))
        self.last_line_count = len(lines)

    def _check_for_quit(self):
        """Check for 'q' keypress without blocking"""
        if os.name == 'nt':  # Windows
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').lower()
                return key == 'q'
        else:  # Unix-like
            # Check if there's data to read from stdin
            rlist, _, _ = select([sys.stdin], [], [], 0)
            if rlist:
                key = sys.stdin.read(1).lower()
                return key == 'q'
        return False

    def start_monitoring(self):
        """Start monitoring resources"""
        print("Starting resource monitoring. Press 'q' to stop, or Ctrl+C.")
        time.sleep(1)  # Give time to read the message
        self._clear_screen()

        if os.name != 'nt':  # For Unix-like systems
            # Set up stdin for non-blocking reads
            import termios, tty
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setcbreak(sys.stdin.fileno())
                self._monitor_loop()
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        else:  # For Windows
            self._monitor_loop()

    def _monitor_loop(self):
        """Main monitoring loop"""
        self.monitoring = True
        start_time = time.time()

        try:
            while self.monitoring:
                resource_data = self._collect_resource_data()
                self.data.append(resource_data)
                self._print_current_snapshot(resource_data)

                if self._check_for_quit():
                    print("\nMonitoring stopped by user ('q' pressed).")
                    break

                if self.duration and (time.time() - start_time) >= self.duration:
                    break

                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user (Ctrl+C).")
        finally:
            self.monitoring = False
            if self.output_file:
                self._save_data()

    def _save_data(self):
        """
        Save collected resource data to CSV file
        """
        if not self.data:
            print("No data collected.")
            return

        try:
            self._save_csv()
            print(f"Data saved to {self.output_file}")
        except Exception as e:
            print(f"Error saving data: {e}")

    def _save_csv(self):
        """
        Save data to CSV file
        """
        with open(self.output_file, 'w', newline='') as csvfile:
            # Get all possible disk fields from the first data point
            disk_fields = set()
            for disk in self.data[0]['disks'].keys():
                for metric in ['total', 'used', 'free', 'percent', 'read_speed', 'write_speed']:
                    disk_fields.add(f"disk_{disk.replace(':', '')}_{metric}")

            # Create fieldnames
            fieldnames = ['timestamp', 'cpu_percent', 'memory_total', 'memory_available',
                         'memory_used', 'memory_percent']
            fieldnames.extend(sorted(disk_fields))

            # Add GPU fields only if GPU data exists
            if self.data[0]['gpu_data']:
                gpu_metrics = ['index', 'name', 'load', 'memory_total', 'memory_used',
                             'memory_free', 'memory_util', 'temperature']
                gpu_count = len(self.data[0]['gpu_data'])
                for i in range(gpu_count):
                    fieldnames.extend([f'gpu{i}_{key}' for key in gpu_metrics])

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in self.data:
                row_data = {
                    key: row[key] for key in row
                    if key not in ['disks', 'gpu_data']
                }

                # Add disk data
                for disk, disk_data in row['disks'].items():
                    disk_key = disk.replace(':', '')
                    for metric, value in disk_data.items():
                        if metric not in ['mountpoint', 'fstype']:
                            row_data[f'disk_{disk_key}_{metric}'] = value

                # Add GPU data if available
                if row['gpu_data']:
                    for i, gpu in enumerate(row['gpu_data']):
                        for key, value in gpu.items():
                            row_data[f'gpu{i}_{key}'] = value

                writer.writerow(row_data)
