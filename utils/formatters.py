
# Constants
BYTES_TO_GB = 1024 * 1024 * 1024  # 1 GB in bytes
DEFAULT_INTERVAL = 1.0  # Default monitoring interval in seconds

def format_timestamp(timestamp):
    """Format ISO timestamp to readable format"""
    return timestamp.replace('T', ' ').split('.')[0]

def format_number(num):
    """Format number to 2 decimal places"""
    return f"{num:.2f}"

def format_speed(bytes_per_sec):
    """Format bytes per second to appropriate unit"""
    if bytes_per_sec >= BYTES_TO_GB:
        return f"{bytes_per_sec / BYTES_TO_GB:.2f} GB/s"
    elif bytes_per_sec >= 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
    elif bytes_per_sec >= 1024:
        return f"{bytes_per_sec / 1024:.2f} KB/s"
    return f"{bytes_per_sec:.2f} B/s"
