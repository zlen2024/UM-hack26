#!/usr/bin/env python3
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000/api"

def make_request(method, url, data=None, headers=None):
    """Helper to make HTTP requests"""
    if headers is None:
        headers = {}
    
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    for key, value in headers.items():
        req.add_header(key, value)
    
    try:
        if data:
            response = urllib.request.urlopen(req, data=json.dumps(data).encode('utf-8'))
        else:
            response = urllib.request.urlopen(req)
        
        status = response.status
        body = response.read().decode('utf-8')
        return status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

# Step 1: Login to get token
print("Step 1: Logging in...")
status, response = make_request(
    "POST",
    f"{BASE_URL}/auth/login",
    {"email": "demo@example.com", "password": "demo123"}
)
print(f"Login Status: {status}")

if status != 200:
    print(f"Login failed: {response}")
    exit(1)

token = json.loads(response)["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"Token obtained: {token[:20]}...")

# Step 2: Check current credentials status
print("\nStep 2: Checking current Google Calendar credentials...")
status, response = make_request(
    "GET",
    f"{BASE_URL}/google-calendar/credentials",
    headers=headers
)
print(f"Status Code: {status}")
print(f"Response: {response}")

# Step 3: Save new credentials
print("\nStep 3: Saving new Google Calendar credentials...")
api_key = "AIzaSyD2CADbtKmdV_A-MUy577S4KZ7PBOxQlFE"
test_email = "fakhrulhakimy93@gmail.com"

status, response = make_request(
    "POST",
    f"{BASE_URL}/google-calendar/credentials",
    {"api_key": api_key, "test_email": test_email},
    headers
)
print(f"Save Status: {status}")
print(f"Response: {response}")

if status == 200:
    print("\n✅ SUCCESS! Credentials saved and test event created!")
    result = json.loads(response)
    if "event_id" in result:
        print(f"   - Event ID: {result['event_id']}")
    if "activity_id" in result:
        print(f"   - Activity ID: {result['activity_id']}")
else:
    print(f"\n❌ Failed to save credentials")
    print(f"   Status: {status}")
    print(f"   Error: {response}")

# Step 4: List events
print("\nStep 4: Listing calendar events...")
status, response = make_request(
    "GET",
    f"{BASE_URL}/google-calendar/events",
    headers=headers
)
print(f"Events Status: {status}")
if status == 200:
    events = json.loads(response)
    print(f"Found {len(events)} event(s)")
    for event in events:
        print(f"   - {event.get('title')}: {event.get('start_time')}")
