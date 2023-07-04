import argparse
import sys
import time
import threading
from multiprocessing import Process
from typing import Optional

from api import HomeAssistant
from config import Config
from monitor import monitoring_thread
from vtpy import Terminal, TerminalException


def spawnTerminal(port: str, baudrate: int) -> Terminal:
    print("Attempting to contact VT-100...", end="")
    sys.stdout.flush()

    while True:
        try:
            terminal = Terminal(port, baudrate)
            print("SUCCESS!")

            break
        except TerminalException:
            # Wait for terminal to re-awaken.
            time.sleep(1.0)

            print(".", end="")
            sys.stdout.flush()

    return terminal


def main(config: Config) -> None:
    if config.homeassistant_uri is None or config.homeassistant_token is None:
        raise Exception(
            "Expected configuration file to include Home Assistant URI and API Token!"
        )

    hass = HomeAssistant(config.homeassistant_uri, config.homeassistant_token)
    entities = hass.getEntities()
    exiting = False
    while not exiting:
        terminal = spawnTerminal(config.terminal_port, config.terminal_baud)

        try:
            while not exiting:
                # Grab input, de-duplicate held down up/down presses so they don't queue up.
                # This can cause the entire message loop to desync as we pile up requests to
                # scroll the screen, ultimately leading in rendering issues and a crash.
                inputVal = terminal.recvInput()
                if inputVal in {Terminal.UP, Terminal.DOWN}:
                    while inputVal == terminal.peekInput():
                        terminal.recvInput()

            print("*")

        except TerminalException:
            # Terminal went away mid-transaction.
            print("Lost terminal, will attempt a reconnect.")
        except KeyboardInterrupt:
            print("Got request to end session!")
            exiting = True

    # Restore the screen before exiting.
    terminal.reset()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Dashboard frontend for Home Assistant that talks to VT-100 compatible terminals.",
    )
    parser.add_argument(
        "--config",
        metavar="CONFIG",
        type=str,
        default="config.yaml",
        help="Configuration file for dashboard. Defaults to config.yaml",
    )
    args = parser.parse_args()
    config = Config(args.config)
    proc: Optional[Process] = None

    # Start monitor just in case we want to monitor this from the main home assistant instance.
    if config.homeassistant_monitoring_port is not None:
        proc = Process(
            target=monitoring_thread,
            args=(
                config.homeassistant_monitoring_port,
                "1.0.0",
            ),
        )
        proc.start()

    try:
        main(config)
    finally:
        # Kill monitor thread now that we're out.
        if proc:
            proc.terminate()

    # Wait until all application threads have terminated.
    for t in threading.enumerate():
        try:
            t.join()
        except RuntimeError:
            pass
