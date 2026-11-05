
import json
import os
import urllib.request
import urllib.error


BASE_URL = "https://api.pleos.ai"


def api_request(url, method="GET", data=None, headers=None):
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url, data=body, headers=headers or {}, method=method
    )
    print("Anropar:", method, url)

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        print(f"API-fel: HTTP {error.code}")
        print(error.read().decode("utf-8")[:1500])
        raise
        
def main():
    client_id = os.environ["PLEOS_CLIENT_ID"]
    client_secret = os.environ["PLEOS_CLIENT_SECRET"]

print("Anropar:", method, url)
request = urllib.request.Request(url, data=body, headers=headers or {}, method=method)

    print("1. Ansluter till Pleos...")

    token_response = api_request(
        f"{BASE_URL}/v1/auth/personal-token",
        method="POST",
        data={
            "clientId": client_id,
            "clientSecret": client_secret
        },
        headers={
            "Brand": "hyundai",
            "Content-Type": "application/json"
        }
    )

    access_token = token_response["data"]["accessToken"]
    print("2. Autentisering lyckades!")

    print("3. Hämtar fordonsinformation...")

    vehicles_response = api_request(
        f"{BASE_URL}/v1/vehicles/consent",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Brand": "hyundai",
            "Content-Type": "application/json"
        }
    )

    print("4. Hyundai API svarade!")
    print("Svar mottaget. Tillgängliga datafält:")

    data = vehicles_response.get("data", {})
    if isinstance(data, dict):
        print(", ".join(data.keys()))
    elif isinstance(data, list):
        print(f"Antal fordon: {len(data)}")
    else:
        print(type(data).__name__)

    print("Första API-testet är klart!")


if __name__ == "__main__":
    main()
