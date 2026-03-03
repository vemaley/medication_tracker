import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Common schemas
def get_dosage_schema(defaults: Dict[str, Any] = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema({
        vol.Required("pills_per_dose", default=defaults.get("pills_per_dose", 1.0)): vol.Coerce(float),
        vol.Required("doses_per_day", default=defaults.get("doses_per_day", 1.0)): vol.Coerce(float),
        vol.Optional(
            "step_value",
            default=defaults.get("step_value", 0.01)
        ): vol.All(vol.Coerce(float), vol.Range(min=0.01)),
    })

def get_threshold_schema(defaults: Dict[str, Any] = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema({
        vol.Optional("low_stock_days", default=defaults.get("low_stock_days", 7)): int,
    })

class MedicationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Medication Tracker."""

    VERSION = 1
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return MedicationOptionsFlowHandler(config_entry)

    data: Dict[str, Any] = {}

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle the initial step."""
        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_dosage()

        DATA_SCHEMA = vol.Schema(
            {
                vol.Required("name"): str,
                vol.Required("initial_stock", description="Starting number of tablets"): vol.Coerce(float),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors={},
            description_placeholders={
                "info": "Enter the name of the medication and your starting tablet count."
            }
        )

    async def async_step_dosage(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle the dosage step."""
        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_threshold()

        return self.async_show_form(
            step_id="dosage",
            data_schema=get_dosage_schema(),
            errors={},
            description_placeholders={
                "info": "Enter the dosage details (decimals allowed)."
            }
        )

    async def async_step_threshold(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle the threshold step."""
        if user_input is not None:
            self.data.update(user_input)
            
            # Calculate daily consumption for initial setup (informational log only, entity calculates dynamically)
            daily_consumption = self.data["pills_per_dose"] * self.data["doses_per_day"]
            self.data["daily_consumption"] = daily_consumption 
            
            if "low_stock_days" not in self.data:
                self.data["low_stock_days"] = 7
            
            _LOGGER.info(f"Medication Configured: {self.data['name']} - Daily Use: {daily_consumption} tablets.")

            return self.async_create_entry(
                title=self.data["name"], 
                data=self.data
            )

        return self.async_show_form(
            step_id="threshold",
            data_schema=get_threshold_schema(),
            errors={},
            description_placeholders={
                "info": "Set the low stock alert level (in days of supply)."
            }
        )

class MedicationOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Medication Tracker options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        # FIXED: Use self._config_entry to avoid conflict with property 'config_entry'
        self._config_entry = config_entry

    async def async_step_init(self, user_input: Dict[str, Any] = None) -> Dict[str, Any]:
        """Manage the options."""
        if user_input is not None:
            # Update entry options
            return self.async_create_entry(title="", data=user_input)

        # Combine data and options to show current values as defaults
        # Use self._config_entry here
        current_config = {**self._config_entry.data, **self._config_entry.options}

        # Build schema with current values
        schema = vol.Schema({
            **get_dosage_schema(current_config).schema,
            **get_threshold_schema(current_config).schema,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "info": "Update dosage and alert settings."
            }
        )
