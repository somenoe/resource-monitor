import os

# Constants
DATA_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
# Create data directory if it doesn't exist
os.makedirs(DATA_DIRECTORY, exist_ok=True)

# Re-export constants from formatters
from .formatters import DEFAULT_INTERVAL, BYTES_TO_GB
