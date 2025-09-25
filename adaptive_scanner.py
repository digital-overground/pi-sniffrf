#!/usr/bin/env python3

import argparse
import time

from RF24 import (
    RF24,
    RF24_1MBPS,
    RF24_2MBPS,
    RF24_250KBPS,
    RF24_CRC_8,
    RF24_CRC_16,
    RF24_CRC_DISABLED,
    RF24_PA_HIGH,
    RF24_PA_LOW,
    RF24_PA_MAX,
    RF24_PA_MIN,
)
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table


class AdaptiveScanner:
    def __init__(self, ce_pin=22, csn_pin=0):
        self.radio = RF24(ce_pin, csn_pin)
        self.console = Console()

    def setup(self):
        """Initialize the radio"""
        if not self.radio.begin():
            raise RuntimeError("nRF24 not responding")

        self.console.print(Panel("Radio initialized successfully", style="green"))

    def scan_all_combinations(self, duration_per_config=2.0):
        """Scan all possible combinations until something is detected"""

        # All possible configurations
        data_rates = [RF24_250KBPS, RF24_1MBPS, RF24_2MBPS]
        crc_lengths = [RF24_CRC_DISABLED, RF24_CRC_8, RF24_CRC_16]
        power_levels = [RF24_PA_MIN, RF24_PA_LOW, RF24_PA_HIGH, RF24_PA_MAX]
        address_widths = [3, 4, 5]
        channels = list(range(125))

        total_combinations = (
            len(data_rates)
            * len(crc_lengths)
            * len(power_levels)
            * len(address_widths)
            * len(channels)
        )

        with Progress(
            TextColumn("[bold blue]Scanning all combinations..."),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task("Scanning", total=total_combinations)

            for rate in data_rates:
                for crc in crc_lengths:
                    for pa in power_levels:
                        for addr_width in address_widths:
                            for channel in channels:
                                config = {
                                    "rate": rate,
                                    "crc": crc,
                                    "pa": pa,
                                    "addr_width": addr_width,
                                    "channel": channel,
                                }

                                packets = self._scan_config(config, duration_per_config)

                                if packets:
                                    self.console.print(
                                        f"\n[bold green]DETECTED ACTIVITY![/bold green]"
                                    )
                                    self._display_detection(config, packets)
                                    return config, packets

                                progress.advance(task)

        self.console.print(
            "\n[bold red]No activity detected on any configuration[/bold red]"
        )
        return None, []

    def _scan_config(self, config, duration):
        """Scan a specific configuration"""
        try:
            self.radio.setDataRate(config["rate"])
            self.radio.setCRCLength(config["crc"])
            self.radio.setPALevel(config["pa"])
            self.radio.setAutoAck(False)
            self.radio.setAddressWidth(config["addr_width"])
            self.radio.setChannel(config["channel"])
            self.radio.startListening()

            packets = []
            start_time = time.time()

            while time.time() - start_time < duration:
                if self.radio.available():
                    data = []
                    self.radio.read(data, 32)
                    if data:
                        packets.append(
                            {
                                "timestamp": time.time(),
                                "data": data,
                                "length": len(data),
                            }
                        )
                time.sleep(0.001)

            self.radio.stopListening()
            return packets

        except Exception as e:
            self.radio.stopListening()
            return []

    def _display_detection(self, config, packets):
        """Display detection results"""
        # Convert config to readable format
        rate_names = {RF24_250KBPS: "250kbps", RF24_1MBPS: "1Mbps", RF24_2MBPS: "2Mbps"}
        crc_names = {
            RF24_CRC_DISABLED: "Disabled",
            RF24_CRC_8: "8-bit",
            RF24_CRC_16: "16-bit",
        }
        pa_names = {
            RF24_PA_MIN: "MIN",
            RF24_PA_LOW: "LOW",
            RF24_PA_HIGH: "HIGH",
            RF24_PA_MAX: "MAX",
        }

        table = Table(title="Detection Results")
        table.add_column("Parameter", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Data Rate", rate_names[config["rate"]])
        table.add_row("CRC Length", crc_names[config["crc"]])
        table.add_row("Power Level", pa_names[config["pa"]])
        table.add_row("Address Width", str(config["addr_width"]))
        table.add_row("Channel", str(config["channel"]))
        table.add_row("Packets Detected", str(len(packets)))

        self.console.print(table)

        # Show sample packets
        if packets:
            self.console.print("\n[bold]Sample Packets:[/bold]")
            for i, packet in enumerate(packets[:5]):  # Show first 5 packets
                self.console.print(
                    f"  {i+1}. {packet['data']} (length: {packet['length']})"
                )

    def continuous_scan(self, config, output_file=None):
        """Continue scanning with the detected configuration"""
        self.console.print(
            f"\n[bold blue]Continuous scanning with detected configuration...[/bold blue]"
        )

        self.radio.setDataRate(config["rate"])
        self.radio.setCRCLength(config["crc"])
        self.radio.setPALevel(config["pa"])
        self.radio.setAutoAck(False)
        self.radio.setAddressWidth(config["addr_width"])
        self.radio.setChannel(config["channel"])

        all_packets = []

        try:
            while True:
                self.radio.startListening()
                packets = self._scan_config(config, 1.0)
                self.radio.stopListening()

                if packets:
                    all_packets.extend(packets)
                    for packet in packets:
                        self.console.print(f"[green]Received: {packet['data']}[/green]")

                time.sleep(0.1)

        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]Scan interrupted by user[/bold yellow]")

            if output_file and all_packets:
                self._save_results(config, all_packets, output_file)

            return all_packets

    def _save_results(self, config, packets, filename):
        """Save results to file"""
        with open(filename, "w") as f:
            f.write(f"RF Scan Results - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Configuration:\n")
            f.write(f"  Data Rate: {config['rate']}\n")
            f.write(f"  CRC Length: {config['crc']}\n")
            f.write(f"  Power Level: {config['pa']}\n")
            f.write(f"  Address Width: {config['addr_width']}\n")
            f.write(f"  Channel: {config['channel']}\n\n")
            f.write(f"Total Packets: {len(packets)}\n\n")

            for i, packet in enumerate(packets):
                f.write(
                    f"Packet {i+1}: {packet['data']} (length: {packet['length']})\n"
                )

        self.console.print(f"Results saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Adaptive RF Scanner")
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=2.0,
        help="Duration per configuration in seconds (default: 2.0)",
    )
    parser.add_argument(
        "-f", "--file", type=str, help="Output file for continuous scan results"
    )
    parser.add_argument("--ce", type=int, default=22, help="CE pin (default: 22)")
    parser.add_argument("--csn", type=int, default=0, help="CSN pin (default: 0)")
    parser.add_argument(
        "--continuous", action="store_true", help="Continue scanning after detection"
    )

    args = parser.parse_args()

    scanner = AdaptiveScanner(ce_pin=args.ce, csn_pin=args.csn)

    try:
        scanner.setup()

        # First, scan all combinations
        config, packets = scanner.scan_all_combinations(args.duration)

        if config and args.continuous:
            # Continue scanning with detected configuration
            scanner.continuous_scan(config, args.file)

    except KeyboardInterrupt:
        print("\nScan interrupted by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
