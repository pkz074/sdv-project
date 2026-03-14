# SDV Pipeline — Eclipse Kuksa · Zenoh · Ditto

A Cloud-to-Vehicle data pipeline built on the Eclipse SDV ecosystem. The system simulates real-time vehicle telemetry, normalizes it through Eclipse Kuksa, transports it via Eclipse Zenoh, and persists it as a live digital twin in Eclipse Ditto.

---

## System Architecture

```
feeder.py  →  Eclipse Kuksa  →  zenoh-bridge.py  →  Eclipse Zenoh  →  Eclipse Ditto
(VSS signals)  (databroker)     (reads + publishes)  (router + store)  (digital twin)
```

**Components:**
- `vehicle/feeder.py` — Simulates vehicle signals (speed, battery SoC) with sensor drift and fault injection
- `Eclipse Kuksa` — VSS databroker, normalizes signals over gRPC
- `cloud/zenoh-bridge.py` — Reads from Kuksa, publishes to Zenoh, and pushes state to Ditto
- `Eclipse Zenoh` — High-performance pub/sub transport with memory storage
- `Eclipse Ditto` — Digital twin backend, exposes vehicle state via REST API

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
Policy response: 201 ...
Thing response: 201 ...
```

This creates the `org.vehicle:my-device` digital twin with features: `VehicleSpeed`, `BatterySOC`, and `SpeedDriftFault`.

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

**Terminal 3 — Verify Zenoh storage (optional):**
```bash
curl http://localhost:8000/vehicle/speed
```

---

## Verifying the Pipeline

### 1. Check feeder output (Terminal 1)
You should see speed and battery values updating every second:
```
Sent -> Speed: 60.43 km/h | Battery: 94.9%
```

### 2. Check bridge output (Terminal 2)
You should see Zenoh publish confirmations and Ditto HTTP 204 responses:
```
Zenoh+Ditto -> Speed: 60.43 km/h | DriftFault: False | Ditto: 204
Zenoh+Ditto -> Battery: 94.90% | Ditto: 204
```

### 3. Check Ditto digital twin via REST
```bash
curl -u ditto:ditto http://localhost:8080/api/2/things/org.vehicle:my-device
```

### 4. Check Ditto Explorer UI
Open `http://localhost:8080` in your browser, click the Explorer UI link, and select `org.vehicle:my-device`. You will see `VehicleSpeed`, `BatterySOC`, and `SpeedDriftFault` updating in real time.

### 5. Check Zenoh REST API
While the bridge is running:
```bash
curl http://localhost:8000/vehicle/speed
curl http://localhost:8000/vehicle/powertrain/tractionbattery/stateofcharge/current
```

---

## Project Structure

```
sdv-project/
├── vehicle/
│   ├── feeder.py           # VSS signal simulator with fault injection
│   └── requirements.txt
├── cloud/
│   ├── zenoh-bridge.py     # Kuksa → Zenoh → Ditto bridge
│   ├── ditto_setup.py      # Registers Ditto policy and digital twin
│   └── requirements.txt
├── policy.json             # Ditto access policy definition
├── VSS_Ditto.json          # Digital twin feature structure
├── zenoh-config.json5      # Zenoh router config with memory storage
├── docker-compose.yaml     # Kuksa + Zenoh services
├── .env.example            # Environment variable template
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
