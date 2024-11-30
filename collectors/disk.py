
import psutil
import os
import time

class DiskCollector:
    def __init__(self):
        self.last_disk_io = {}
        self.disk_map = {}
        self._initialize_disk_mapping()

    def _initialize_disk_mapping(self):
        disk_io = psutil.disk_io_counters(perdisk=True)
        for partition in psutil.disk_partitions(all=False):
            try:
                self._map_partition(partition, disk_io)
            except Exception as e:
                print(f"Error mapping disk {partition.device}: {e}")

    def collect_data(self):
        disk_data = {}
        current_disk_io = psutil.disk_io_counters(perdisk=True)
        current_time = time.time()

        for disk in psutil.disk_partitions(all=False):
            disk_data[disk.device] = self._process_disk_metrics(disk, current_disk_io, current_time)

        return disk_data

    def _map_partition(self, partition, disk_io):
        if os.name == 'nt':  # Windows
            for io_name in disk_io.keys():
                if io_name.startswith('PhysicalDrive'):
                    self.disk_map[partition.device] = io_name
                    self.last_disk_io[partition.device] = {
                        'io': disk_io[io_name],
                        'time': time.time()
                    }
                    break
        else:  # Linux/Unix
            base_device = partition.device.rstrip('0123456789')
            device_name = base_device.split('/')[-1]
            if device_name in disk_io:
                self.disk_map[partition.device] = device_name
                self.last_disk_io[partition.device] = {
                    'io': disk_io[device_name],
                    'time': time.time()
                }

    def _process_disk_metrics(self, disk, current_disk_io, current_time):
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

        self.last_disk_io[device]['io'] = current_io
        self.last_disk_io[device]['time'] = current_time

        return {
            'read_speed': read_speed,
            'write_speed': write_speed
        }
