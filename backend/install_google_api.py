#!/usr/bin/env python3
import subprocess
import sys

packages = [
    "google-api-python-client",
    "google-auth",
    "google-auth-httplib2"
]

print("Installing Google API packages...")
for package in packages:
    print(f"Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", package])

print("✅ All packages installed successfully!")
