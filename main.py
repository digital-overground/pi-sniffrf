#!/usr/bin/env python3

import argparse
import signal
import sys
import time

from rich.console import Console
from rich.panel import Panel

from rf_capture import RFCapture
from rf_repeat import RFRepeat


class RFSniffer:
    def __init__(self, capture_ce=22, capture_csn=0, repeat_ce=24, repeat_csn=1):
        self.capture = RFCapture(ce_pin=capture_ce, csn_pin=capture_csn)
        self.repeat = RFRepeat(ce_pin=repeat_ce, csn_pin=repeat_csn)
        self.running = True
        self.console = Console()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.console.print("\n[yellow]Shutting down...[/yellow]")
        self.running = False
        self.capture.stop_capture()
        self.repeat.stop_repeat()
        self.cleanup()
        sys.exit(0)

    def setup(self):
        """Initialize both RF modules"""
        try:
            self.capture.setup()
            self.repeat.setup()
            self.console.print(
                Panel(
                    "[bold green]RF modules initialized successfully[/bold green]",
                    title="Hardware Status",
                    border_style="green",
                )
            )
        except Exception as e:
            self.console.print(
                Panel(
                    f"[bold red]Failed to initialize RF modules: {e}[/bold red]",
                    title="Hardware Error",
                    border_style="red",
                )
            )
            sys.exit(1)

    def capture_mode(self, duration=60, channel=76, output_file=None, scan_all=False):
        """Run in capture mode"""
        if not scan_all:
            self.capture.channel = channel
        self.capture.setup()

        if output_file is None:
            output_file = f"capture_{int(time.time())}.txt"

        self.capture.start_capture(duration, scan_all)
        self.capture.save_capture(output_file)
        self.console.print(f"[green]Capture saved to {output_file}[/green]")

        if scan_all:
            most_active = self.capture.get_most_active_channel()
            if most_active:
                self.console.print(
                    f"[bold yellow]Most active channel: "
                    f"{most_active[0]} ({most_active[1]} packets)[/bold yellow]"
                )

    def repeat_mode(self, input_file, delay=0.1, channel=76):
        """Run in repeat mode"""
        self.repeat.channel = channel
        self.repeat.setup()

        self.console.print(
            Panel(
                f"[bold blue]Repeating packets from {input_file}[/bold blue]",
                title="RF Repeater",
                border_style="blue",
            )
        )
        success_count = self.repeat.repeat_from_file(input_file, delay)
        self.console.print(
            f"[green]Successfully repeated {success_count} packets[/green]"
        )

    def live_repeat_mode(self, duration=60, channel=76, delay=0.1):
        """Capture and immediately repeat signals"""
        self.capture.channel = channel
        self.repeat.channel = channel

        self.capture.setup()
        self.repeat.setup()

        self.console.print(
            Panel(
                f"[bold magenta]Live repeat mode - capturing and repeating on "
                f"channel {channel}[/bold magenta]",
                title="Live RF Repeater",
                border_style="magenta",
            )
        )
        self.console.print("[yellow]Press Ctrl+C to stop[/yellow]")

        start_time = time.time()

        while self.running and (time.time() - start_time) < duration:
            if self.capture.radio.available():
                length = self.capture.radio.getDynamicPayloadSize()
                if length > 0:
                    data = self.capture.radio.read(length)
                    self.console.print(f"[green]Captured:[/green] {data.hex()}")

                    # Immediately repeat the captured signal
                    self.repeat.repeat_packet(data, delay)

            time.sleep(0.001)

    def cleanup(self):
        """Clean up resources"""
        self.capture.cleanup()
        self.repeat.cleanup()


def main():
    parser = argparse.ArgumentParser(description="RF Signal Capture and Repeat Tool")
    parser.add_argument(
        "mode", choices=["capture", "repeat", "live", "scan"], help="Operation mode"
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=int,
        default=60,
        help="Duration in seconds (default: 60)",
    )
    parser.add_argument(
        "-c", "--channel", type=int, default=76, help="RF channel (default: 76)"
    )
    parser.add_argument("-f", "--file", type=str, help="Input/output file")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay between repeated packets (default: 0.1)",
    )
    parser.add_argument(
        "--capture-ce", type=int, default=22, help="Capture module CE pin (default: 22)"
    )
    parser.add_argument(
        "--capture-csn", type=int, default=0, help="Capture module CSN pin (default: 0)"
    )
    parser.add_argument(
        "--repeat-ce", type=int, default=24, help="Repeat module CE pin (default: 24)"
    )
    parser.add_argument(
        "--repeat-csn", type=int, default=1, help="Repeat module CSN pin (default: 1)"
    )
    parser.add_argument(
        "--scan", action="store_true", help="Scan all channels (capture mode only)"
    )

    args = parser.parse_args()

    sniffer = RFSniffer(
        capture_ce=args.capture_ce,
        capture_csn=args.capture_csn,
        repeat_ce=args.repeat_ce,
        repeat_csn=args.repeat_csn,
    )

    try:
        if args.mode == "capture":
            sniffer.capture_mode(args.duration, args.channel, args.file, args.scan)
        elif args.mode == "scan":
            sniffer.capture_mode(args.duration, args.channel, args.file, True)
        elif args.mode == "repeat":
            if not args.file:
                sniffer.console.print(
                    Panel(
                        "[bold red]Error: Input file required for repeat mode[/bold red]",
                        title="Error",
                        border_style="red",
                    )
                )
                sys.exit(1)
            sniffer.repeat_mode(args.file, args.delay, args.channel)
        elif args.mode == "live":
            sniffer.live_repeat_mode(args.duration, args.channel, args.delay)

    except KeyboardInterrupt:
        sniffer.console.print("\n[yellow]Interrupted by user[/yellow]")
    finally:
        sniffer.cleanup()


if __name__ == "__main__":
    main()
