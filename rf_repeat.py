#!/usr/bin/env python3

import time

import RPi.GPIO as GPIO
from pyrf24 import RF24, RF24_1MBPS, RF24_CRC_8, RF24_PA_LOW


class RFRepeat:
    def __init__(self, ce_pin=24, csn_pin=1, channel=76):
        self.radio = RF24(ce_pin, csn_pin)
        self.channel = channel
        self.is_repeating = False

    def setup(self):
        """Initialize the RF24 radio for transmission"""
        if not self.radio.begin():
            raise RuntimeError("RF24 radio hardware not responding")

        # Configure radio settings
        self.radio.setChannel(self.channel)
        self.radio.setPALevel(RF24_PA_LOW)
        self.radio.setDataRate(RF24_1MBPS)
        self.radio.setCRCLength(RF24_CRC_8)
        self.radio.setAutoAck(False)
        self.radio.setRetries(0, 0)

        # Open writing pipe
        self.radio.openWritingPipe(0x1234567890)
        self.radio.stopListening()

    def repeat_packet(self, data, delay=0.1):
        """Repeat a single packet"""
        if self.radio.write(data):
            print(f"Repeated: {data.hex()}")
            time.sleep(delay)
            return True
        else:
            print(f"Failed to repeat: {data.hex()}")
            return False

    def repeat_sequence(self, packets, delay=0.1):
        """Repeat a sequence of packets"""
        self.is_repeating = True
        success_count = 0

        for packet in packets:
            if not self.is_repeating:
                break

            if self.repeat_packet(packet["data"], delay):
                success_count += 1

        self.is_repeating = False
        print(f"Repeated {success_count}/{len(packets)} packets")
        return success_count

    def repeat_from_file(self, filename, delay=0.1):
        """Repeat packets from a saved capture file"""
        packets = []

        try:
            with open(filename, "r") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 4:
                        data = bytes.fromhex(parts[3])
                        packets.append({"data": data})
        except FileNotFoundError:
            print(f"File {filename} not found")
            return 0

        return self.repeat_sequence(packets, delay)

    def stop_repeat(self):
        """Stop the repeat process"""
        self.is_repeating = False

    def cleanup(self):
        """Clean up GPIO and radio resources"""
        self.radio.powerDown()
        GPIO.cleanup()
