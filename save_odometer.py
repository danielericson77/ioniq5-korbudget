
import os
import requests
from hyundai_kia_connect_api import VehicleManager

print("1. Ansluter till Hyundai Bluelink...")

username = os.environ["HYUNDAI_USERNAME"]
password = os.environ["HYUNDAI_PASSWORD"]

vm = VehicleManager(
    region=1,
    brand=2,
    username=username,
    password=password,
    pin="",
    language="sv"
)

print("2. Loggar in och hämtar bilinformation...")
vm.check_and_refresh_token()
vm.update_all_vehicles_with_cached_state()

print(f"Antal bilar hittade: {len(vm.vehicles)}")

supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
supabase_key = os.environ["SUPABASE_SECRET_KEY"]

headers = {
    "apikey": supabase_key,
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

for vehicle_id, vehicle in vm.vehicles.items():
    odometer = float(vehicle._odometer_value)

    print(f"Mätarställning hämtad: {odometer} km")
    print("3. Sparar i Supabase...")

    response = requests.post(
        f"{supabase_url}/rest/v1/odometer_history",
        headers=headers,
        json={"odometer_km": odometer},
        timeout=30
    )

    if response.status_code not in (200, 201, 204):
        print("Fel vid sparning:", response.status_code)
        print(response.text)
        response.raise_for_status()

    print("Mätarställningen har sparats!")

print("Testet är klart.")

