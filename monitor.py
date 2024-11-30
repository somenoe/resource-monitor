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

# Constants for formatting output
OUTPUT_SEPARATOR = '\n'
DISK_INDENT = '  '
GPU_INDENT = '    '
AUTO_SAVE_INTERVAL = 60

class ResourceMonitor:
    def __init__(self, interval=DEFAULT_INTERVAL, duration=None, output_file=None):
        self.interval = interval
        self.duration = duration
        self.start_time = datetime.now()
        self.output_file = output_file or self._get_default_filename()
        self.monitoring = False
        self.data = []
        self.last_line_count = 0
        self.should_stop = False
        self.last_save_time = time.time()

        # Initialize collectors
        self.disk_collector = DiskCollector()
        self.gpu_collector = GPUCollector()
        self.network_collector = NetworkCollector()
        self.screen_manager = ScreenManager()

    def _get_default_filename(self):
        """Generate default filename using start time"""
        return f"resource_monitor_{self.start_time.strftime('%Y%m%d_%H%M%S')}.csv"

    def _collect_resource_data(self):
        """Collect current snapshot of system resource usage"""
        return {
            'timestamp': datetime.now().isoformat(),
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

    def _format_snapshot_lines(self, data):
        """Format resource data into displayable lines"""
        lines = [
            f"Timestamp: {format_timestamp(data['timestamp'])}",
            f"CPU Usage: {data['cpu_percent']:,}%",
            f"Memory Used: {format_number(data['memory_used'] / BYTES_TO_GB)} GB ({data['memory_percent']:,}%)",
            "",
            "Disk Usage:"
        ]

        lines.extend(self._format_disk_lines(data['disks']))

        if data['gpu_data']:
            lines.extend(self._format_gpu_lines(data['gpu_data']))

        return lines

    def _format_disk_lines(self, disks):
        """Format disk metrics into lines"""
        lines = []
        for device, disk in disks.items():
            lines.extend([
                f"{device} ({disk['mountpoint']}, {disk['fstype']}):",
                f"{DISK_INDENT}Usage: {format_number(disk['used'] / BYTES_TO_GB)} GB / {format_number(disk['total'] / BYTES_TO_GB)} GB ({disk['percent']:,}%)",
                f"{DISK_INDENT}I/O: Read: {format_speed(disk['read_speed'])}, Write: {format_speed(disk['write_speed'])}",
                ""
            ])
        return lines

    def _format_gpu_lines(self, gpu_data):
        """Format GPU metrics into lines"""
        lines = ["GPUs:"]
        for gpu in gpu_data:
            lines.extend([
                f"{DISK_INDENT}GPU {gpu['index']} ({gpu['name']}):",
                f"{GPU_INDENT}Load: {int(gpu['load']):,}%",
                f"{GPU_INDENT}Memory Used: {int(gpu['memory_used']):,} MB / {int(gpu['memory_total']):,} MB ({int(gpu['memory_util']):,}%)",
                f"{GPU_INDENT}Temperature: {int(gpu['temperature']):,}°C"
            ])
        return lines

    def _print_current_snapshot(self, data):
        """Print current resource snapshot"""
        self._clear_last_output()
        lines = self._format_snapshot_lines(data)
        print(OUTPUT_SEPARATOR.join(lines))
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

                # Auto-save check
                current_time = time.time()
                if current_time - self.last_save_time >= AUTO_SAVE_INTERVAL:
                    self._save_data()
                    self.last_save_time = current_time

                if self._check_for_quit():
                    print("\nMonitoring stopped by user ('q' pressed).")
                    break

                if self.duration and (current_time - start_time) >= self.duration:
                    break

                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user (Ctrl+C).")
        finally:
            self.monitoring = False
            self._save_data()  # Final save when monitoring stops

    def _save_data(self):
        """Save collected resource data"""
        if not self.data:
            print("No data collected.")
            return

        try:
            file_exists = os.path.exists(self.output_file)
            DataExporter.save_to_csv(self.data, self.output_file)
            if file_exists:
                print(f"\nUpdated data in: {self.output_file}")
            else:
                print(f"\nCreated new file: {self.output_file}")
        except Exception as e:
            print(f"\nError saving data: {e}")
