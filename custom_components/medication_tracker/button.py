import logging
from typing import Any, Dict, List

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SERVICE_TAKE_DOSE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Medication buttons (Refill or Group)."""
    try:
        config = {**config_entry.data, **config_entry.options}
        
        # CASE 1: This is a Medication Group
        if "members" in config:
            async_add_entities([
                MedicationGroupButton(config_entry.entry_id, config, hass)
            ], True)
            return

        # CASE 2: This is a Single Medication (Refill Button)
        # We try to find the linked number entity to enable the refill button
        entry_data = hass.data[DOMAIN].get(config_entry.entry_id)
        number_entity = entry_data.get("number_entity") if entry_data else None

        if number_entity:
            async_add_entities([
                MedicationRefillButton(config_entry.entry_id, config, number_entity)
            ], True)

    except Exception as e:
        _LOGGER.error(f"FATAL CRASH in button setup: {e}")
        return


class MedicationRefillButton(ButtonEntity):
    """Button to add a pre-configured amount of stock to a single med."""
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, unique_id: str, config: Dict[str, Any], number_entity):
        self._device_unique_id = unique_id 
        self._unique_id = f"{unique_id}_refill"
        self._medication_name = config.get("name", "Medication")
        self._refill_amount = int(config.get("refill_amount", 30))
        self._number_entity = number_entity
        self._attr_name = "Refill Stock"
        self._attr_icon = "mdi:pill-multiple"

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def device_info(self) -> Dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._device_unique_id)},
            "name": self._medication_name,
            "manufacturer": "Custom",
            "model": "Medication Tracker",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        if self._number_entity:
            await self._number_entity.async_add_stock(self._refill_amount)


class MedicationGroupButton(ButtonEntity):
    """Button to take a dose for a GROUP of medications."""
    _attr_has_entity_name = True

    def __init__(self, unique_id: str, config: Dict[str, Any], hass: HomeAssistant):
        self.hass = hass
        self._device_unique_id = unique_id
        self._unique_id = f"{unique_id}_take_group"
        self._group_name = config.get("name", "Medication Group")
        self._members: List[str] = config.get("members", [])
        
        self._attr_name = "Take Dose"
        self._attr_icon = "mdi:checkbox-multiple-marked-circle-outline"

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def device_info(self) -> Dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._device_unique_id)},
            "name": self._group_name,
            "manufacturer": "Custom",
            "model": "Medication Group",
        }

    async def async_press(self) -> None:
        """Trigger take_dose for all members."""
        if not self._members:
            return

        _LOGGER.info(f"Group '{self._group_name}' taking dose for: {self._members}")
        
        # We call the service directly on the entity IDs.
        for entity_id in self._members:
            await self.hass.services.async_call(
                DOMAIN, 
                SERVICE_TAKE_DOSE, 
                {"entity_id": entity_id},
                blocking=False 
            )
