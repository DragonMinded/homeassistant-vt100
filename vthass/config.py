import yaml
from typing import List, Optional


class Entity:
    def __init__(self, entity_id: str, name: Optional[str], units: Optional[str]) -> None:
        if entity_id[:3] == "<hr" and entity_id[-1:] == ">":
            self.entity_id = "<hr>"
            self.name = None
            self.units = None
        elif entity_id[:6] == "<label" and entity_id[-1:] == ">":
            self.entity_id = "<label>"
            self.name = entity_id[6:-1].strip() or name
            self.units = None
        elif entity_id[:9] == "<template" and entity_id[-1:] == ">":
            self.entity_id = "<template>"
            self.name = entity_id[9:-1].strip() or name
            self.units = None
        else:
            self.entity_id = entity_id
            self.name = name
            self.units = units


class Page:
    def __init__(self, name: str, entities: List[Entity]) -> None:
        self.name = name
        self.entities = entities


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
            self.terminal_flow: bool = terminal.get("flow", False)

            # General configuration
            general = yamlfile.get("general", {})
            self.dashboard_name: Optional[str] = general.get("name")
            self.display_help: bool = general.get("show_help", False)

            # Layout configuration
            self.layout: List[Page] = []

            layout = yamlfile.get("layout", [])
            for index, entry in enumerate(layout):
                name = entry.get("name", f"Tab {index + 1}")
                page = Page(name, [])

                for entity in entry.get("entities") or []:
                    if isinstance(entity, str):
                        # Raw entity list.
                        page.entities.append(Entity(entity, None, None))
                    elif isinstance(entity, dict):
                        # Entity description.
                        entity_id = entity.get("entity", "__invalid__")
                        entity_name = entity.get("name", None)
                        entity_units = entity.get("units", None)
                        page.entities.append(Entity(entity_id, entity_name, entity_units))

                self.layout.append(page)
