import json
import os
import time

import requests
import zenoh
from dotenv import load_dotenv
from kuksa_client.grpc import VSSClient

load_dotenv()

KUKSA_HOST = os.getenv("KUKSA_ADDRESS", "localhost")
KUKSA_PORT = int(os.getenv("KUKSA_PORT", 55556))
ZENOH_ROUTER = os.getenv("ZENOH_ROUTER_ADDRESS", "localhost")
ZENOH_PORT = int(os.getenv("ZENOH_PORT", 7447))
DITTO_URL = os.getenv("DITTO_API_URL", "http://localhost:8080/api/2")
AUTH = (os.getenv("DITTO_USERNAME", "ditto"), os.getenv("DITTO_PASSWORD", "ditto"))

THING_ID = "org.vehicle:my-device"

SOC_LOW_THRESHOLD = 20.0  # % below this triggers LowBatteryAlert
TEMP_HIGH_THRESHOLD = 100.0  # °C above this triggers OverheatAlert
SPEED_DRIFT_THRESHOLD = 61.0  # km/h above this triggers SpeedDriftFault

SIGNALS = [
    "Vehicle.Speed",
    "Vehicle.Powertrain.TractionBattery.StateOfCharge.Current",
    "Vehicle.Powertrain.CombustionEngine.Speed",
    "Vehicle.Chassis.Accelerator.PedalPosition",
    "Vehicle.Powertrain.CombustionEngine.ECT",
]

SIGNAL_TO_FEATURE = {
    "Vehicle.Speed": "VehicleSpeed",
    "Vehicle.Powertrain.TractionBattery.StateOfCharge.Current": "BatterySOC",
    "Vehicle.Powertrain.CombustionEngine.Speed": "EngineSpeed",
    "Vehicle.Chassis.Accelerator.PedalPosition": "ThrottlePosition",
    "Vehicle.Powertrain.CombustionEngine.ECT": "CoolantTemperature",
}

def create_feature(feature, value):
    url = f"{DITTO_URL}/things/{THING_ID}/features/{feature}"
    headers = {"Content-Type": "application/json"}
    data = {"properties": {"value": value}}
    response = requests.put(url, json=data, headers=headers, auth=AUTH)
    return response.status_code


def put_feature_value(feature, value):
    url = f"{DITTO_URL}/things/{THING_ID}/features/{feature}/properties"
    headers = {"Content-Type": "application/json"}
    data = {"value": value}
    response = requests.put(url, json=data, headers=headers, auth=AUTH)
    return response.status_code


def compute_health_state(speed_fault, low_battery, overheat):
    if (overheat and speed_fault) or (overheat and low_battery):
        return "UNSAFE"
    elif speed_fault or low_battery or overheat:
        return "DEGRADED"
    else:
        return "NORMAL"


def main():
    config = zenoh.Config()
    config.insert_json5(
        "connect/endpoints", json.dumps([f"tcp/{ZENOH_ROUTER}:{ZENOH_PORT}"])
    )
    session = zenoh.open(config)
    print(f"Connected to router at {ZENOH_ROUTER}:{ZENOH_PORT}")
    print(f"Connecting to kuksa at {KUKSA_HOST}:{KUKSA_PORT}")

    with VSSClient(KUKSA_HOST, KUKSA_PORT) as client:
        print("Pipeline running: Kuksa -> Zenoh -> Ditto")
        try:
            while True:
                values = client.get_current_values(SIGNALS)
                cycle_timestamp = time.time()
                speed = None
                soc = None
                temperature = None

                for signal, datapoint in values.items():
                    if datapoint is None or datapoint.value is None:
                        continue

                    topic = signal.replace(".", "/").lower()
                    payload = json.dumps(
                        {
                            "signal": signal,
                            "value": datapoint.value,
                            "timestamp": str(datapoint.timestamp),
                        }
                    )
                    session.put(topic, payload)

                    feature = SIGNAL_TO_FEATURE.get(signal)
                    if feature:
                        status = put_feature_value(feature, round(datapoint.value, 2))
                        print(f"[{feature}] {datapoint.value:.2f} -> Ditto: {status}")

                    if signal == "Vehicle.Speed":
                        speed = datapoint.value
                    elif (
                        signal
                        == "Vehicle.Powertrain.TractionBattery.StateOfCharge.Current"
                    ):
                        soc = datapoint.value
                    elif signal == "Vehicle.Powertrain.CombustionEngine.ECT":
                        temperature = datapoint.value

                # Compute fault flags
                speed_fault = speed is not None and speed > SPEED_DRIFT_THRESHOLD
                low_battery = soc is not None and soc < SOC_LOW_THRESHOLD
                overheat = temperature is not None and temperature > TEMP_HIGH_THRESHOLD

                # Push timestamp + fault flags to Ditto
                timestamp_status = create_feature("Timestamp", cycle_timestamp)
                speed_fault_status = put_feature_value("SpeedDriftFault", speed_fault)
                low_battery_status = put_feature_value("LowBatteryAlert", low_battery)
                overheat_status = put_feature_value("OverheatAlert", overheat)

                # Compute and push health state
                health_state = compute_health_state(speed_fault, low_battery, overheat)
                health_status = put_feature_value("VehicleHealthState", health_state)

                print(f"[Timestamp] {cycle_timestamp} -> Ditto: {timestamp_status}")
                print(
                    f"[Faults] SpeedDrift: {speed_fault} ({speed_fault_status}) | "
                    f"LowBattery: {low_battery} ({low_battery_status}) | "
                    f"Overheat: {overheat} ({overheat_status})"
                )
                print(f"[HealthState] {health_state} ({health_status})")
                print("---")

                time.sleep(1)

        except KeyboardInterrupt:
            print("Shutting down...")
        except Exception as e:
            print(f"Error: {e}, retrying in 5s")
            time.sleep(5)
        finally:
            session.close()


if __name__ == "__main__":
    main()
