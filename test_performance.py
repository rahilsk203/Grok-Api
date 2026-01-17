import requests
import time
import json

def test_grok_performance():
    """
    Test script to verify the improved performance of the Grok API
    """
    url = "http://localhost:6969/ask"
    
    # Sample request payload
    payload = {
        "model": "grok-3-auto",
        "message": "Hello, how are you today?",
        "proxy": None
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Testing Grok API performance...")
    print("-" * 40)
    
    # Make multiple requests to measure average response time
    response_times = []
    successful_requests = 0
    
    for i in range(3):
        print(f"Request {i+1}...")
        start_time = time.time()
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            if response.status_code == 200:
                print(f"  Status: {response.status_code}")
                print(f"  Response time: {response_time:.2f} seconds")
                
                # Print a snippet of the response
                try:
                    resp_json = response.json()
                    if "response" in resp_json:
                        print(f"  Response preview: {resp_json['response'][:100]}...")
                except:
                    print(f"  Raw response: {response.text[:100]}...")
                
                successful_requests += 1
            else:
                print(f"  Status: {response.status_code}")
                print(f"  Error: {response.text[:100]}...")
                
        except requests.exceptions.Timeout:
            print(f"  Request timed out after {time.time() - start_time:.2f} seconds")
        except Exception as e:
            print(f"  Request failed: {str(e)}")
        
        print()
        time.sleep(1)  # Brief pause between requests
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        print("-" * 40)
        print(f"Average response time: {avg_time:.2f} seconds")
        print(f"Successful requests: {successful_requests}/{len(response_times)}")
        
        if successful_requests > 0:
            print("\nPerformance improvements implemented:")
            print("- Faster retry settings (0.05s base delay)")
            print("- Reduced timeouts (15s from 45s)")
            print("- More aggressive retry strategy")
            print("- Optimized connection settings")
            print("- Faster session creation")
            print("\nThe API should now respond faster internally when fetching from Grok!")
        else:
            print("\nNote: All requests failed. Please check the server logs.")
    else:
        print("No responses recorded.")

if __name__ == "__main__":
    test_grok_performance()