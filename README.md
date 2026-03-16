# SDV Pipeline — Eclipse Kuksa · Zenoh · Ditto

A Cloud-to-Vehicle data pipeline built on the Eclipse SDV ecosystem. The system simulates real-time vehicle telemetry, normalizes it through Eclipse Kuksa, transports it via Eclipse Zenoh, and persists it as a live digital twin in Eclipse Ditto.

---

## System Architecture

```
feeder.py  →  Eclipse Kuksa  →  zenoh-bridge.py  →  Eclipse Zenoh  →  Eclipse Ditto
(VSS signals)  (databroker)     (reads + publishes)  (router + store)  (digital twin)
```

**Components:**
- `vehicle/feeder.py` — Simulates vehicle signals with sensor drift and fault injection
- `Eclipse Kuksa` — VSS databroker, normalizes signals over gRPC
- `cloud/zenoh-bridge.py` — Reads from Kuksa, publishes to Zenoh, and pushes state to Ditto
- `cloud/zenoh-subscriber.py` — Subscribes to Zenoh topics for pipeline verification
- `Eclipse Zenoh` — High-performance pub/sub transport with memory storage
- `Eclipse Ditto` — Digital twin backend, exposes vehicle state via REST API

**Signals monitored:**
- `Vehicle.Speed` — vehicle speed (km/h)
- `Vehicle.Powertrain.TractionBattery.StateOfCharge.Current` — battery SOC (%)
- `Vehicle.Powertrain.CombustionEngine.Speed` — engine speed (RPM)
- `Vehicle.Chassis.Accelerator.PedalPosition` — throttle position (%)
- `Vehicle.Powertrain.CombustionEngine.ECT` — coolant temperature (°C)

**Functional Modification:**
A `SpeedDriftFault` flag is computed in the bridge — it activates when speed drifts beyond a threshold. This flag propagates through the full pipeline and is visible in the Ditto digital twin in real time.

---

## Requirements

### Software
- Python 3.10+
- Docker + Docker Compose
- Git

### Python Packages
Installed per folder via `requirements.txt`:

**`vehicle/`**
```
kuksa-client
python-dotenv
```

**`cloud/`**
```
kuksa-client
python-dotenv
requests
eclipse-zenoh
```

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/pkz074/sdv-project.git
cd sdv-project
```

### 2. Set up environment variables
```bash
cp .env.example .env
```
The default values work out of the box for local development. Edit `.env` if your ports differ.

### 3. Set up Python virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r vehicle/requirements.txt
pip install -r cloud/requirements.txt
```

### 4. Start Kuksa and Zenoh
```bash
docker compose up -d
```

This starts:
- `kuksa-databroker` on port `55556`
- `zenoh-router` on ports `7447` (protocol) and `8000` (REST API)

### 5. Start Eclipse Ditto
Ditto requires its own Docker Compose stack:
```bash
git clone https://github.com/eclipse-ditto/ditto ~/ditto
cd ~/ditto/deployment/docker/
docker compose up -d
```

Wait ~30 seconds for Ditto to fully boot. Verify it is running:
```bash
curl -u ditto:ditto http://localhost:8080/api/2/things
```
Expected output: `[]` (empty array means Ditto is up with no things yet).

### 6. Register the digital twin policy and thing
```bash
cd sdv-project/cloud
source ../.venv/bin/activate
python ditto_setup.py
```

Expected output:
```
Deleting old thing and policy...
Thing delete: 204
Policy delete: 204
Registering policy...
Policy response: 201
Registering thing...
Thing response: 201
Ditto setup complete.
```

This creates the `org.vehicle:my-device` digital twin with 6 features: `VehicleSpeed`, `BatterySOC`, `EngineSpeed`, `ThrottlePosition`, `CoolantTemperature`, and `SpeedDriftFault`.

---

## Running the System

Open **three separate terminals**, all with the virtual environment activated:

```bash
source .venv/bin/activate
```

**Terminal 1 — Vehicle feeder:**
```bash
cd vehicle
python feeder.py
```

**Terminal 2 — Zenoh bridge:**
```bash
cd cloud
python zenoh-bridge.py
```

**Terminal 3 — Zenoh subscriber (optional, for pipeline verification):**
```bash
cd cloud
python zenoh-subscriber.py
```

---

## Verifying the Pipeline

### 1. Check feeder output (Terminal 1)
You should see all 5 signals updating every second:
```
Speed: 60.4 km/h | SOC: 94.9% | RPM: 2034 | Throttle: 25.3% | Temp: 71.2°C
```

### 2. Check bridge output (Terminal 2)
You should see each signal being pushed to Ditto with HTTP 204 responses:
```
[VehicleSpeed] 60.44 -> Ditto: 204
[BatterySOC] 94.90 -> Ditto: 204
[EngineSpeed] 2034.00 -> Ditto: 204
[ThrottlePosition] 25.00 -> Ditto: 204
[CoolantTemperature] 71.20 -> Ditto: 204
[SpeedDriftFault] False
```

### 3. Check Zenoh subscriber output (Terminal 3)
You should see all Zenoh topics receiving messages:
```
[vehicle/speed] signal: Vehicle.Speed | value: 60.44 | timestamp: ...
[vehicle/powertrain/combustionengine/speed] signal: Vehicle.Powertrain.CombustionEngine.Speed | value: 2034 | timestamp: ...
```

### 4. Check Ditto digital twin via REST
```bash
curl -u ditto:ditto http://localhost:8080/api/2/things/org.vehicle:my-device
```

### 5. Check Ditto Explorer UI
Open `http://localhost:8080` in your browser, click the Explorer UI link, and select `org.vehicle:my-device`. You will see all 6 features updating in real time.

### 6. Check Zenoh REST API
While the bridge is running:
```bash
curl http://localhost:8000/vehicle/speed
curl http://localhost:8000/vehicle/powertrain/tractionbattery/stateofcharge/current
curl http://localhost:8000/vehicle/powertrain/combustionengine/speed
curl http://localhost:8000/vehicle/chassis/accelerator/pedalposition
curl http://localhost:8000/vehicle/powertrain/combustionengine/ect
```

---

## Project Structure

```
sdv-project/
├── vehicle/
│   ├── feeder.py               # VSS signal simulator with fault injection
│   └── requirements.txt
├── cloud/
│   ├── zenoh-bridge.py         # Kuksa → Zenoh → Ditto bridge
│   ├── zenoh-subscriber.py     # Zenoh subscriber for pipeline verification
│   ├── ditto_setup.py          # Registers Ditto policy and digital twin
│   └── requirements.txt
├── policy.json                 # Ditto access policy definition
├── VSS_Ditto.json              # Digital twin feature structure
├── zenoh-config.json5          # Zenoh router config with memory storage
├── docker-compose.yaml         # Kuksa + Zenoh services
├── .env.example                # Environment variable template
└── README.md
```

---

## Stopping the System

```bash
# Stop Kuksa + Zenoh
cd sdv-project
docker compose down

# Stop Ditto
cd ~/ditto/deployment/docker/
docker compose down
```

---

## Notes

- Ditto is managed in a separate Docker Compose stack and must be started independently.
- The `ditto_setup.py` script only needs to be run once. If you restart Ditto, the thing persists unless you explicitly delete it.
- If Ditto loses state after a restart, re-run `python ditto_setup.py` from the `cloud/` folder.
- The `.env` file is excluded from version control. Use `.env.example` as a reference.
