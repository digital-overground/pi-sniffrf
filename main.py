#!/usr/bin/env python3

from RF24 import RF24

radio = RF24(22, 0)  # CE on GPIO22, CSN on CE0
if not radio.begin():
    raise RuntimeError("nRF24 not responding")
print("Radio ready")
