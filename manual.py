from core import Grok
import time
import random

def example_usage():
    """
    Example usage of the Grok API with proper rate limiting handling
    """
    print("Grok API Usage Examples")
    print("="*50)
    
    # Example 1: Basic usage
    print("\n1. Basic usage:")
    try:
        response = Grok("grok-3-fast").start_convo("Hello, how are you?")
        if "error" not in response:
            print(f"Response: {response['response']}")
        else:
            print(f"Error: {response['error']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Add delay to avoid rate limiting
    time.sleep(random.uniform(2, 5))
    
    # Example 2: Using with extra_data for follow-up conversations
    print("\n2. Follow-up conversation:")
    try:
        initial_response = Grok("grok-3-fast").start_convo("What is the capital of France?")
        if "extra_data" in initial_response and "error" not in initial_response:
            print(f"Initial response: {initial_response['response']}")
            
            # Follow up on the conversation
            follow_up = Grok("grok-3-fast").start_convo("What else can you tell me about it?", initial_response["extra_data"])
            if "error" not in follow_up:
                print(f"Follow-up response: {follow_up['response']}")
            else:
                print(f"Follow-up error: {follow_up['error']}")
        else:
            print(f"Initial request failed: {initial_response.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Using different models
    print("\n3. Using different models:")
    models = ["grok-3-fast", "grok-3-auto"]
    for model in models:
        try:
            print(f"\nTrying {model}...")
            response = Grok(model).start_convo(f"Hi, which model are you? Respond with just the model name: {model}")
            if "error" not in response:
                print(f"Response: {response['response']}")
            else:
                print(f"Error with {model}: {response['error']}")
            
            # Delay between model requests
            time.sleep(random.uniform(3, 6))
        except Exception as e:
            print(f"Error with {model}: {e}")
    
    print("\nNote: Rate limiting is now handled automatically with exponential backoff.")
    print("The system will retry failed requests with increasing delays.")

if __name__ == "__main__":
    example_usage()