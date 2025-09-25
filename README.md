# RF Sniffer and Repeater

A Python project for capturing and repeating RF signals using two nRF24 modules on Raspberry Pi 4.

## Hardware Setup

- Raspberry Pi 4
- 2x nRF24L01+ modules
- Wiring:
  - Capture module: CE=22, CSN=0
  - Repeat module: CE=24, CSN=1
  - VCC=3.3V, GND=GND, MOSI=10, MISO=9, SCK=11

## Installation

Using uv (recommended):

For development on macOS:
```bash
make install
# or
uv sync
```

For Raspberry Pi:
```bash
make rpi-install
# or
uv sync --extra rpi
```

Using pip:
```bash
pip install -r requirements.txt
```

## Usage

### Using Make Commands (Recommended)

```bash
# Show all available commands
make help

# Quick setup
make setup

# Capture mode
make run-capture
make run-capture DURATION=120 CHANNEL=50 FILE=my_capture.txt

# Scan all channels
make run-scan
make run-scan DURATION=180 FILE=scan_results.txt

# Repeat captured signals
make run-repeat FILE=capture.txt
make run-repeat FILE=capture.txt CHANNEL=76 DELAY=0.2

# Live repeat mode
make run-live
make run-live DURATION=60 CHANNEL=76 DELAY=0.1
```

### Direct Python Commands

```bash
# Capture mode
uv run python main.py capture -d 60 -c 76 -f capture.txt

# Scan mode
uv run python main.py scan -d 60 -f scan_results.txt

# Repeat mode
uv run python main.py repeat -f capture.txt -c 76

# Live repeat mode
uv run python main.py live -d 60 -c 76
```

## Make Commands

| Command | Description | Parameters |
|---------|-------------|------------|
| `make help` | Show all available commands | |
| `make install` | Install dependencies (macOS/development) | |
| `make dev-install` | Install development dependencies | |
| `make rpi-install` | Install Raspberry Pi dependencies | |
| `make rpi-dev-install` | Install RPi + dev dependencies | |
| `make clean` | Clean virtual environment and cache | |
| `make run-capture` | Run capture mode | `DURATION`, `CHANNEL`, `FILE` |
| `make run-scan` | Run channel scan mode | `DURATION`, `FILE` |
| `make run-repeat` | Run repeat mode | `FILE`, `CHANNEL`, `DELAY` |
| `make run-live` | Run live repeat mode | `DURATION`, `CHANNEL`, `DELAY` |
| `make test` | Run tests | |
| `make lint` | Run linter | |
| `make format` | Format code | |

## Options

- `DURATION`: Duration in seconds (default: 60)
- `CHANNEL`: RF channel (0-125) - ignored in scan mode
- `FILE`: Input/output file
- `DELAY`: Delay between repeated packets (default: 0.1)

## Configuration

Edit `config.py` to modify default settings.
