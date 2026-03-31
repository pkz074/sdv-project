import time
import requests

DITTO_URL = "http://localhost:8080/api/2/things/org.vehicle:my-device"

def get_latency():

    try:
        res = requests.get(DITTO_URL, auth=("ditto", "ditto"))
        data = res.json()

        ts = data.get("features", {}).get("Timestamp", {}).get("properties", {}).get("value")

        if ts is None:
            print("No timestamp found!")
            return None

        return time.time() - float(ts)

    except Exception as e:
        print("Error:", e)
        return None

def measure_throughput(duration=5):

    start = time.time()
    count = 0

    while time.time() - start < duration:
        res = requests.get(
            DITTO_URL,
            auth=("ditto", "ditto")
        )
        
        if res.status_code == 200:
            count += 1

    return count / duration