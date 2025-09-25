#!/usr/bin/env python3

import time

import RPi.GPIO as GPIO
from pyrf24 import RF24, RF24_1MBPS, RF24_CRC_8, RF24_PA_LOW
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.table import Table


class RFCapture:
    def __init__(self, ce_pin=22, csn_pin=0, channel=76):
        self.radio = RF24(ce_pin, csn_pin)
        self.channel = channel
        self.captured_data = []
        self.is_capturing = False
        self.channel_activity = {}
        self.console = Console()

    def setup(self):
        """Initialize the RF24 radio for capture"""
        if not self.radio.begin():
            raise RuntimeError("RF24 radio hardware not responding")

        # Configure radio settings
        self.radio.setChannel(self.channel)
        self.radio.setPALevel(RF24_PA_LOW)
        self.radio.setDataRate(RF24_1MBPS)
        self.radio.setCRCLength(RF24_CRC_8)
        self.radio.setAutoAck(False)
        self.radio.setRetries(0, 0)

        # Open reading pipe
        self.radio.openReadingPipe(1, 0x1234567890)
        self.radio.startListening()

    def start_capture(self, duration=60, scan_all=False):
        """Start capturing RF signals for specified duration"""
        self.is_capturing = True
        self.captured_data = []
        self.channel_activity = {}

        if scan_all:
            self.console.print(
                Panel(
                    f"[bold blue]Starting channel scan for {duration} seconds[/bold blue]",
                    title="RF Scanner",
                    border_style="blue",
                )
            )
            self._scan_all_channels(duration)
        else:
            self.console.print(
                Panel(
                    f"[bold green]Starting capture on channel {self.channel} for "
                    f"{duration} seconds[/bold green]",
                    title="RF Capture",
                    border_style="green",
                )
            )
            self._capture_single_channel(duration)

        self.is_capturing = False

        # Display results
        self._display_results(scan_all)

    def _display_results(self, scan_all=False):
        """Display capture results with Rich formatting"""
        total_packets = len(self.captured_data)

        if total_packets == 0:
            self.console.print("[yellow]No packets captured[/yellow]")
            return

        # Summary panel
        summary_text = f"Captured {total_packets} packets"
        if scan_all and self.channel_activity:
            active_channels = len(self.channel_activity)
            summary_text += f" across {active_channels} channels"

        self.console.print(
            Panel(summary_text, title="Capture Complete", border_style="green")
        )

        # Channel activity table
        if scan_all and self.channel_activity:
            self._display_channel_table()

    def _display_channel_table(self):
        """Display channel activity in a Rich table"""
        table = Table(title="Channel Activity Summary")
        table.add_column("Channel", style="cyan", no_wrap=True)
        table.add_column("Packets", style="magenta", justify="right")
        table.add_column("Activity", style="green")

        # Sort by packet count
        sorted_channels = sorted(
            self.channel_activity.items(), key=lambda x: x[1], reverse=True
        )

        for channel, count in sorted_channels:
            # Create activity bar
            bar_length = min(20, int(count / max(self.channel_activity.values()) * 20))
            activity_bar = "█" * bar_length + "░" * (20 - bar_length)

            table.add_row(str(channel), str(count), f"[green]{activity_bar}[/green]")

        self.console.print(table)

        # Most active channel
        most_active = self.get_most_active_channel()
        if most_active:
            self.console.print(
                f"\n[bold yellow]Most active channel: "
                f"{most_active[0]} ({most_active[1]} packets)[/bold yellow]"
            )

    def _capture_single_channel(self, duration):
        """Capture from a single channel"""
        start_time = time.time()
        while self.is_capturing and (time.time() - start_time) < duration:
            if self.radio.available():
                length = self.radio.getDynamicPayloadSize()
                if length > 0:
                    data = self.radio.read(length)
                    timestamp = time.time()
                    self.captured_data.append(
                        {
                            "timestamp": timestamp,
                            "data": data,
                            "length": length,
                            "channel": self.channel,
                        }
                    )
                    self.console.print(
                        f"[green]Captured:[/green] {data.hex()} at {timestamp}"
                    )

            time.sleep(0.001)

    def _scan_all_channels(self, duration):
        """Scan all channels for activity"""
        start_time = time.time()
        channel_time = 0.1  # Time to spend on each channel
        total_channels = 126

        with Progress(
            TextColumn("[bold blue]Scanning channels"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            scan_task = progress.add_task("Channel scan", total=total_channels)

            while self.is_capturing and (time.time() - start_time) < duration:
                for channel in range(0, total_channels):
                    if not self.is_capturing:
                        break

                    self.radio.setChannel(channel)
                    channel_start = time.time()

                    # Listen on this channel for a short time
                    while (
                        self.is_capturing
                        and (time.time() - channel_start) < channel_time
                        and (time.time() - start_time) < duration
                    ):
                        if self.radio.available():
                            length = self.radio.getDynamicPayloadSize()
                            if length > 0:
                                data = self.radio.read(length)
                                timestamp = time.time()

                                # Track activity on this channel
                                if channel not in self.channel_activity:
                                    self.channel_activity[channel] = 0
                                self.channel_activity[channel] += 1

                                self.captured_data.append(
                                    {
                                        "timestamp": timestamp,
                                        "data": data,
                                        "length": length,
                                        "channel": channel,
                                    }
                                )
                                self.console.print(
                                    f"[blue]Channel {channel}:[/blue] "
                                    f"{data.hex()} at {timestamp}"
                                )

                        time.sleep(0.001)

                    # Update progress
                    progress.update(scan_task, advance=1)

    def stop_capture(self):
        """Stop the capture process"""
        self.is_capturing = False

    def get_captured_data(self):
        """Return captured data"""
        return self.captured_data

    def get_channel_activity(self):
        """Return channel activity summary"""
        return self.channel_activity

    def get_most_active_channel(self):
        """Return the channel with most activity"""
        if not self.channel_activity:
            return None
        return max(self.channel_activity.items(), key=lambda x: x[1])

    def save_capture(self, filename):
        """Save captured data to file"""
        with open(filename, "w") as f:
            for packet in self.captured_data:
                f.write(
                    f"{packet['timestamp']},{packet['channel']},"
                    f"{packet['length']},{packet['data'].hex()}\n"
                )

    def cleanup(self):
        """Clean up GPIO and radio resources"""
        self.radio.stopListening()
        self.radio.powerDown()
        GPIO.cleanup()
