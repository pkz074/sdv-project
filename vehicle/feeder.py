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
        speed = 60.0  # km/h
        soc = 95.0  # %
        rpm = 2000
        throttle = 25  # %
        temperature = 70  # celsius
        while True:
            try:
                drift = random.uniform(-0.1, 0.4)
                speed += drift

                soc -= 0.05
                if soc < 0:
                    soc = 100.0

                rpm += random.uniform(-50, 50)
                rpm = max(700, min(6000, rpm))

                throttle += random.uniform(-1, 1)
                throttle = max(0, min(100, throttle))

                temperature += random.uniform(-0.1, 0.3)
                temperature = max(60, min(120, temperature))

                client.set_current_values(
                    {
                        "Vehicle.Speed": Datapoint(speed),
                        "Vehicle.Powertrain.TractionBattery.StateOfCharge.Current": Datapoint(
                            soc
                        ),
                        "Vehicle.Powertrain.CombustionEngine.Speed": Datapoint(rpm),
                        "Vehicle.Chassis.Accelerator.PedalPosition": Datapoint(
                            throttle
                        ),
                        "Vehicle.Powertrain.CombustionEngine.ECT": Datapoint(
                            temperature
                        ),
                    }
                )

                print(
                    f"Speed: {speed:.1f} km/h | SOC: {soc:.1f}% | RPM: {rpm:.0f} | Throttle: {throttle:.1f}% | Temp: {temperature:.1f}°C"
                )
                time.sleep(1)

            except Exception as e:
                print(f"Connection error: {e}, retrying in 5s")
                time.sleep(5)


if __name__ == "__main__":
    run_feeder()
