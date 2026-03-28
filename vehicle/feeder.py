import os
import random
import time

from dotenv import load_dotenv
from kuksa_client.grpc import Datapoint, VSSClient

load_dotenv()

KUKSA_HOST = os.getenv("KUKSA_ADDRESS", "localhost")
KUKSA_PORT = int(os.getenv("KUKSA_PORT", 55556))

# Fault injection config
DROPOUT_PROBABILITY = 0.1
NOISE_PROBABILITY = 0.15


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
                speed += 500

                if random.random() < NOISE_PROBABILITY:
                    speed += random.uniform(5, 15)
                    print("Speed noise spike injected")

                soc -= random.uniform(0.05, 0.15)
                if soc < 0:
                    soc = 100.0

                rpm += random.uniform(-50, 50)
                rpm = max(700, min(6000, rpm))

                throttle += random.uniform(-1, 1)
                throttle = max(0, min(100, throttle))

                temperature += random.uniform(-0.1, 0.5)
                temperature = max(60, min(130, temperature))  # can exceed 100 now

                # cleaner then before
                signals = {
                    "Vehicle.Speed": Datapoint(speed),
                    "Vehicle.Powertrain.TractionBattery.StateOfCharge.Current": Datapoint(
                        soc
                    ),
                    "Vehicle.Powertrain.CombustionEngine.Speed": Datapoint(rpm),
                    "Vehicle.Chassis.Accelerator.PedalPosition": Datapoint(throttle),
                }

                if random.random() > DROPOUT_PROBABILITY:
                    signals["Vehicle.Powertrain.CombustionEngine.ECT"] = Datapoint(
                        temperature
                    )
                else:
                    print("Temperature signal dropout, skipping this cycle")

                client.set_current_values(signals)

                print(
                    f"Speed: {speed:.1f} km/h | SOC: {soc:.1f}% | RPM: {rpm:.0f} | Throttle: {throttle:.1f}% | Temp: {temperature:.1f}°C"
                )
                time.sleep(1)

            except Exception as e:
                print(f"Connection error: {e}, retrying in 5s")
                time.sleep(5)


if __name__ == "__main__":
    run_feeder()
