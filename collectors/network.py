import psutil
import time

class NetworkCollector:
    def __init__(self):
        current_io = psutil.net_io_counters()
        self.last_net_io = {
            'io': current_io,
            'time': time.time()
        }

    def collect_data(self):
        """Collect current network I/O metrics"""
        current_io = psutil.net_io_counters()
        current_time = time.time()
        time_diff = current_time - self.last_net_io['time']
        last_io = self.last_net_io['io']

        network_stats = self._calculate_network_speeds(current_io, last_io, time_diff)

        # Update last values for next calculation
        self.last_net_io = {
            'io': current_io,
            'time': current_time
        }

        return network_stats

    def _calculate_network_speeds(self, current_io, last_io, time_diff):
        """Calculate network speeds based on I/O differences"""
        bytes_sent_sec = (current_io.bytes_sent - last_io.bytes_sent) / time_diff if time_diff > 0 else 0
        bytes_recv_sec = (current_io.bytes_recv - last_io.bytes_recv) / time_diff if time_diff > 0 else 0

        return {
            'bytes_sent': current_io.bytes_sent,
            'bytes_recv': current_io.bytes_recv,
            'packets_sent': current_io.packets_sent,
            'packets_recv': current_io.packets_recv,
            'send_speed': bytes_sent_sec,
            'recv_speed': bytes_recv_sec
        }
