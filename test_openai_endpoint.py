import requests
import json

# Test the OpenAI-compatible endpoint
url = "http://localhost:6969/v1/chat/completions"

headers = {
    "Content-Type": "application/json"
}

data = {
    "model": "grok-3-auto",
    "messages": [
        {"role": "system", "content": "Tu ek savage desi dost hai, Hinglish mein baat kar."},
        {"role": "user", "content": "Bhai life mein sab barbaad ho gaya 😭"}
    ],
    "temperature": 0.9,
    "max_tokens": 200
}

try:
    print("Sending request to OpenAI-compatible endpoint...")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, headers=headers, json=data)
    
    print(f"\nResponse Status Code: {response.status_code}")
    print(f"Response JSON: {json.dumps(response.json(), indent=2)}")
    
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the API server. Make sure it's running on http://localhost:6969")
except Exception as e:
    print(f"An error occurred: {str(e)}")