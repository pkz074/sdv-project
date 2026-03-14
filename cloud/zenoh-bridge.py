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
]


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

        while True:
            try:
                values = client.get_current_values(SIGNALS)
                speed = None
                soc = None
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
                    if signal == "Vehicle.Speed":
                        speed = datapoint.value
                    elif (
                        signal
                        == "Vehicle.Powertrain.TractionBattery.StateOfCharge.Current"
                    ):
                        soc = datapoint.value

                if speed is not None:
                    drift_fault = speed > 61.0
                    status = put_feature_value("VehicleSpeed", round(speed, 2))
                    put_feature_value("SpeedDriftFault", drift_fault)
                    print(
                        f"Zenoh+Ditto -> Speed: {speed:.2f} km/h | DriftFault: {drift_fault} | Ditto: {status}"
                    )

                if soc is not None:
                    status = put_feature_value("BatterySOC", round(soc, 2))
                    print(f"Zenoh+Ditto -> Battery: {soc:.2f}% | Ditto: {status}")

                time.sleep(1)
            except Exception as e:
                print(f"Error {e} trying again in 5 sec")
                time.sleep(5)
            finally:
                session.close()


if __name__ == "__main__":
    main()
