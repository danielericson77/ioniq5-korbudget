
import os
from hyundai_kia_connect_api import VehicleManager

print("1. Ansluter till Hyundai Bluelink...")

username = os.environ["HYUNDAI_USERNAME"]
password = os.environ["HYUNDAI_PASSWORD"]

vm = VehicleManager(
    region=1,       # Europa
    brand=2,        # Hyundai
    username=username,
    password=password,
    pin="",
    language="sv"
)

print("2. Försöker logga in...")
vm.check_and_refresh_token()

print("3. Hämtar bilinformation...")
vm.update_all_vehicles_with_cached_state()

print(f"Antal bilar hittade: {len(vm.vehicles)}")

for vehicle_id, vehicle in vm.vehicles.items():
    print("\nBil hittad!")

    attributes = [
    name for name in dir(vehicle)
    if any(word in name.lower() for word in [
        "odo",
        "battery",
        "soc",
        "charge",
        "remain"
    ])
    ]
    print("Mätarställningsfält:", attributes)

    for name in attributes:
        try:
            value = getattr(vehicle, name)
            if not callable(value):
                print(f"{name}: {value}")
        except Exception:
            pass

print("\nTestet klart.")
