import logging
from typing import Any, Dict
import traceback

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback, State, Event
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_call_later
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN 

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Medication Days Remaining sensor entity."""
    try:
        config = {**config_entry.data, **config_entry.options}
        
        base_unique_id = config_entry.entry_id
        number_unique_id = f"{base_unique_id}_stock"
        
        entities = [
            MedicationDaysRemainingSensor(
                hass,
                base_unique_id,
                config,
                number_unique_id,
            )
        ]
        async_add_entities(entities, True)

    except Exception as e:
        _LOGGER.error(f"FATAL CRASH in sensor setup: {e}")
        return


class MedicationDaysRemainingSensor(SensorEntity):
    """Represents the estimated days remaining until a medication runs out."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    
    def __init__(self, hass: HomeAssistant, base_unique_id: str, config: Dict[str, Any], number_unique_id: str):
        self.hass = hass
        self._base_unique_id = base_unique_id 
        self._unique_id = f"{base_unique_id}_days_remaining"
        self._name = config.get("name", "Medication")
        self._number_unique_id = number_unique_id 
        
        pills_per_dose = float(config.get("pills_per_dose", 1.0))
        doses_per_day = float(config.get("doses_per_day", 1.0))
        
        self._daily_consumption = pills_per_dose * doses_per_day
        self._low_stock_days = int(config.get("low_stock_days", 7))
        
        self._days_remaining = None
        self._current_stock = None
        
        self._attr_name = "Days Remaining"
        
        # FIXED: Use _attr_native_unit_of_measurement to resolve "None" unit error
        self._attr_native_unit_of_measurement = 'd' 
        self._attr_icon = "mdi:calendar-clock"
        self._attr_device_class = SensorDeviceClass.DURATION
        
        self._remove_listener = None
        self._retry_count = 0 

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def device_info(self) -> Dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._base_unique_id)},
            "name": self._name,
            "manufacturer": "Custom",
            "model": "Medication Tracker",
        }

    @property
    def native_value(self) -> float | None:
        return self._days_remaining

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        is_low_stock = False
        if self._days_remaining is not None and self._low_stock_days is not None:
             is_low_stock = self._days_remaining <= self._low_stock_days
        
        return {
            "stock_level": self._current_stock,
            "daily_consumption": self._daily_consumption,
            "low_stock_threshold_days": self._low_stock_days,
            "is_low_stock": is_low_stock,
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._setup_stock_listener()

    @callback
    def _setup_stock_listener(self, *args) -> None:
        entity_registry = er.async_get(self.hass)
        number_entity_id = entity_registry.async_get_entity_id(
            "number", DOMAIN, self._number_unique_id
        )

        if not number_entity_id:
            self._retry_count += 1
            if self._retry_count > 10:
                _LOGGER.debug(f"Stop retrying to link {self._name} after 10 attempts. Entity not ready.")
                return
            self._remove_listener = async_call_later(self.hass, 5.0, self._setup_stock_listener)
            return

        if self._remove_listener:
            self._remove_listener()

        @callback
        def async_stock_state_listener(event: Event) -> None:
            new_state = event.data.get("new_state")
            if new_state is None:
                return
            self._update_state_from_stock(new_state)
            self.async_write_ha_state()

        self._remove_listener = async_track_state_change_event(
            self.hass, 
            [number_entity_id], 
            async_stock_state_listener
        )
        
        current_state = self.hass.states.get(number_entity_id)
        if current_state:
            self._update_state_from_stock(current_state)
            self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()
        await super().async_will_remove_from_hass()

    @callback
    def _update_state_from_stock(self, state: State) -> None:
        if state and state.state not in ("unavailable", "unknown", None):
            try:
                stock_value = float(state.state)
                self._current_stock = stock_value
                if self._daily_consumption and self._daily_consumption > 0:
                    self._days_remaining = round(stock_value / self._daily_consumption, 2)
                else:
                    self._days_remaining = 9999.0
            except ValueError:
                self._days_remaining = None
        else:
            self._days_remaining = None
