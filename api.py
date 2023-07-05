import requests
from typing import Dict, List, Optional


class Entity:
    def __init__(self, api: "HomeAssistant", entity_id: str) -> None:
        self.api = api
        self.entity_id = entity_id

    def _merge(self, other: "Entity") -> None:
        pass

    def __repr__(self) -> str:
        return f"Entity({self.entity_id!r})"


class SwitchEntity(Entity):
    def __init__(
        self, api: "HomeAssistant", entity_id: str, name: str, initial_state: bool
    ) -> None:
        super().__init__(api, entity_id)
        self.name: str = name
        self.__state: Optional[bool] = initial_state

    def _merge(self, other: Entity) -> None:
        if isinstance(other, SwitchEntity):
            self.name = other.name
            self.__state = other.__state

    @property
    def state(self) -> Optional[bool]:
        return self.__state

    @state.setter
    def state(self, new_state: bool) -> None:
        self.api.setSwitchState(self.entity_id, new_state)
        self.__state = self.api.getSwitchState(self.entity_id)

    def __repr__(self) -> str:
        return f"SwitchEntity({self.entity_id!r}, {self.name!r}, {self.__state!r})"


class HomeAssistant:
    def __init__(self, uri: str, token: str) -> None:
        self.uri = uri + ("/" if uri[-1] != "/" else "")
        self.token = token

    def getEntities(self) -> Optional[List[Entity]]:
        url = f"{self.uri}api/states"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        }
        try:
            entities: List[Entity] = []

            response = requests.get(url, headers=headers, timeout=3.0)
            response.raise_for_status()

            data = response.json()
            for entry in data:
                if "attributes" not in entry:
                    pass

                device = entry["attributes"].get("device_class")
                entity_id = entry["entity_id"]
                if device == "switch" or entity_id.startswith("switch."):
                    name = entry["attributes"].get("friendly_name", entity_id)
                    entities.append(
                        SwitchEntity(
                            self,
                            entity_id,
                            name,
                            bool(entry.get("state", "off").lower() == "on"),
                        )
                    )

            return entities
        except Exception as e:
            print(f"Failed to fetch entities!\n{e}")
            return None

    def refreshEntities(self, entities: List[Entity]) -> bool:
        entities_by_id: Dict[str, Entity] = {e.entity_id: e for e in entities}

        new_states = self.getEntities()
        if new_states:
            for entity in new_states:
                if entity.entity_id in entities_by_id:
                    entities_by_id[entity.entity_id]._merge(entity)

        return new_states is not None

    def getSwitchState(self, entity: str) -> Optional[bool]:
        url = f"{self.uri}api/states/{entity}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        }
        try:
            response = requests.get(url, headers=headers, timeout=3.0)
            response.raise_for_status()

            data = response.json()
            if data.get("entity_id", None) != entity:
                return None

            return bool(data.get("state", "off").lower() == "on")
        except Exception as e:
            print(f"Failed to fetch {entity} state!\n{e}")
            return None

    def setSwitchState(self, entity: str, newstate: bool) -> None:
        url = f"{self.uri}api/services/switch/turn_{'on' if newstate else 'off'}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        }
        request = {
            "entity_id": entity,
        }
        try:
            requests.post(url, headers=headers, json=request, timeout=3.0)
        except Exception as e:
            print(f"Failed to update {entity} state!\n{e}")
