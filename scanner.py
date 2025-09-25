#!/usr/bin/env python3

import argparse
import time

from pyrf24 import RF24, RF24_PA_LOW


def scan_channel(radio, channel, duration=1.0):
    """Scan a single channel for activity"""
    radio.set_channel(channel)
    radio.start_listening()

    packets = []
    start_time = time.time()

    while time.time() - start_time < duration:
        if radio.available():
            data = radio.read(32)
            if data:
                packets.append(
                    {"timestamp": time.time(), "data": data, "length": len(data)}
                )
        time.sleep(0.001)

    radio.stop_listening()
    return packets


def scan_all_channels(ce_pin=25, csn_pin=1, duration=60, output_file=None):
    """Scan all 125 channels for activity"""
    radio = RF24(ce_pin, csn_pin)

    if not radio.begin():
        raise RuntimeError("nRF24L01+ hardware isn't responding")

    radio.set_pa_level(RF24_PA_LOW)
    radio.set_auto_ack(False)
    radio.set_payload_size(32)

    # Use a simple address for scanning
    radio.open_reading_pipe(1, b"SCAN")

    print(f"Scanning all channels for {duration} seconds...")
    print("Press buttons on MS-8 remote while scanning...")

    channels = list(range(125))
    results = {}

    for i, channel in enumerate(channels):
        print(f"Scanning channel {channel} ({i+1}/125)", end="\r")
        packets = scan_channel(radio, channel, duration / len(channels))
        if packets:
            results[channel] = packets
            print(f"\nChannel {channel}: {len(packets)} packets")

    print(f"\nScan complete. Found activity on {len(results)} channels.")

    if results:
        print("\nResults:")
        for channel, packets in results.items():
            print(f"Channel {channel}: {len(packets)} packets")
            for packet in packets[:3]:  # Show first 3 packets
                data_str = " ".join(f"{b:02x}" for b in packet["data"])
                print(f"  {packet['timestamp']:.3f}: {data_str}")

    if output_file:
        with open(output_file, "w") as f:
            f.write(f"RF Scan Results - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            for channel, packets in results.items():
                f.write(f"Channel {channel}: {len(packets)} packets\n")
                for packet in packets:
                    data_str = " ".join(f"{b:02x}" for b in packet["data"])
                    f.write(f"  {packet['timestamp']:.3f}: {data_str}\n")
                f.write("\n")
        print(f"Results saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="RF Channel Scanner")
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=60,
        help="Total scan duration in seconds (default: 60)",
    )
    parser.add_argument("-f", "--file", type=str, help="Output file for results")
    parser.add_argument("--ce", type=int, default=25, help="CE pin (default: 25)")
    parser.add_argument("--csn", type=int, default=1, help="CSN pin (default: 1)")

    args = parser.parse_args()

    try:
        scan_all_channels(args.ce, args.csn, args.duration, args.file)
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
