import csv

class DataExporter:
    @staticmethod
    def save_to_csv(data, output_file):
        if not data:
            print("No data collected.")
            return

        try:
            with open(output_file, 'w', newline='') as csvfile:
                fieldnames = DataExporter._get_fieldnames(data[0])
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in data:
                    writer.writerow(DataExporter._prepare_row(row))
        except Exception as e:
            print(f"Error saving data: {str(e)}")

    @staticmethod
    def _get_fieldnames(first_row):
        disk_fields = set()
        for disk in first_row['disks'].keys():
            for metric in ['total', 'used', 'free', 'percent', 'read_speed', 'write_speed']:
                disk_fields.add(f"disk_{disk.replace(':', '')}_{metric}")

        fieldnames = ['timestamp', 'cpu_percent', 'memory_total', 'memory_available',
                      'memory_used', 'memory_percent']
        fieldnames.extend(sorted(disk_fields))

        if first_row['gpu_data']:
            gpu_metrics = ['index', 'name', 'load', 'memory_total', 'memory_used',
                           'memory_free', 'memory_util', 'temperature']
            gpu_count = len(first_row['gpu_data'])
            for i in range(gpu_count):
                fieldnames.extend([f'gpu{i}_{key}' for key in gpu_metrics])

        return fieldnames

    @staticmethod
    def _prepare_row(row):
        row_data = {
            key: row[key] for key in row
            if key not in ['disks', 'gpu_data']
        }

        for disk, disk_data in row['disks'].items():
            disk_key = disk.replace(':', '')
            for metric, value in disk_data.items():
                if metric not in ['mountpoint', 'fstype']:
                    row_data[f'disk_{disk_key}_{metric}'] = value

        if row['gpu_data']:
            for i, gpu in enumerate(row['gpu_data']):
                for key, value in gpu.items():
                    row_data[f'gpu{i}_{key}'] = value

        return row_data
