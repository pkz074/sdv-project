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


def put_feature_value(feature, value):
    url = f"{DITTO_URL}/things/{THING_ID}/features/{feature}/properties"
    headers = {"Content-Type": "application/json"}
    data = {"value": value}
    response = requests.put(url, json=data, headers=headers, auth=AUTH)
    return response.status_code


def main():
    config = zenoh.Config()
    config.insert_json5(
        "connect/endpoints", json.dumps([f"tcp/{ZENOH_ROUTER}:{ZENOH_PORT}"])
    )

    session = zenoh.open(config)

    print(f"Connected to router at {ZENOH_ROUTER}:{ZENOH_PORT}")
    print(f"Connecting to kuksa at {KUKSA_HOST}:{KUKSA_PORT}")

    with VSSClient(KUKSA_HOST, KUKSA_PORT) as client:
        print("Sending to Zenoh")
        try:
            while True:
                values = client.get_current_values(SIGNALS)

                for signal, datapoint in values.items():
                    if datapoint is None:
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
                    if feature and datapoint.value is not None:
                        status = put_feature_value(feature, round(datapoint.value, 2))
                        print(f"[{feature}] {datapoint.value:.2f} -> Ditto: {status}")

                speed_dp = values.get("Vehicle.Speed")
                if speed_dp and speed_dp.value is not None:
                    drift_fault = speed_dp.value > 61
                    put_feature_value("SpeedDriftFault", drift_fault)
                    print(f"[SpeedDriftFault] {drift_fault}")

                time.sleep(1)
        except KeyboardInterrupt:
            print("shutting down")
        except Exception as e:
            print(f"Error: {e} retrying in 5 sec")
            time.sleep(5)
        finally:
            session.close()


if __name__ == "__main__":
    main()
