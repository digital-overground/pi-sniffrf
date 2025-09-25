"""
RF Scanner for nRF24L01+ modules
Uses RPD (Received Power Detection) to scan for RF activity
Based on pyRF24 scanner example
"""

import argparse
import time

from pyrf24 import (
    RF24,
    RF24_1MBPS,
    RF24_2MBPS,
    RF24_250KBPS,
    RF24_CRC_DISABLED,
    RF24_PA_LOW,
    address_repr,
)


def scan_channel_rpd(radio, channel, duration=0.1):
    """Scan a single channel using RPD (Received Power Detection)"""
    radio.channel = channel
    radio.listen = True
    time.sleep(0.00013)  # Wait 130 microseconds for RPD
    rpd_detected = radio.rpd
    radio.listen = False
    return rpd_detected


def scan_spectrum(radio, duration=30):
    """Scan all 126 channels using RPD with multiple detection methods"""
    print("Scanning spectrum using RPD (Received Power Detection)...")
    print("0" * 100 + "1" * 26)
    for i in range(13):
        print(str(i % 10) * (10 if i < 12 else 6), sep="", end="")
    print("")
    for i in range(126):
        print(str(i % 10), sep="", end="")
    print("\n" + "~" * 126)

    # Configure for aggressive noise detection (like C++ scanner)
    radio.set_auto_ack(False)
    radio.disable_crc()
    radio.address_width = 2

    # Use multiple "worst possible" addresses to catch any RF signal
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

    signals = [0] * 126
    num_reps = 100  # Number of passes through spectrum

    start_timer = time.monotonic()
    rep_counter = 0

    while time.monotonic() - start_timer < duration:
        for channel in range(126):
            radio.channel = channel
            radio.listen = True
            time.sleep(0.00013)  # 130 microseconds

            # Multiple detection methods like C++ scanner
            found_signal = radio.rpd or radio.available() or radio.test_rpd()

            radio.listen = False

            if found_signal:
                signals[channel] += 1
                radio.flush_rx()  # Discard noise packets

            # Visual output
            sig_cnt = signals[channel]
            print(
                ("%X" % min(15, sig_cnt)) if sig_cnt else "-",
                sep="",
                end="" if channel < 125 else "\r",
            )

        rep_counter += 1
        if rep_counter >= num_reps:
            print("\n")
            rep_counter = 0

    return signals


def noise(radio, timeout=1, channel=None):
    """Print a stream of detected noise for duration of time.

    :param int timeout: The number of seconds to scan for ambient noise.
    :param int channel: The specific channel to focus on. If not provided, then the
        radio's current setting is used.
    """
    if channel is not None:
        radio.channel = channel
    radio.listen = True
    timeout += time.monotonic()
    while time.monotonic() < timeout:
        signal = radio.read(radio.payload_size)
        if signal:
            print(address_repr(signal, False, " "))
    radio.listen = False
    while not radio.is_fifo(False, True):
        # dump the left overs in the RX FIFO
        print(address_repr(radio.read(), False, " "))


def scan_noise(radio, duration=30, channels=None):
    """Scan multiple channels for noise/data"""
    if channels is None:
        channels = list(range(76, 86))  # Focus on common remote channels

    print(f"Scanning {len(channels)} channels for noise/data...")
    print("Press buttons on MS-8 remote while scanning...")

    results = {}

    for channel in channels:
        print(f"\nChannel {channel}:")
        radio.channel = channel
        radio.listen = True

        packets = []
        start_time = time.time()

        while time.time() - start_time < duration / len(channels):
            signal = radio.read(radio.payload_size)
            if signal:
                packets.append(signal)
                print(f"  {address_repr(signal, False, ' ')}")

        radio.listen = False

        # Clear any remaining data
        while not radio.is_fifo(False, True):
            signal = radio.read()
            if signal:
                packets.append(signal)
                print(f"  {address_repr(signal, False, ' ')}")

        if packets:
            results[channel] = packets
            print(f"  Found {len(packets)} signals on channel {channel}")
        else:
            print(f"  No signals on channel {channel}")

    return results


def scan_packets(radio, duration=30, output_file=None):
    """Scan for actual packets (not just RPD)"""
    print(f"Scanning for packets on all channels for {duration} seconds...")

    # Configure for packet reception
    radio.set_auto_ack(False)
    radio.dynamic_payloads = False
    radio.crc_length = RF24_CRC_DISABLED
    radio.set_retries(0, 0)
    radio.address_width = 2
    radio.open_rx_pipe(1, b"\0\x55")
    radio.open_rx_pipe(0, b"\0\xaa")

    results = {}
    channels = list(range(126))

    for channel in channels:
        radio.channel = channel
        radio.listen = True

        packets = []
        start_time = time.time()

        while time.time() - start_time < 0.1:  # 100ms per channel
            if radio.available():
                data = radio.read(radio.payload_size)
                if data:
                    packets.append(
                        {"timestamp": time.time(), "data": data, "length": len(data)}
                    )
            time.sleep(0.001)

        radio.listen = False

        if packets:
            results[channel] = packets
            print(f"Channel {channel}: {len(packets)} packets")

    return results


def main():
    parser = argparse.ArgumentParser(description="RF Scanner for nRF24L01+")
    parser.add_argument(
        "-d", "--duration", type=int, default=30, help="Scan duration in seconds"
    )
    parser.add_argument("-f", "--file", help="Output file for results")
    parser.add_argument(
        "-m",
        "--mode",
        choices=["rpd", "packets", "noise", "scan_noise"],
        default="rpd",
        help="Scan mode: rpd (spectrum), packets, noise, or scan_noise",
    )
    parser.add_argument(
        "-c", "--channel", type=int, help="Channel for noise mode (0-125)"
    )
    parser.add_argument(
        "--data-rate",
        choices=["1", "2", "250"],
        default="1",
        help="Data rate: 1 (1Mbps), 2 (2Mbps), 250 (250kbps)",
    )
    args = parser.parse_args()

    # Initialize radio
    radio = RF24(25, 0)  # CE=25, CSN=0

    if not radio.begin():
        print("Error: nRF24 not responding")
        return

    radio.set_pa_level(RF24_PA_LOW)

    # Set data rate
    if args.data_rate == "2":
        radio.set_data_rate(RF24_2MBPS)
        print("Using 2 Mbps")
    elif args.data_rate == "250":
        radio.set_data_rate(RF24_250KBPS)
        print("Using 250 kbps")
    else:
        radio.set_data_rate(RF24_1MBPS)
        print("Using 1 Mbps")

    if args.mode == "noise":
        # Configure for noise detection
        radio.set_auto_ack(False)
        radio.dynamic_payloads = False
        radio.crc_length = RF24_CRC_DISABLED
        radio.set_retries(0, 0)
        radio.address_width = 2
        radio.open_rx_pipe(1, b"\0\x55")
        radio.open_rx_pipe(0, b"\0\xaa")

        print(
            f"Listening for noise on channel {args.channel or 'current'} for {args.duration} seconds..."
        )
        print("Press buttons on MS-8 remote...")
        noise(radio, args.duration, args.channel)

    elif args.mode == "scan_noise":
        # Configure for noise scanning
        radio.set_auto_ack(False)
        radio.dynamic_payloads = False
        radio.crc_length = RF24_CRC_DISABLED
        radio.set_retries(0, 0)
        radio.address_width = 2
        radio.open_rx_pipe(1, b"\0\x55")
        radio.open_rx_pipe(0, b"\0\xaa")

        results = scan_noise(radio, args.duration)

        print(f"\nScan complete. Found signals on {len(results)} channels.")

        if args.file:
            with open(args.file, "w") as f:
                f.write(f"RF Noise Scan - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                for channel, signals in results.items():
                    f.write(f"Channel {channel}: {len(signals)} signals\n")
                    for signal in signals:
                        f.write(f"  {address_repr(signal, False, ' ')}\n")

    elif args.mode == "rpd":
        signals = scan_spectrum(radio, args.duration)

        # Find channels with activity
        active_channels = [i for i, count in enumerate(signals) if count > 0]

        print(f"\nFound activity on {len(active_channels)} channels:")
        for channel in active_channels:
            print(f"  Channel {channel}: {signals[channel]} detections")

        if args.file:
            with open(args.file, "w") as f:
                f.write(f"RF Spectrum Scan - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                for channel, count in enumerate(signals):
                    if count > 0:
                        f.write(f"Channel {channel}: {count} detections\n")

    else:  # packets mode
        results = scan_packets(radio, args.duration, args.file)

        print(f"\nScan complete. Found activity on {len(results)} channels.")

        if results:
            print("\nResults:")
            for channel, packets in results.items():
                print(f"Channel {channel}: {len(packets)} packets")
                for packet in packets[:3]:  # Show first 3 packets
                    data_str = " ".join(f"{b:02x}" for b in packet["data"])
                    print(f"  {packet['timestamp']:.3f}: {data_str}")

        if args.file:
            with open(args.file, "w") as f:
                f.write(f"RF Packet Scan - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                for channel, packets in results.items():
                    f.write(f"Channel {channel}: {len(packets)} packets\n")
                    for packet in packets:
                        data_str = " ".join(f"{b:02x}" for b in packet["data"])
                        f.write(f"  {packet['timestamp']:.3f}: {data_str}\n")


if __name__ == "__main__":
    main()
