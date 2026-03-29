#!/bin/bash

echo "Stopping Kuksa + Zenoh..."
docker compose down

echo "Stopping Ditto..."
cd ~/ditto/deployment/docker/
docker compose down

echo "Done."