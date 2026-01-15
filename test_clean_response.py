import requests
import json

# Test the OpenAI-compatible endpoint to verify clean, structured response
url = "http://localhost:6969/v1/chat/completions"

headers = {
    "Content-Type": "application/json"
}

data = {
    "model": "grok-3-auto",
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ],
    "temperature": 0.7,
    "max_tokens": 150
}

try:
    print("Sending request to OpenAI-compatible endpoint...")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, headers=headers, json=data)
    
    print(f"\nResponse Status Code: {response.status_code}")
    response_data = response.json()
    print(f"Response JSON: {json.dumps(response_data, indent=2)}")
    
    # Validate the response structure
    required_fields = ["id", "object", "created", "model", "choices", "usage"]
    missing_fields = [field for field in required_fields if field not in response_data]
    
    if not missing_fields:
        print("\n✓ Response has all required OpenAI-compatible fields!")
        
        # Check choices structure
        if len(response_data["choices"]) > 0:
            choice = response_data["choices"][0]
            choice_required = ["index", "message", "finish_reason"]
            missing_choice_fields = [field for field in choice_required if field not in choice]
            
            if not missing_choice_fields:
                print("✓ Choice object has correct structure!")
                
                # Check message structure
                message = choice["message"]
                message_required = ["role", "content"]
                missing_message_fields = [field for field in message_required if field not in message]
                
                if not missing_message_fields:
                    print("✓ Message object has correct structure!")
                    
                    # Check usage structure
                    usage = response_data["usage"]
                    usage_required = ["prompt_tokens", "completion_tokens", "total_tokens"]
                    missing_usage_fields = [field for field in usage_required if field not in usage]
                    
                    if not missing_usage_fields:
                        print("✓ Usage object has correct structure!")
                        
                        # Check for additional fields in your desired format
                        additional_fields_present = (
                            "refusal" in message and 
                            "logprobs" in choice and
                            "prompt_tokens_details" in usage and
                            "completion_tokens_details" in usage and
                            "system_fingerprint" in response_data
                        )
                        
                        if additional_fields_present:
                            print("✓ Response includes all additional fields from your desired format!")
                        else:
                            print("! Some additional fields from your desired format are missing")
                    else:
                        print(f"! Missing usage fields: {missing_usage_fields}")
                else:
                    print(f"! Missing message fields: {missing_message_fields}")
            else:
                print(f"! Missing choice fields: {missing_choice_fields}")
        else:
            print("! No choices in response")
    else:
        print(f"! Missing required fields: {missing_fields}")
    
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the API server. Make sure it's running on http://localhost:6969")
except Exception as e:
    print(f"An error occurred: {str(e)}")
    import traceback
    traceback.print_exc()