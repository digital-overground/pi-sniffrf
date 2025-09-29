#!/usr/bin/env python3
"""
Channel scanner with Rich display - Python port of the C++ scanner example
Uses Rich for better terminal output and real-time spectrum display
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
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text


class SpectrumDisplay:
    def __init__(self, console):
        self.console = console
        self.num_channels = 126
        self.values = [0] * self.num_channels
        self.num_reps = 100
        self.current_rep = 0

    def create_header(self):
        """Create the channel number header"""
        # Hundreds digits
        hundreds = "".join(str(i // 100) for i in range(self.num_channels))
        # Tens digits
        tens = "".join(str((i % 100) // 10) for i in range(self.num_channels))
        # Singles digits
        singles = "".join(str(i % 10) for i in range(self.num_channels))
        # Divider
        divider = "~" * self.num_channels

        return f"{hundreds}\n{tens}\n{singles}\n{divider}"

    def create_spectrum_line(self):
        """Create the current spectrum line"""
        line = ""
        for i in range(self.num_channels):
            if self.values[i]:
                # Print hex digit, clamped to F
                line += f"{min(0xF, self.values[i]):X}"
            else:
                line += "-"
        return line

    def update_channel(self, channel, found_signal):
        """Update a single channel's value"""
        if found_signal:
            self.values[channel] += 1

    def reset_values(self):
        """Reset all channel values"""
        self.values = [0] * self.num_channels
        self.current_rep = 0

    def increment_rep(self):
        """Increment repetition counter"""
        self.current_rep += 1

    def is_rep_complete(self):
        """Check if current repetition is complete"""
        return self.current_rep >= self.num_reps


def scan_spectrum(radio, console, data_rate="1"):
    """Main scanning function with Rich display"""

    # Configure radio
    if data_rate == "2":
        radio.setDataRate(RF24_2MBPS)
        rate_text = "2 Mbps"
    elif data_rate == "250":
        radio.setDataRate(RF24_250KBPS)
        rate_text = "250 kbps"
    else:
        radio.setDataRate(RF24_1MBPS)
        rate_text = "1 Mbps"

    # Configure for noise detection
    radio.set_auto_ack(False)
    radio.disableCRC()
    radio.setAddressWidth(2)

    # Use multiple noise addresses
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

    # Create display
    display = SpectrumDisplay(console)

    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(Panel("nRF24L01 Channel Scanner", style="bold blue"), size=3),
        Layout(name="main"),
        Layout(
            Panel(f"Data Rate: {rate_text} | Press Ctrl+C to exit", style="dim"), size=3
        ),
    )

    layout["main"].split_row(Layout(name="header", size=4), Layout(name="spectrum"))

    # Set header content
    layout["header"].update(
        Panel(display.create_header(), title="Channels", border_style="green")
    )

    try:
        with Live(layout, console=console, refresh_per_second=10) as live:
            while True:
                # Clear measurement values
                display.reset_values()

                # Scan all channels
                while not display.is_rep_complete():
                    for channel in range(display.num_channels):
                        # Select this channel
                        radio.channel = channel

                        # Listen for a little
                        radio.listen = True
                        time.sleep(0.00013)  # 130 microseconds
                        found_signal = radio.testRPD()
                        radio.listen = False

                        # Check for signal using multiple methods
                        if found_signal or radio.testRPD() or radio.available():
                            display.update_channel(channel, True)
                            radio.flush_rx()  # discard packets of noise

                    display.increment_rep()

                    # Update spectrum display
                    spectrum_line = display.create_spectrum_line()
                    layout["spectrum"].update(
                        Panel(
                            spectrum_line,
                            title="Signal Strength",
                            border_style="yellow",
                        )
                    )

                # Show summary
                active_channels = [
                    i for i, count in enumerate(display.values) if count > 0
                ]
                if active_channels:
                    summary = f"Active channels: {', '.join(map(str, active_channels))}"
                    layout["spectrum"].update(
                        Panel(
                            f"{spectrum_line}\n\n[green]{summary}[/green]",
                            title="Signal Strength",
                            border_style="yellow",
                        )
                    )

                time.sleep(0.1)  # Brief pause between scans

    except KeyboardInterrupt:
        console.print(
            "\n[yellow]Keyboard Interrupt detected. Powering down radio...[/yellow]"
        )
        radio.power = False


def main():
    console = Console()
    console.print(f"[bold blue]{sys.argv[0]}[/bold blue]")

    # Radio setup
    CSN_PIN = 0
    CE_PIN = 25  # GPIO25 for your setup
    radio = RF24(CE_PIN, CSN_PIN)

    # Setup the radio
    if not radio.begin():
        console.print("[red]Radio hardware not responding![/red]")
        return 1

    console.print(
        "\n[bold]!!! This example requires a width of at least 126 characters.[/bold]"
    )

    # Data rate selection
    console.print("\n[cyan]Select your Data Rate:[/cyan]")
    console.print("  [green]1[/green] - 1 Mbps (default)")
    console.print("  [green]2[/green] - 2 Mbps")
    console.print("  [green]3[/green] - 250 kbps")

    try:
        data_rate = input("\nEnter choice (1-3): ").strip()
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/yellow]")
        return 0

    if data_rate.startswith("2"):
        console.print("[green]Using 2 Mbps.[/green]")
        rate = "2"
    elif data_rate.startswith("3"):
        console.print("[green]Using 250 kbps.[/green]")
        rate = "250"
    else:
        console.print("[green]Using 1 Mbps.[/green]")
        rate = "1"

    # Start scanning
    scan_spectrum(radio, console, rate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
