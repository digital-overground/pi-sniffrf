"""
Simple example of using the RF24 class.

See documentation at https://nRF24.github.io/pyRF24
"""

import struct
import time

from pyrf24 import RF24, RF24_DRIVER, RF24_PA_LOW

print(__file__)  # print example name

########### USER CONFIGURATION ###########
# CE Pin uses GPIO number with RPi and SPIDEV drivers, other drivers use
# their own pin numbering
# CS Pin corresponds the SPI bus number at /dev/spidev<a>.<b>
# ie: radio = RF24(<ce_pin>, <a>*10+<b>)
# where CS pin for /dev/spidev1.0 is 10, /dev/spidev1.1 is 11 etc...
CSN_PIN = 1  # aka CE1 on SPI bus 0: /dev/spidev0.1
CE_PIN = 25  # GPIO25 for receiver
radio = RF24(CE_PIN, CSN_PIN)

# using the python keyword global is bad practice. Instead we'll use a 1 item
# list to store our float number for the payloads sent
payload = [0.0]

# For this example, we will use different addresses
# An address need to be a buffer protocol object (bytearray)
address = [b"1Node", b"2Node"]
# It is very helpful to think of an address as a path instead of as
# an identifying device destination

# to use different addresses on a pair of radios, we need a variable to
# uniquely identify which address this radio will use to transmit
# 0 uses address[0] to transmit, 1 uses address[1] to transmit
radio_number = 1  # Set to 1 for receiver

# initialize the nRF24L01 on the spi bus
if not radio.begin():
    raise OSError("nRF24L01 hardware isn't responding")

# set the Power Amplifier level to -12 dBm since this test example is
# usually run with nRF24L01 transceivers in close proximity of each other
radio.set_pa_level(RF24_PA_LOW)  # RF24_PA_MAX is default

# set TX address of RX node (uses pipe 0)
radio.stop_listening(address[radio_number])  # enter inactive TX mode

# set RX address of TX node into an RX pipe
radio.open_rx_pipe(1, address[not radio_number])  # using pipe 1

# To save time during transmission, we'll set the payload size to be only what
# we need. A float value occupies 4 bytes in memory using struct.calcsize()
# "<f" means a little endian unsigned float
radio.payload_size = struct.calcsize("<f")

# for debugging
radio.print_details()
# or for human readable data
# radio.print_pretty_details()


def slave(timeout: int = 6):
    """Polls the radio and prints the received value. This method expires
    after 6 seconds of no received transmission."""
    print("Starting receiver, listening for packets...")
    radio.listen = True  # put radio into RX mode

    start = time.monotonic()
    while (time.monotonic() - start) < timeout:
        has_payload, pipe_number = radio.available_pipe()
        if has_payload:
            length = radio.payload_size  # grab the payload length
            # fetch 1 payload from RX FIFO
            received = radio.read(length)
            # expecting a little endian float, thus the format string "<f"
            # received[:4] truncates padded 0s in case dynamic payloads are disabled
            payload[0] = struct.unpack("<f", received[:4])[0]
            # print details about the received packet
            print(f"Received {length} bytes on pipe {pipe_number}: {payload[0]}")
            start = time.monotonic()  # reset the timeout timer
        else:
            print("No packet available, waiting...")
            time.sleep(0.5)

    print("Timeout reached, stopping receiver")
    # recommended behavior is to keep radio in TX mode while idle
    radio.listen = False  # enter inactive TX mode


if __name__ == "__main__":
    slave()
