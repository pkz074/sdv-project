import os
import random
import time

from dotenv import load_dotenv
from kuksa_client.grpc import Datapoint, VSSClient

load_dotenv()

KUKSA_HOST = os.getenv("KUKSA_ADDRESS", "localhost")
KUKSA_PORT = int(os.getenv("KUKSA_PORT", 55556))


def run_feeder():
    print(f"Connecting to Kuksa at {KUKSA_HOST}:{KUKSA_PORT}")
    with VSSClient(KUKSA_HOST, KUKSA_PORT) as client:
        speed = 60.0
        soc = 95.0
        while True:
            try:
                drift = random.uniform(-0.1, 0.4)
                speed += drift

                client.set_current_values(
                    {
                        "Vehicle.Speed": Datapoint(speed),
                        "Vehicle.Powertrain.TractionBattery.StateOfCharge.Current": Datapoint(
                            soc
                        ),
                    }
                )

                print(f"Sent -> Speed: {speed:.2f} km/h | Battery: {soc:.1f}%")

                soc -= 0.05
                if soc < 0:
                    soc = 100.0

                time.sleep(1)

            except Exception as e:
                print(f"Connection error: {e}, retrying in 5s")
                time.sleep(5)


if __name__ == "__main__":
    run_feeder()
