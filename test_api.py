import requests
import json

url = "http://localhost:8000/api/cs/analyze"
data = {"text": "John Doe told me he loves the new Xiaomi phone and he works for Acme Corp. He wants to buy it next week."}

print("Testing /api/cs/analyze...")
response = requests.post(url, json=data)
print(response.status_code)
print(json.dumps(response.json(), indent=2))

print("\nTesting /api/cs/graph...")
url_graph = "http://localhost:8000/api/cs/graph"
response = requests.get(url_graph)
print(response.status_code)
print(json.dumps(response.json(), indent=2))
