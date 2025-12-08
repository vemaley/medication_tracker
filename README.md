[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=vemaley&repository=medication_tracker&category=integration)

# <img src="icon.png" width="40" height="40"> Medication Stock Tracker for Home Assistant

# Medication Stock Tracker for Home Assistant

A custom component to track medication stock levels, calculate days remaining based on usage, and alert you when you are running low.

## Features
* **Track Stock:** Manually or automatically update tablet counts.
* **Days Remaining Calculation:** Automatically estimates how long your supply will last based on your daily dose.
* **Low Stock Alerts:** Built-in "Low Stock" binary sensor and blueprint support.
* **Crash Proof:** Robust error handling and service recovery.

## Installation (HACS)
1.  Go to HACS -> Integrations.
2.  Click the 3 dots (top right) -> **Custom repositories**.
3.  Add the URL of this repository.
4.  Category: **Integration**.
5.  Click **Add**, then install "Medication Stock Tracker".
6.  Restart Home Assistant.

## Configuration
1.  Go to **Settings -> Devices & Services**.
2.  Click **Add Integration** and search for "Medication Stock Tracker".
3.  Follow the setup wizard:
    * **Name:** e.g., "Metformin"
    * **Initial Stock:** Total pills you currently have.
    * **Pills per dose:** e.g., 1
    * **Doses per day:** e.g., 2
    * **Low Stock Threshold:** e.g., 7 days (default).

## Services
You can use these services in automations or dashboard buttons:
* `medication_tracker.take_dose`: Deducts the configured dose amount from the stock.
* `medication_tracker.add_stock`: Adds a specific amount to the stock (e.g., when refilling).

## Dashboard Example (Mushroom/Lovelace)
Here is a clean card configuration. 
**Note:** Replace `metformin` with the name of the medication you added in the setup.

```yaml
type: entities
title: My Medication Tracker
show_header_toggle: false
entities:
  # REPLACE 'metformin' WITH YOUR MEDICATION NAME
  - entity: number.metformin_stock
    name: Current Stock
    icon: mdi:pill
  - entity: sensor.metformin_days_remaining
    name: Days Supply
    icon: mdi:calendar-clock
  - type: divider
  - type: call-service
    name: Take Dose
    icon: mdi:check-circle-outline
    action_name: TAKE
    service: medication_tracker.take_dose
    service_data:
      # MAKE SURE THIS MATCHES YOUR ENTITY ID
      entity_id: number.metformin_stock



