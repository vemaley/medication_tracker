import logging
from typing import Any, Dict, Optional
import datetime

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE
from homeassistant.util import dt as dt_util

from .const import DOMAIN 

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Medication Stock number entity."""
    try:
        # Merge data and options
        config = {**config_entry.data, **config_entry.options}
        
        entity = MedicationStockNumber(
            config_entry.entry_id, 
            config,
        )
        
        # Store reference for service calls
        if DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN][config_entry.entry_id]["number_entity"] = entity

        async_add_entities([entity], True)
    
    except Exception as e:
        _LOGGER.error(f"FATAL CRASH in number setup: {e}")
        return


class MedicationStockNumber(NumberEntity, RestoreEntity):
    """Represents the current stock level of a medication."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, unique_id: str, config: Dict[str, Any]):
        self._device_unique_id = unique_id 
        self._unique_id = f"{unique_id}_stock"
        self._medication_name = config.get("name", "Medication")
        
        # Configuration (Supports decimals)
        self._pills_per_dose = float(config.get("pills_per_dose", 1.0))
        self._doses_per_day = float(config.get("doses_per_day", 1.0))
        self._daily_consumption = self._pills_per_dose * self._doses_per_day
        self._low_stock_days = int(config.get("low_stock_days", 7))
        self._initial_stock = float(config.get("initial_stock", 0.0))
        
        self._current_stock = self._initial_stock 
        self._last_taken: Optional[datetime.datetime] = None
        
        self._attr_name = "Current Stock"
        self._attr_mode = NumberMode.BOX
        self._attr_native_min_value = 0
        self._attr_native_max_value = 10000 
        # Read step_value from config (default 0.01)
        try:
            step_val = float(config.get("step_value", 0.01))
            if step_val <= 0:
                step_val = 0.01
        except (TypeError, ValueError):
            step_val = 0.01

        self._attr_native_step = step_val
        self._attr_unit_of_measurement = "tablets"
        self._attr_icon = "mdi:pill"

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

    @property
    def native_value(self) -> Optional[float]:
        return self._current_stock
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        attrs = {
            "pills_per_dose": self._pills_per_dose, 
            "doses_per_day": self._doses_per_day,
            "daily_consumption": self._daily_consumption,
            "low_stock_days": self._low_stock_days,
            "medication_name": self._medication_name,
        }
        if self._last_taken:
            attrs["last_taken"] = self._last_taken.isoformat()
        return attrs

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        
        if last_state and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._current_stock = float(last_state.state)
            except (ValueError, TypeError):
                self._current_stock = self._initial_stock
            
            # Restore last_taken attribute
            if "last_taken" in last_state.attributes:
                try:
                    self._last_taken = dt_util.parse_datetime(last_state.attributes["last_taken"])
                except Exception:
                    self._last_taken = None
        else:
            self._current_stock = self._initial_stock
        
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value manually."""
        try:
            new_value = float(value)
        except ValueError:
            return
            
        self._current_stock = new_value
        self.async_write_ha_state()

    async def async_take_dose(self) -> None:
        """Action: Take a dose and record history."""
        dose = self._pills_per_dose
        if dose <= 0:
            return
            
        self._current_stock = max(0.0, self._current_stock - dose)
        self._last_taken = dt_util.now()
        
        _LOGGER.info(f"{self._medication_name}: Taken {dose}. New stock: {self._current_stock}")
        self.async_write_ha_state()

    async def async_add_stock(self, amount: float) -> None:
        """Action: Add stock."""
        if amount <= 0:
            return
            
        self._current_stock += amount
        _LOGGER.info(f"{self._medication_name}: Added {amount}. New stock: {self._current_stock}")
        self.async_write_ha_state()
