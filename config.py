#!/usr/bin/env python3

# RF24 Configuration
RF24_CONFIG = {
    # Pin configurations for two nRF24 modules
    "CAPTURE": {"CE_PIN": 22, "CSN_PIN": 0, "CHANNEL": 76},
    "REPEAT": {"CE_PIN": 24, "CSN_PIN": 1, "CHANNEL": 76},
    # Radio settings
    "POWER_LEVEL": "LOW",  # LOW, HIGH, MAX
    "DATA_RATE": "1MBPS",  # 250KBPS, 1MBPS, 2MBPS
    "CRC_LENGTH": 8,  # 8, 16
    "AUTO_ACK": False,
    "RETRIES": (0, 0),  # (delay, count)
    # Default pipes
    "READING_PIPE": 0x1234567890,
    "WRITING_PIPE": 0x1234567890,
    # Timing settings
    "CAPTURE_DELAY": 0.001,
    "REPEAT_DELAY": 0.1,
    "DEFAULT_DURATION": 60,
}

# Channel scanning range
CHANNEL_RANGE = (0, 125)

# File settings
DEFAULT_CAPTURE_DIR = "captures"
DEFAULT_CAPTURE_EXT = ".txt"
