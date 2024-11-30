
import psutil

def collect_memory_data():
    memory = psutil.virtual_memory()
    return {
        'memory_total': memory.total,
        'memory_available': memory.available,
        'memory_used': memory.used,
        'memory_percent': memory.percent
    }
