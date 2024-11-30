from datetime import datetime

# Constants
BYTES_TO_GB = 1024 * 1024 * 1024
BYTES_TO_MB = 1024 * 1024
SEPARATOR_LINE = '-' * 40
DEFAULT_INTERVAL = 1

# ...existing code from utils.py...
def format_timestamp(timestamp_str):
    """Convert ISO timestamp to readable local time"""
    dt = datetime.fromisoformat(timestamp_str)
    return dt.strftime('%Y-%m-%d %I:%M:%S %p')

def format_number(value, precision=2):
    """Format number with fixed precision and thousand separators"""
    formatted = f"{value:.{precision}f}"
    parts = formatted.split('.')
    parts[0] = f"{int(parts[0]):,}"
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
