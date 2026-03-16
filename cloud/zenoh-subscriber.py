import json
import os

import zenoh
from dotenv import load_dotenv

load_dotenv()

ZENOH_ROUTER = os.getenv("ZENOH_ROUTER_ADDRESS", "localhost")
ZENOH_PORT = int(os.getenv("ZENOH_PORT", 7447))


def listener(sample):
    try:
        data = json.loads(sample.payload.to_string())
        print(
            f"[{sample.key_expr}] signal: {data['signal']} | value: {data['value']} | timestamp: {data['timestamp']}"
        )
    except Exception as e:
        print(f"error while parsing message: {e}")


def main():
    config = zenoh.Config()
    config.insert_json5(
        "connect/endpoints", json.dumps([f"tcp/{ZENOH_ROUTER}:{ZENOH_PORT}"])
    )
    session = zenoh.open(config)
    print(f"Connected to Zenoh router at {ZENOH_ROUTER}:{ZENOH_PORT}")
    print("Listening for vehicle signals")

    sub = session.declare_subscriber("vehicle/**", listener)

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("shutting down")
    finally:
        sub.undeclare()
        session.close()


if __name__ == "__main__":
    main()
