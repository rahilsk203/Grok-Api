import sys
import os

# Add the directory to sys.path to import api_server
sys.path.append(r"c:\Users\root\Desktop\Ruto-GLM\Grok-Api")

from api_server import extract_message_from_parts, clean_response

def test_extraction():
    print("Testing extraction...")
    data = {
        "system_instruction": {"parts": [{"text": "You are an agent."}]},
        "contents": [
            {"role": "user", "parts": [{"text": "Hello"}]},
            {"role": "model", "parts": [{"text": "Hi"}]},
            {"role": "user", "parts": [{"text": "Open YouTube"}]}
        ]
    }
    result = extract_message_from_parts(data)
    print(f"Extracted prompt:\n{result}")
    assert "System: You are an agent." in result
    assert "User: Hello" in result
    assert "Assistant: Hi" in result
    assert "User: Open YouTube" in result
    print("Extraction test passed!")

def test_cleaning():
    print("\nTesting cleaning...")
    text = "Certainly! Based on the screen, I've analyzed the state. [think]I need to open YouTube.[/think][answer]do(action=\"Launch\", app=\"YouTube\")[/answer] I hope this helps!"
    result = clean_response(text)
    print(f"Cleaned response:\n{result}")
    assert result == "[think]I need to open YouTube.[/think][answer]do(action=\"Launch\", app=\"YouTube\")[/answer]"
    
    text2 = "Sure, [think]Thinking...[/think][answer]do(action=\"Home\")[/answer]"
    result2 = clean_response(text2)
    print(f"Cleaned response 2:\n{result2}")
    assert result2 == "[think]Thinking...[/think][answer]do(action=\"Home\")[/answer]"
    
    print("Cleaning test passed!")

if __name__ == "__main__":
    try:
        test_extraction()
        test_cleaning()
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
