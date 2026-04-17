# KairosLoop

**Closed-loop tool wear compensation system for CNC machining**

KairosLoop monitors part measurements from gauges, calculates feature deviations, and automatically sends tool offset adjustments to CNC controllers to maintain dimensional accuracy as tools wear.

---

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Gauge     │────▶│  Measurement │────▶│ Compensation │────▶│  Controller │
│  (N1700)    │     │   Engine     │     │    Engine    │     │   (PLC)     │
└─────────────┘     └─────────────┘     └──────────────┘     └─────────────┘
       │                   │                    │                    │
       │                   ▼                    ▼                    │
       │            ┌─────────────┐     ┌──────────────┐            │
       │            │  Feature    │     │    Tool      │            │
       │            │ Calculation │     │  Assignment  │            │
       │            └─────────────┘     └──────────────┘            │
       │                                                             │
       └──────────────────── WebSocket ─────────────────────────────┘
                          (Live Dashboard)
```

### Data Flow

1. **Gauge** reads raw channel values (e.g., two opposing probes measuring OD)
2. **Feature** calculates derived value using formula (e.g., `(A + B) / 2`)
3. **Measurement** records computed value, deviation from nominal, and status (OK/WARN/ALARM)
4. **CompensationRule** evaluates if offset is needed based on deviation vs threshold
5. **CompensationEvent** records the offset sent to the controller
6. **ToolAssignment** tracks accumulated wear offset and usage percentage
7. **Controller** receives offset via protocol (Focas, MTConnect, Modbus, etc.)

---

## Django Apps

### `controller`
Machine and CNC controller configuration.

**Models:**
- `Machine` - Physical machine (name, location, is_active)
- `ControllerConfig` - CNC connection settings (protocol, host, port, offset_method, on_tool_limit)

**Protocols:** FOCAS, MTCONNECT, MODBUS_TCP, OPCUA, HEIDENHAIN, MAZAK, HAAS, TEST

### `measurement`
Gauge configuration and feature definitions.

**Models:**
- `GaugeConfig` - Gauge hardware (driver_type, filter_level, machine FK)
- `ChannelConfig` - Individual probe/channel (gauge FK, channel_index, name, enabled)
- `Feature` - Calculated measurement (formula, nominal, tolerance_upper/lower, tolerance_mode)
- `FeatureInput` - Maps formula variables to channels (feature FK, label like 'A', channel_index)
- `Measurement` - Recorded reading (feature FK, computed_value, deviation, status, timestamp)

**Feature Types:** DIAMETER, LENGTH, POSITION, RUNOUT, CONCENTRICITY, PERPENDICULARITY, PARALLELISM, CUSTOM

**Tolerance Modes:** BILATERAL (±), UNILATERAL_PLUS (+0/-x), UNILATERAL_MINUS (-0/+x)

### `tooling`
Tool lifecycle and wear tracking.

**Models:**
- `ToolType` - Tool definition (name, manufacturer, part_number, tool_kind, max_offset_distance)
- `ToolInstance` - Physical tool (tool_type FK, uuid, status, total_parts_cut, total_accumulated_wear)
- `ToolAssignment` - Tool loaded in machine (tool_instance FK, controller FK, tool_position, accumulated_offset, cycle_count, status)

**Tool Kinds:** insert, drill, endmill, reamer, tap, boring_bar, turning, grooving, threading, custom

**Assignment Status:** ACTIVE, WARNING, CHANGE_REQUIRED, REPLACED

**Key Properties:**
- `usage_percentage` - accumulated_offset / tool_type.max_offset_distance × 100
- `tool_type` (shortcut) - returns tool_instance.tool_type

### `compensation`
Compensation rules and event logging.

**Models:**
- `CompensationRule` - Links feature to tool (feature FK, tool_assignment FK, offset_axis, trigger_threshold, max_per_cycle, warning_threshold)
- `CompensationEvent` - Offset record (rule FK, measurement FK, offset_applied, accumulated_after, status, reason)

**Trigger Modes:** THRESHOLD, EVERY_PART, MANUAL

**Key Properties:**
- `tool_position` - returns tool_assignment.tool_position
- `controller` - returns tool_assignment.controller

### `simulator`
Test environment for development without real hardware.

**Key Files:**
- `seed.py` - Creates test data (gauge, channels, feature, tool, assignment, rule)
- `gauge.py` - Simulates gauge readings with wear and random variation
- `engine.py` - Simulation loop
- `plc.py` - Test PLC for offset storage

**Usage:**
```python
python manage.py shell
>>> from simulator.seed import seed_all, reset_all, validate
>>> seed_all(force=True)  # Create/reset all test data
>>> validate()            # Check configuration
```

### `dashboard`
Operator interface and setup pages.

**Views:**
- `dashboard()` - Live monitoring with trend chart, channel values, tool wear, recent offsets
- `setup()` - Configuration management with side menu + detail panel
- `toggle_*()` - AJAX endpoints for enabling/disabling items

### `logs`
System logging (structure TBD).

---

## Database Schema (Key Relationships)

```
Machine
  └── ControllerConfig (machine_id)
        └── ToolAssignment (controller_id)
              └── CompensationRule (tool_assignment_id)
                    └── CompensationEvent (rule_id)

GaugeConfig (machine_id)
  └── ChannelConfig (gauge_id)

Feature
  ├── FeatureInput (feature_id) → channel_index
  ├── Measurement (feature_id)
  └── CompensationRule (feature_id)

ToolType
  └── ToolInstance (tool_type_id)
        └── ToolAssignment (tool_instance_id)
```

---

## Key Calculations

### Feature Deviation
```python
deviation = computed_value - nominal
```

### Tolerance Status
```python
if abs(deviation) <= tolerance * (warning_percent / 100):
    status = 'OK'
elif abs(deviation) <= tolerance:
    status = 'WARN'
else:
    status = 'ALARM'
```

### Tool Usage Percentage
```python
usage_percentage = (accumulated_offset / max_offset_distance) * 100
```

### Compensation Trigger
```python
if abs(deviation) > trigger_threshold:
    offset = min(abs(deviation), max_per_cycle) * sign(deviation) * offset_direction
    # Send to controller
```

---

## URL Structure

```
/                           → dashboard (live monitoring)
/setup/                     → setup page (configuration)
/setup/toggle/feature/<id>/ → AJAX toggle
/setup/toggle/rule/<id>/    → AJAX toggle
/setup/toggle/controller/<id>/ → AJAX toggle
/setup/toggle/gauge/<id>/   → AJAX toggle

/measurement/               → feature list
/measurement/feature/add/   → add feature
/measurement/feature/<id>/  → edit feature
/measurement/gauge/         → gauge list
/measurement/gauge/add/     → add gauge
/measurement/gauge/<id>/    → edit gauge
/measurement/gauge/<id>/channel/add/ → add channel
/measurement/channel/<id>/  → edit channel

/controller/                → controller list
/controller/add/            → add controller
/controller/<id>/           → edit controller

/compensation/              → rule list
/compensation/add/          → add rule
/compensation/<id>/         → edit rule
```

---

## Frontend Stack

- **Django Templates** with Jinja-style syntax
- **Vanilla JavaScript** for interactivity
- **WebSocket** (Django Channels + Redis) for live updates
- **CSS Variables** for dark theme (industrial look)

### CSS Color Scheme
```css
--bg-primary: #0a0a0a;
--bg-panel: #111111;
--bg-card: #1a1a1a;
--bg-recessed: #0d0d0d;
--border-dark: #2a2a2a;
--border-light: #3a3a3a;
--text-primary: #ffffff;
--text-secondary: #b0b0b0;
--text-dim: #666666;
--green: #00ff88;
--red: #ff3333;
--yellow: #ffcc00;
--blue: #00aaff;
```

---

## Simulator Configuration

The simulator creates:
- **Gauge:** Marposs N1700 with n1700 driver
- **Channels:** CH0 "OD Probe Left", CH1 "OD Probe Right" (nominal 12.7 each)
- **Feature:** "OD Diameter" with formula `(A + B) / 2`, nominal 12.7, tolerance ±0.025
- **ToolType:** "OD Roughing Insert" with max_offset_distance 0.1
- **ToolAssignment:** T1 position on test controller
- **CompensationRule:** trigger_threshold 0.005, max_per_cycle 0.010

### Gauge Simulation Formula
```python
reading = nominal + (wear * wear_direction) + offset + random_variation
```

---

## Known Gaps / TODO

### Models
- [ ] GaugeConfig needs `machine` FK in seed.py
- [ ] ChannelConfig may need additional fields for calibration

### Dashboard
- [ ] Tolerance bands not rendering correctly on trend chart (check JS)
- [ ] Channels section empty (gauge not linked to machine?)

### Setup Page
- [ ] Tool Assignment add button links to admin (needs custom form/view)
- [ ] Some detail views may be missing fields

### General
- [ ] Real gauge drivers (N1700, etc.) not implemented
- [ ] Real controller protocols not implemented
- [ ] User authentication not configured
- [ ] No unit tests

---

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install django channels channels-redis daphne

# Start Redis (required for WebSocket)
redis-server

# Run migrations
python manage.py migrate

# Seed test data
python manage.py shell
>>> from simulator.seed import seed_all
>>> seed_all(force=True)

# Run development server
python manage.py runserver
```

---

## File Locations

```
kairosloop/
├── kairosloop/          # Project settings
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── controller/
│   ├── models.py        # Machine, ControllerConfig
│   ├── views.py
│   ├── urls.py
│   └── templates/controller/
├── measurement/
│   ├── models.py        # GaugeConfig, ChannelConfig, Feature, FeatureInput, Measurement
│   ├── views.py
│   ├── urls.py
│   └── templates/measurement/
├── tooling/
│   ├── models.py        # ToolType, ToolInstance, ToolAssignment
│   ├── views.py
│   ├── urls.py
│   └── templates/tooling/
├── compensation/
│   ├── models.py        # CompensationRule, CompensationEvent
│   ├── views.py
│   ├── urls.py
│   └── templates/compensation/
├── dashboard/
│   ├── views.py         # dashboard(), setup(), toggle_*()
│   ├── urls.py
│   └── templates/dashboard/
│       ├── base.html
│       ├── dashboard.html
│       └── setup.html
├── simulator/
│   ├── seed.py          # Test data creation
│   ├── gauge.py         # Simulated readings
│   ├── engine.py        # Simulation loop
│   └── plc.py           # Test PLC
├── logs/
└── db.sqlite3
```


*Last updated: April 17, 2026*