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
CSN_PIN = 0  # aka CE0 on SPI bus 0: /dev/spidev0.0
CE_PIN = 22
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
radio_number = 0  # Set to 0 for transmitter

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


def master(count: int = 5):  # count = 5 will only transmit 5 packets
    """Transmits an incrementing float every second"""
    radio.listen = False  # ensures the nRF24L01 is in TX mode

    while count:
        # use struct.pack() to pack your data into a usable payload
        # into a usable payload
        buffer = struct.pack("<f", payload[0])
        # "<f" means a single little endian (4 byte) float value.
        start_timer = time.monotonic_ns()  # start timer
        result = radio.write(buffer)
        end_timer = time.monotonic_ns()  # end timer
        if not result:
            print("Transmission failed or timed out")
        else:
            print(
                "Transmission successful! Time to Transmit:",
                f"{(end_timer - start_timer) / 1000} us. Sent: {payload[0]}",
            )
            payload[0] += 0.01
        time.sleep(1)
        count -= 1

    # recommended behavior is to keep radio in TX mode while idle
    radio.listen = False  # enter inactive TX mode


if __name__ == "__main__":
    master()
