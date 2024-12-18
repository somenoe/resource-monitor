# System Resource Monitor CLI

## Overview

A Python CLI tool that monitors and logs system resources in real-time, providing comprehensive metrics for CPU, memory, disk, and GPU usage.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- Real-time system resource monitoring:
  - CPU utilization tracking
  - Memory usage and statistics
  - Disk usage, I/O metrics
  - GPU performance monitoring
  - Interactive console display

## Installation

```bash
git clone https://github.com/somenoe/resource-monitor.git
cd resource-monitor
pip install -r requirements.txt
```

## Usage

Basic command:

```bash
python main.py
```

Advanced options:

```bash
python main.py -i 5 -d 600 -o resources_log.csv
```

### Command Arguments

| Argument | Purpose           | Default                                 |
|----------|-------------------|-----------------------------------------|
| `-i`     | Sampling interval | 1s                                      |
| `-d`     | Duration          | Continuous                              |
| `-o`     | Output file       | ./data/resource-monitor-[TIMESTAMP].csv |

## Data Output

### System Metrics

- CPU utilization
- Memory statistics
- Disk metrics

### GPU Metrics

- Usage statistics
- Memory utilization
- Temperature monitoring

## Contributing

Please submit issues and pull requests on GitHub.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
