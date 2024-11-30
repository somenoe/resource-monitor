#!/usr/bin/env python3
import psutil
import time
import csv
import argparse
import threading
from datetime import datetime
import GPUtil
import os
import sys
from select import select
if os.name == 'nt':  # Windows
    import msvcrt

# Constants
BYTES_TO_GB = 1024 * 1024 * 1024
BYTES_TO_MB = 1024 * 1024
DEFAULT_INTERVAL = 1
DATA_DIRECTORY = './data'
SEPARATOR_LINE = '-' * 40

def format_timestamp(timestamp_str):
    """Convert ISO timestamp to readable local time"""
    dt = datetime.fromisoformat(timestamp_str)
    return dt.strftime('%Y-%m-%d %I:%M:%S %p')

def format_number(value, precision=2):
    """Format number with fixed precision and thousand separators"""
    # Format with specified precision first
    formatted = f"{value:.{precision}f}"
    # Split into integer and decimal parts
    parts = formatted.split('.')
    # Add commas to integer part
    parts[0] = f"{int(parts[0]):,}"
    # Rejoin with decimal if it exists
    return '.'.join(parts)

def format_speed(bytes_per_sec):
    """Format speed with appropriate unit and thousand separators"""
    units = ['B/s', 'KB/s', 'MB/s', 'GB/s']
    unit_index = 0
    value = float(bytes_per_sec)

    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1

    return f"{format_number(value)} {units[unit_index]}"

def format_bytes(bytes_value):
    """Format bytes with appropriate unit and thousand separators"""
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    value = float(bytes_value)

    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1

    return f"{format_number(value)} {units[unit_index]}"

class ResourceMonitor:
    def __init__(self, interval=DEFAULT_INTERVAL, duration=None, output_file=None):
        """
        Initialize the Resource Monitor

        Args:
            interval (float): Seconds between each monitoring snapshot
            duration (float, optional): Total duration to monitor in seconds
            output_file (str, optional): Path to save the output CSV file

        The monitor tracks CPU, memory, disk I/O, network, and GPU (if available) usage.
        """
        self.interval = interval
        self.duration = duration
        self.output_file = output_file
        self.monitoring = False
        self.data = []
        self.stdscr = None
        self.last_line_count = 0  # Track number of lines printed
        self.should_stop = False
        # Track IO for all disks
        self.last_disk_io = {}
        self.disk_map = {}

        # Get initial disk I/O counters
        disk_io = psutil.disk_io_counters(perdisk=True)
        print("Available disk IO counters:", list(disk_io.keys()))  # Debug print

        # Map physical disks to partitions
        for partition in psutil.disk_partitions(all=False):
            try:
                if os.name == 'nt':  # Windows
                    # On Windows, map PhysicalDrive numbers to drive letters
                    for io_name in disk_io.keys():
                        if io_name.startswith('PhysicalDrive'):
                            self.disk_map[partition.device] = io_name
                            self.last_disk_io[partition.device] = {
                                'io': disk_io[io_name],
                                'time': time.time()
                            }
                            break
                else:  # Linux/Unix
                    # On Linux, use device name without partition number
                    base_device = partition.device.rstrip('0123456789')
                    device_name = base_device.split('/')[-1]
                    if device_name in disk_io:
                        self.disk_map[partition.device] = device_name
                        self.last_disk_io[partition.device] = {
                            'io': disk_io[device_name],
                            'time': time.time()
                        }
            except Exception as e:
                print(f"Error mapping disk {partition.device}: {e}")

        print("Disk mapping:", self.disk_map)  # Debug print

        self.has_gpu = True  # Will be set to False if GPU is not available
        try:
            GPUtil.getGPUs()
        except:
            self.has_gpu = False
            print("No GPU detected - GPU monitoring disabled")

        # Add network tracking
        self.last_net_io = {
            'io': psutil.net_io_counters(),
            'time': time.time()
        }

    def _collect_disk_data(self):
        """
        Collect disk usage and I/O statistics for all mounted disks

        Returns:
            dict: Disk statistics including usage and I/O speeds
        """
        disk_data = {}
        try:
            current_disk_io = psutil.disk_io_counters(perdisk=True)
        except Exception as e:
            print(f"Error getting disk I/O counters: {str(e)}")
            current_disk_io = {}
        current_time = time.time()

        for disk in psutil.disk_partitions(all=False):
            disk_data[disk.device] = self._process_disk_metrics(disk, current_disk_io, current_time)

        return disk_data

    def _process_disk_metrics(self, disk, current_disk_io, current_time):
        """
        Process metrics for a single disk

        Args:
            disk: Disk partition information
            current_disk_io: Current disk I/O counters
            current_time: Current timestamp

        Returns:
            dict: Processed disk metrics
        """
        try:
            usage = psutil.disk_usage(disk.mountpoint)
            disk_info = {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent,
                'mountpoint': disk.mountpoint,
                'fstype': disk.fstype,
                'read_speed': 0,
                'write_speed': 0
            }

            if disk.device in self.disk_map:
                disk_info.update(
                    self._calculate_disk_io_speeds(
                        disk.device,
                        current_disk_io,
                        current_time
                    )
                )

            return disk_info
        except Exception as e:
            print(f"Error processing disk {disk.device}: {str(e)}")
            return None

    def _calculate_disk_io_speeds(self, device, current_disk_io, current_time):
        """Calculate disk I/O speeds for a given device"""
        io_name = self.disk_map[device]
        if io_name not in current_disk_io or device not in self.last_disk_io:
            return {'read_speed': 0, 'write_speed': 0}

        current_io = current_disk_io[io_name]
        last_io = self.last_disk_io[device]['io']
        io_time_diff = current_time - self.last_disk_io[device]['time']

        if io_time_diff <= 0:
            return {'read_speed': 0, 'write_speed': 0}

        read_speed = max(0, (current_io.read_bytes - last_io.read_bytes) / io_time_diff)
        write_speed = max(0, (current_io.write_bytes - last_io.write_bytes) / io_time_diff)

        # Update last values
        self.last_disk_io[device]['io'] = current_io
        self.last_disk_io[device]['time'] = current_time

        return {
            'read_speed': read_speed,
            'write_speed': write_speed
        }

    def _collect_resource_data(self):
        """
        Collect current system resource data including CPU, memory, disk, network, and GPU metrics

        Returns:
            dict: Current system resource metrics
        """
        timestamp = datetime.now().isoformat()

        return {
            'timestamp': timestamp,
            'cpu_percent': psutil.cpu_percent(interval=None),
            **self._collect_memory_data(),
            'disks': self._collect_disk_data(),
            'gpu_data': self._collect_gpu_data()
        }

    def _collect_memory_data(self):
        """
        Collect memory usage statistics

        Returns:
            dict: Memory usage statistics
        """
        memory = psutil.virtual_memory()
        return {
            'memory_total': memory.total,
            'memory_available': memory.available,
            'memory_used': memory.used,
            'memory_percent': memory.percent
        }

    def _collect_network_data(self):
        """
        Collect network I/O statistics

        Returns:
            dict: Network I/O statistics
        """
        current_net_io = psutil.net_io_counters()
        return {
            'net_bytes_sent': current_net_io.bytes_sent,
            'net_bytes_recv': current_net_io.bytes_recv
        }

    def _collect_gpu_data(self):
        """
        Collect GPU usage statistics for all available GPUs

        Returns:
            list: List of GPU usage statistics or None if GPU is not available
        """
        if not self.has_gpu:
            return None

        try:
            gpus = GPUtil.getGPUs()
            if not gpus:
                self.has_gpu = False
                return None

            return [{
                'index': gpu.id,
                'name': gpu.name,
                'load': gpu.load * 100,
                'memory_total': gpu.memoryTotal,
                'memory_used': gpu.memoryUsed,
                'memory_free': gpu.memoryFree,
                'memory_util': gpu.memoryUtil * 100,
                'temperature': gpu.temperature
            } for gpu in gpus]
        except:
            self.has_gpu = False
            return None

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
