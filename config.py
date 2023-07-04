import yaml
from typing import Optional


class Config:
    def __init__(self, file: str) -> None:
        with open(file, "r") as stream:
            yamlfile = yaml.safe_load(stream)

            # Basic config for where to get home assistant stuff
            hass = yamlfile.get("homeassistant", {})
            self.homeassistant_uri: Optional[str] = hass.get("url", None)
            self.homeassistant_token: Optional[str] = hass.get("token", None)

            # If present, read the monitoring port argument to put a simple HTTP
            # monitoring page up.
            monitoring = hass.get("monitoring", {})
            enabled = bool(monitoring.get("enabled", False))
            if enabled:
                port = int(monitoring.get("port", 8080))
            else:
                port = None
            self.homeassistant_monitoring_port: Optional[int] = port

            # Terminal configuration
            terminal = yamlfile.get("terminal", {})
            self.terminal_port: str = terminal.get("port", "/dev/ttyUSB0")
            self.terminal_baud: int = int(terminal.get("baud", "9600"))
