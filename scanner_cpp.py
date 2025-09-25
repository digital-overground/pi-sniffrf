#!/usr/bin/env python3
"""
Channel scanner - Python port of the C++ scanner example
Ported from: https://github.com/nRF24/RF24/blob/master/examples_linux/scanner.cpp

This is an example of how to use the nRF24L01's builtin
Received Power Detection (RPD) to scan for possible interference.
This example does not require a counterpart node.
"""

import sys
import time

from pyrf24 import (
    RF24,
    RF24_1MBPS,
    RF24_2MBPS,
    RF24_250KBPS,
    RF24_CRC_DISABLED,
    RF24_PA_LOW,
)


def print_header():
    """Print the vertical header showing channel numbers"""
    num_channels = 126

    # print the hundreds digits
    for i in range(num_channels):
        print(i // 100, end="")
    print()

    # print the tens digits
    for i in range(num_channels):
        print((i % 100) // 10, end="")
    print()

    # print the singles digits
    for i in range(num_channels):
        print(i % 10, end="")
    print()

    # print the header's divider
    for i in range(num_channels):
        print("~", end="")
    print()


def main():
    print(f"{sys.argv[0]}")

    # Radio CE Pin, CSN Pin, SPI Speed
    # CE Pin uses GPIO number with BCM and SPIDEV drivers
    # CS Pin addresses the SPI bus number at /dev/spidev<a>.<b>
    # ie: RF24 radio(<ce_pin>, <a>*10+<b>); spidev1.0 is 10, spidev1.1 is 11 etc..
    CSN_PIN = 0
    CE_PIN = 25  # GPIO25 for your setup

    radio = RF24(CE_PIN, CSN_PIN)

    # Setup the radio
    if not radio.begin():
        print("Radio hardware not responding!")
        return 1

    # print a line that should not be wrapped
    print(
        "\n!!! This example requires a width of at least 126 characters. "
        "If this text uses multiple lines, then the output will look bad."
    )

    # set the data rate
    print(
        "Select your Data Rate. "
        "Enter '1' for 1 Mbps, '2' for 2 Mbps, '3' for 250 kbps. "
        "Defaults to 1Mbps."
    )

    try:
        data_rate = input().strip()
    except KeyboardInterrupt:
        print("\nExiting...")
        return 0

    if data_rate.startswith("2"):
        print("Using 2 Mbps.")
        radio.set_data_rate(RF24_2MBPS)
    elif data_rate.startswith("3"):
        print("Using 250 kbps.")
        radio.set_data_rate(RF24_250KBPS)
    else:
        print("Using 1 Mbps.")
        radio.set_data_rate(RF24_1MBPS)

    # configure the radio
    radio.set_auto_ack(False)  # Don't acknowledge arbitrary signals
    radio.disable_crc()  # Accept any signal we find
    radio.set_address_width(
        2
    )  # A reverse engineering tactic (not typically recommended)

    # To detect noise, we'll use the worst addresses possible (a reverse engineering tactic).
    # These addresses are designed to confuse the radio into thinking
    # that the RF signal's preamble is part of the packet/payload.
    noise_addresses = [
        b"\x55\x55",
        b"\xaa\xaa",
        b"\x0a\xaa",
        b"\xa0\xaa",
        b"\x00\xaa",
        b"\xab\xaa",
    ]

    for i, addr in enumerate(noise_addresses):
        radio.open_rx_pipe(i, addr)

    # Get into standby mode
    radio.listen = True
    radio.listen = False
    radio.flush_rx()

    # Channel info
    num_channels = 126  # 0-125 are supported
    values = [
        0
    ] * num_channels  # the array to store summary of signal counts per channel
    num_reps = 100  # number of passes for each scan of the entire spectrum

    # print the vertical header
    print_header()

    # forever loop
    try:
        while True:
            # Clear measurement values
            values = [0] * num_channels

            # Scan all channels num_reps times
            rep_counter = num_reps
            while rep_counter > 0:
                for i in range(num_channels):
                    # Select this channel
                    radio.channel = i

                    # Listen for a little
                    radio.listen = True
                    time.sleep(0.00013)  # 130 microseconds
                    found_signal = radio.test_rpd()
                    radio.listen = False

                    # Did we get a signal?
                    if found_signal or radio.test_rpd() or radio.available():
                        values[i] += 1
                        radio.flush_rx()  # discard packets of noise

                    # output the summary/snapshot for this channel
                    if values[i]:
                        # Print out channel measurements, clamped to a single hex digit
                        print(f"{min(0xF, values[i]):X}", end="", flush=True)
                    else:
                        print("-", end="", flush=True)

                print("\r", end="", flush=True)
                rep_counter -= 1

            print()

    except KeyboardInterrupt:
        print("\nKeyboard Interrupt detected. Powering down radio...")
        radio.power = False
        return 0


if __name__ == "__main__":
    sys.exit(main())
