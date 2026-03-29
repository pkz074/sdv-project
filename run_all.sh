#!/bin/bash

echo "Starting Kuksa + Zenoh..."
docker compose up -d

echo "Starting Ditto..."
cd ~/ditto/deployment/docker/
docker compose up -d

echo "Done. Now run feeder, bridge, and OpenSOVD manually."
