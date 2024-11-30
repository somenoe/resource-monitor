
import psutil
import time

class NetworkCollector:
    def __init__(self):
        self.last_net_io = {
            'io': psutil.net_io_counters(),
            'time': time.time()
        }

    def collect_data(self):
        current_net_io = psutil.net_io_counters()
        current_time = time.time()

        time_diff = current_time - self.last_net_io['time']
        last_io = self.last_net_io['io']

        # Calculate speeds
        bytes_sent_sec = (current_net_io.bytes_sent - last_io.bytes_sent) / time_diff if time_diff > 0 else 0
        bytes_recv_sec = (current_net_io.bytes_recv - last_io.bytes_recv) / time_diff if time_diff > 0 else 0

        # Update last values
        self.last_net_io = {
            'io': current_net_io,
            'time': current_time
        }

        return {
            'bytes_sent': current_net_io.bytes_sent,
            'bytes_recv': current_net_io.bytes_recv,
            'packets_sent': current_net_io.packets_sent,
            'packets_recv': current_net_io.packets_recv,
            'send_speed': bytes_sent_sec,
            'recv_speed': bytes_recv_sec
        }
