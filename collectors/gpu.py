
import GPUtil

class GPUCollector:
    def __init__(self):
        self.has_gpu = True
        try:
            GPUtil.getGPUs()
        except:
            self.has_gpu = False
            print("No GPU detected - GPU monitoring disabled")

    def collect_data(self):
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
