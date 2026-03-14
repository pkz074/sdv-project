import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

DITTO_URL = os.getenv("DITTO_API_URL", "http://localhost:8080/api/2")
AUTH = (os.getenv("DITTO_USERNAME", "ditto"), os.getenv("DITTO_PASSWORD", "ditto"))

THING_ID = "org.vehicle:my-device"
POLICY_ID = "org.vehicle:my-policy"


def put_policy(policy_id, policy_data):
    url = f"{DITTO_URL}/policies/{policy_id}"
    headers = {"Content-Type": "application/json"}
    response = requests.put(url, json=policy_data, headers=headers, auth=AUTH)
    return response


def put_thing(thing_id, thing_data):
    url = f"{DITTO_URL}/things/{thing_id}"
    headers = {"Content-Type": "application/json"}
    response = requests.put(url, json=thing_data, headers=headers, auth=AUTH)
    return response


if __name__ == "__main__":
    with open("../policy.json", "r") as f:
        policy_data = json.load(f)

    response = put_policy(POLICY_ID, policy_data)
    print(f"Policy response: {response.status_code} - {response.text}")

    with open("../VSS_Ditto.json", "r") as f:
        thing_data = json.load(f)

    response = put_thing(THING_ID, thing_data)
    print(f"Thing response: {response.status_code} - {response.text}")
