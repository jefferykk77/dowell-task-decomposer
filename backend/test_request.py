import requests
import json

url = "http://127.0.0.1:8000/api/tasks/decompose"
headers = {"Content-Type": "application/json"}
with open("test_payload_ai.json", "r", encoding="utf-8") as f:
    data = json.load(f)

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response (first 500 chars):")
        print(json.dumps(response.json(), ensure_ascii=False, indent=2)[:500])
    else:
        print("Error Response:")
        print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
