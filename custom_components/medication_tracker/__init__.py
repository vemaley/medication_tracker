import logging
import traceback
from functools import partial
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import discovery

# Define domain and constants
DOMAIN = "medication_tracker"
_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["number", "sensor"]

# Service definitions
SERVICE_TAKE_DOSE = "take_dose"
SERVICE_ADD_STOCK = "add_stock"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Medication Tracker from a config entry."""
    
    try: 
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}
        
        # Initialize storage for this entry
        hass.data[DOMAIN][entry.entry_id] = {
            "data": dict(entry.data),
            "number_entity": None # Reference to the number entity instance
        }
        
        # 1. Register the service handlers (only once)
        if not hass.services.has_service(DOMAIN, SERVICE_TAKE_DOSE):
            hass.services.async_register(
                DOMAIN, 
                SERVICE_TAKE_DOSE, 
                partial(_handle_service_call, hass, service_type=SERVICE_TAKE_DOSE)
            )
            hass.services.async_register(
                DOMAIN, 
                SERVICE_ADD_STOCK, 
                partial(_handle_service_call, hass, service_type=SERVICE_ADD_STOCK)
            )
        
        # 2. Set up platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        # 3. Add update listener for options flow
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))
        
        _LOGGER.info("Medication Tracker setup successful for entry: %s", entry.title)
        return True

    except Exception as e: 
        _LOGGER.error(
            "FATAL UNHANDLED CRASH during component setup for entry %s.\nError: %s\nTraceback:\n%s", 
            entry.entry_id, str(e), traceback.format_exc()
        )
        return False

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def _handle_service_call(hass: HomeAssistant, call: ServiceCall, service_type: str):
    """Robust handler for service calls that updates the entity instance."""
    
    # Handle Entity ID as list or string
    raw_entity_id = call.data.get(ATTR_ENTITY_ID)
    if isinstance(raw_entity_id, list):
        entity_id = raw_entity_id[0]
    else:
        entity_id = raw_entity_id

    if not entity_id:
        _LOGGER.error("Service call failed: Missing 'entity_id'.")
        return

    # Find the entity instance across all configured entries
    target_entity = None
    for entry_id, entry_data in hass.data[DOMAIN].items():
        number_ref = entry_data.get("number_entity")
        if number_ref and number_ref.entity_id == entity_id:
            target_entity = number_ref
            break
            
    if not target_entity:
        _LOGGER.error("Could not find loaded entity instance for %s", entity_id)
        return

    try:
        if service_type == SERVICE_TAKE_DOSE:
            await target_entity.async_take_dose()
            
        elif service_type == SERVICE_ADD_STOCK:
            amount = float(call.data.get("amount", 0))
            await target_entity.async_add_stock(amount)
            
    except Exception as e:
        _LOGGER.error(
            "Error in service '%s' for %s: %s", 
            service_type, entity_id, str(e)
        )
