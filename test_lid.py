import sys
import os
import json
import logging

sys.path.append("/workspace/backend")
from routes.chatery import resolve_lid_to_phone, LID_TO_PHONE_CACHE

# Mock requests.post
import requests

class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

def mock_post(url, json=None, headers=None, timeout=None):
    print(f"Mock POST to {url} with {json}")
    if url.endswith("/contacts"):
        return MockResponse({
            "success": True,
            "contacts": [
                {
                    "id": "147527898800287@lid",
                    "jid": "60123456789@s.whatsapp.net",
                    "name": "Test LID"
                },
                {
                    "id": "999999@lid",
                    "number": "60111111111",
                    "name": "Test LID 2"
                }
            ]
        }, 200)
    return MockResponse({}, 404)

requests.post = mock_post

def test():
    # Test 1: Resolve a known LID with JID
    print("--- Test 1 ---")
    phone1 = resolve_lid_to_phone("session123", "147527898800287@lid")
    print(f"Result 1: {phone1}")
    assert phone1 == "60123456789"
    assert "147527898800287@lid" in LID_TO_PHONE_CACHE

    # Test 2: Resolve a known LID with number
    print("--- Test 2 ---")
    phone2 = resolve_lid_to_phone("session123", "999999@lid")
    print(f"Result 2: {phone2}")
    assert phone2 == "60111111111"

    # Test 3: Resolve an unknown LID (should fallback to LID)
    print("--- Test 3 ---")
    phone3 = resolve_lid_to_phone("session123", "unknown@lid")
    print(f"Result 3: {phone3}")
    assert phone3 == "unknown@lid"

    # Test 4: Use cache (should not call POST again for known LID)
    print("--- Test 4 ---")
    # overwrite mock to fail if called
    requests.post = lambda *a, **k: sys.exit("Should not be called")
    phone4 = resolve_lid_to_phone("session123", "147527898800287@lid")
    print(f"Result 4 (from cache): {phone4}")
    assert phone4 == "60123456789"

    print("All tests passed!")

if __name__ == "__main__":
    test()
