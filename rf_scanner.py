#!/usr/bin/env python3

import argparse
import time

from RF24 import RF24, RF24_1MBPS, RF24_CRC_8, RF24_PA_LOW
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table


class RFScanner:
    def __init__(self, ce_pin=22, csn_pin=0):
        self.radio = RF24(ce_pin, csn_pin)
        self.console = Console()

    def setup(self):
        """Initialize the radio"""
        if not self.radio.begin():
            raise RuntimeError("nRF24 not responding")

        self.radio.setDataRate(RF24_1MBPS)
        self.radio.setCRCLength(RF24_CRC_8)
        self.radio.setPALevel(RF24_PA_LOW)
        self.radio.setAutoAck(False)
        self.radio.setAddressWidth(5)

        self.console.print(Panel("Radio initialized successfully", style="green"))

    def scan_channel(self, channel, duration=1.0):
        """Scan a single channel for activity"""
        self.radio.setChannel(channel)
        self.radio.startListening()

        packets = []
        start_time = time.time()

        while time.time() - start_time < duration:
            if self.radio.available():
                packet = []
                self.radio.read(packet, 32)
                if packet:
                    packets.append(
                        {
                            "timestamp": time.time(),
                            "data": packet,
                            "length": len(packet),
                        }
                    )
            time.sleep(0.001)

        self.radio.stopListening()
        return packets

    def scan_all_channels(self, duration=60, output_file=None):
        """Scan all 125 channels for activity"""
        channels = list(range(125))
        results = {}

        with Progress(
            TextColumn("[bold blue]Scanning channels..."),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task("Scanning", total=len(channels))

            for channel in channels:
                packets = self.scan_channel(channel, duration / len(channels))
                if packets:
                    results[channel] = packets
                    self.console.print(f"Channel {channel}: {len(packets)} packets")

                progress.advance(task)

        self._display_results(results)

        if output_file:
            self._save_results(results, output_file)

        return results

    def _display_results(self, results):
        """Display scan results in a table"""
        if not results:
            self.console.print("No activity detected on any channel")
            return

        table = Table(title="RF Scan Results")
        table.add_column("Channel", style="cyan")
        table.add_column("Packets", style="magenta")
        table.add_column("Avg Length", style="green")

        for channel, packets in results.items():
            avg_length = sum(p["length"] for p in packets) / len(packets)
            table.add_row(str(channel), str(len(packets)), f"{avg_length:.1f}")

        self.console.print(table)

    def _save_results(self, results, filename):
        """Save results to file"""
        with open(filename, "w") as f:
            f.write(f"RF Scan Results - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")

            for channel, packets in results.items():
                f.write(f"Channel {channel}: {len(packets)} packets\n")
                for packet in packets:
                    f.write(f"  {packet['timestamp']:.3f}: {packet['data']}\n")
                f.write("\n")

        self.console.print(f"Results saved to {filename}")


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
    parser.add_argument("--ce", type=int, default=22, help="CE pin (default: 22)")
    parser.add_argument("--csn", type=int, default=0, help="CSN pin (default: 0)")

    args = parser.parse_args()

    scanner = RFScanner(ce_pin=args.ce, csn_pin=args.csn)

    try:
        scanner.setup()
        scanner.scan_all_channels(args.duration, args.file)
    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
