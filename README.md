[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=vemaley&repository=medication_tracker&category=integration)

# <img src="icon.png" width="40" height="40"> Medication Stock Tracker for Home Assistant

# Medication Stock Tracker for Home Assistant

A custom component to track medication stock levels, calculate days remaining based on usage, and alert you when you are running low.

## Features
* **Track Stock:** Manually or automatically update tablet counts.
* **Days Remaining Calculation:** Automatically estimates how long your supply will last based on your daily dose.
* **Low Stock Alerts:** Built-in "Low Stock" binary sensor and blueprint support.
* **Crash Proof:** Robust error handling and service recovery.

* ## Automations
This integration comes with a blueprint to easily set up low-stock alerts.

[![Open your Home Assistant instance and show the blueprint import dialog with a specific blueprint URL.](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fvemaley%2Fmedication_tracker%2Fblob%2Fmain%2Fblueprints%2Flow_stock_alert.yaml)

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

## 🎨 Dashboard Example (Mushroom Cards)
This integration works beautifully with [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom). Here is a complete card configuration that shows stock status, history, and quick actions.

**Features:**
* **Dynamic Icon Color:** Turns red when stock is low (< 7 days).
* **Smart History:** Shows "Last taken: X minutes ago".
* **Quick Actions:** One-tap buttons to take a dose or add a refill.

```yaml
type: vertical-stack
cards:
  # --- MAIN STATUS CARD ---
  - type: custom:mushroom-template-card
    primary: My Medication
    secondary: >
      {{ states('number.my_medication_stock') }} tablets left 
      ({{ states('sensor.my_medication_days_remaining') }} days)
    icon: mdi:pill
    icon_color: >
      {% if states('sensor.my_medication_days_remaining') | float(0) <= 7 %} red
      {% else %} green
      {% endif %}
    tap_action:
      action: more-info
      entity: number.my_medication_stock

  # --- ACTION ROW ---
  - type: horizontal-stack
    cards:
      # 1. HISTORY
      - type: custom:mushroom-template-card
        primary: Last Taken
        secondary: >
          {% set last = state_attr('number.my_medication_stock', 'last_taken') %}
          {% if last %} {{ relative_time(last) }} ago
          {% else %} Never {% endif %}
        icon: mdi:history
        icon_color: blue
        layout: vertical
        tap_action:
          action: none

      # 2. TAKE DOSE BUTTON
      - type: custom:mushroom-template-card
        primary: Take Dose
        secondary: Record usage
        icon: mdi:check-circle-outline
        icon_color: teal
        layout: vertical
        tap_action:
          action: call-service
          service: medication_tracker.take_dose
          service_data:
            entity_id: number.my_medication_stock

      # 3. ADD STOCK BUTTON (Set 'amount' to your pack size)
      - type: custom:mushroom-template-card
        primary: Add Stock
        secondary: +30 tabs
        icon: mdi:plus-box-outline
        icon_color: green
        layout: vertical
        tap_action:
          action: call-service
          service: medication_tracker.add_stock
          service_data:
            entity_id: number.my_medication_stock
            amount: 30






