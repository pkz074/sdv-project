import requests
import json
import time

DITTO_URL = "http://localhost:8080/api/2/things/org.vehicle:my-device"
AUTH = ('ditto', 'ditto')

def run_diagnostic():
    print("--- OpenSOVD Diagnostic Scan Starting ---")
    try:
        # 1. Reach out to the Digital Twin in the Cloud
        response = requests.get(DITTO_URL, auth=AUTH)
        
        if response.status_code == 200:
            data = response.json()
            # 2. Navigate the JSON structure to find features
            features = data.get('features', {})
            
            # 3. Check specific Fault Flags
            # We look for the SpeedDriftFault added in Iteration 2
            drift_fault = features.get('SpeedDriftFault', {}).get('properties', {}).get('value', False)
            
            print(f"Checking SpeedDriftFault... Status: {'[ ERROR ]' if drift_fault else '[ OK ]'}")
            
            if drift_fault:
                print("ALERT: Vehicle Speed Instability Detected! Service Required.")
            else:
                print("SUCCESS: All systems within normal operating parameters.")
                
        else:
            print(f"Failed to connect to Ditto. Status Code: {response.status_code}")

    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    # Run a scan every 5 seconds
    while True:
        run_diagnostic()
        time.sleep(5)