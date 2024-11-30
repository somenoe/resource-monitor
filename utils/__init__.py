import os

# Constants
DATA_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
# Create data directory if it doesn't exist
os.makedirs(DATA_DIRECTORY, exist_ok=True)

# Re-export everything from formatters
from .formatters import (
    BYTES_TO_GB, BYTES_TO_MB, SEPARATOR_LINE, DEFAULT_INTERVAL,
    format_timestamp, format_number, format_speed, format_bytes
)
